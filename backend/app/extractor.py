"""Tiered recipe extraction.

The strategy, cheapest/most-reliable first:

1. ``recipe-scrapers`` — a maintained library with hand-tuned parsers for hundreds
   of popular recipe sites, plus a generic Schema.org/JSON-LD wildcard fallback.
2. ``extruct`` JSON-LD — raw Schema.org ``Recipe`` parsing for sites the library
   doesn't special-case but that still publish structured data.
3. (future) LLM fallback — feed stripped page text to the Claude API for the messy
   pages that have no structured data at all. See md/CONTEXT.md.

Build #1 and #2 first, measure the miss rate, then add #3 only for the stragglers.
"""
from __future__ import annotations

import httpx

from .models import Recipe


class FetchError(Exception):
    """Raised when a page can't be retrieved even after the impersonation fallback."""

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# A realistic Chrome header set. Sent on every request — cheap and helps with
# naive header checks. The heavy lifting against TLS/JA3 fingerprinting is done by
# curl_cffi in the fallback below (see md/CONTEXT.md for the anti-bot rationale).
BROWSER_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
    "image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

# HTTP statuses that indicate anti-bot blocking rather than a genuine "not found".
# These trigger the curl_cffi browser-impersonation fallback.
_BLOCKED_STATUSES = {402, 403, 406, 429, 503}


async def _fetch_httpx(url: str) -> str:
    """Fast path: lightweight async client. Used for the majority of sites."""
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=15.0,
        headers=BROWSER_HEADERS,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


async def _fetch_curl_cffi(url: str) -> str:
    """Fallback path: impersonate a real Chrome TLS/JA3 fingerprint.

    Defeats Cloudflare/Akamai blocks that header-only approaches can't, because
    those systems fingerprint the TLS handshake itself — not just the headers.
    """
    from curl_cffi.requests import AsyncSession

    async with AsyncSession() as session:
        resp = await session.get(
            url,
            headers=BROWSER_HEADERS,
            impersonate="chrome",
            timeout=20,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text


async def fetch_html(url: str) -> str:
    """Fetch a page, falling back to browser impersonation if the site blocks us."""
    try:
        return await _fetch_httpx(url)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code not in _BLOCKED_STATUSES:
            raise
        # Anti-bot block — retry with curl_cffi's TLS impersonation.
        try:
            return await _fetch_curl_cffi(url)
        except Exception as fallback_exc:  # curl_cffi raises its own exception types
            raise FetchError(
                f"Site returned {exc.response.status_code} and the browser-impersonation "
                f"fallback also failed: {fallback_exc}"
            ) from fallback_exc


def _try_recipe_scrapers(html: str, url: str) -> Recipe | None:
    try:
        from recipe_scrapers import scrape_html
    except ImportError:
        return None

    try:
        scraper = scrape_html(html, org_url=url)
        ingredients = scraper.ingredients()
        instructions = scraper.instructions_list()
    except Exception:
        return None

    if not ingredients and not instructions:
        return None

    def safe(fn):
        try:
            return fn()
        except Exception:
            return None

    return Recipe(
        title=safe(scraper.title),
        ingredients=ingredients or [],
        instructions=instructions or [],
        image=safe(scraper.image),
        total_time=str(safe(scraper.total_time) or "") or None,
        yields=safe(scraper.yields),
        source_url=url,
        extracted_via="recipe-scrapers",
    )


def _try_json_ld(html: str, url: str) -> Recipe | None:
    try:
        import extruct
    except ImportError:
        return None

    data = extruct.extract(html, base_url=url, syntaxes=["json-ld"])
    for item in data.get("json-ld", []):
        types = item.get("@type", [])
        types = types if isinstance(types, list) else [types]
        if "Recipe" not in types:
            continue

        ingredients = item.get("recipeIngredient") or item.get("ingredients") or []
        instructions = _parse_instructions(item.get("recipeInstructions"))
        if not ingredients and not instructions:
            continue

        image = item.get("image")
        if isinstance(image, dict):
            image = image.get("url")
        elif isinstance(image, list) and image:
            image = image[0].get("url") if isinstance(image[0], dict) else image[0]

        return Recipe(
            title=item.get("name"),
            ingredients=_as_str_list(ingredients),
            instructions=instructions,
            image=image,
            total_time=item.get("totalTime"),
            yields=_as_str(item.get("recipeYield")),
            source_url=url,
            extracted_via="json-ld",
        )
    return None


def _try_wprm_html(html: str, url: str) -> Recipe | None:
    """Parse WP Recipe Maker (WPRM) HTML directly.

    Fallback for WPRM sites whose JSON-LD is missing or broken — the markup is
    well-structured with stable `wprm-recipe-*` CSS classes. Most WPRM sites are
    already caught by the structured-data tiers; this covers the stragglers.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    container = soup.select_one(".wprm-recipe-container, .wprm-recipe")
    if container is None:
        return None

    def text(el) -> str:
        return el.get_text(" ", strip=True) if el else ""

    ingredients: list[str] = []
    for el in container.select(".wprm-recipe-ingredient"):
        # Join amount / unit / name / notes; each part is optional.
        parts = [
            text(el.select_one(".wprm-recipe-ingredient-amount")),
            text(el.select_one(".wprm-recipe-ingredient-unit")),
            text(el.select_one(".wprm-recipe-ingredient-name")),
            text(el.select_one(".wprm-recipe-ingredient-notes")),
        ]
        line = " ".join(p for p in parts if p)
        # Some themes don't use the sub-spans; fall back to the whole row's text.
        ingredients.append(line or text(el))
    ingredients = [i for i in ingredients if i]

    instructions = [
        text(el)
        for el in container.select(".wprm-recipe-instruction-text")
        if text(el)
    ]

    if not ingredients and not instructions:
        return None

    image_el = container.select_one(".wprm-recipe-image img")
    image = None
    if image_el:
        image = image_el.get("data-src") or image_el.get("src")

    # WPRM splits total time into separate hour/minute spans; the class separator
    # varies (hyphen vs underscore) across versions, so match both. Normalize to a
    # plain minutes string to match the recipe-scrapers tier (frontend appends "min").
    def _minutes(*needles: str) -> int:
        for needle in needles:
            el = container.select_one(f'[class*="{needle}"]')
            digits = "".join(c for c in text(el) if c.isdigit())
            if digits:
                return int(digits)
        return 0

    hours = _minutes("total_time-hours", "total-time-hours")
    mins = _minutes("total_time-minutes", "total-time-minutes")
    total_minutes = hours * 60 + mins

    return Recipe(
        title=text(container.select_one(".wprm-recipe-name")) or None,
        ingredients=ingredients,
        instructions=instructions,
        image=image,
        total_time=str(total_minutes) if total_minutes else None,
        yields=text(container.select_one(".wprm-recipe-servings")) or None,
        source_url=url,
        extracted_via="wprm-html",
    )


def _parse_instructions(raw) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        return [s.strip() for s in raw.split("\n") if s.strip()]
    steps: list[str] = []
    for step in raw if isinstance(raw, list) else [raw]:
        if isinstance(step, str):
            steps.append(step.strip())
        elif isinstance(step, dict):
            # HowToStep, or HowToSection containing itemListElement
            if step.get("@type") == "HowToSection":
                steps.extend(_parse_instructions(step.get("itemListElement")))
            elif step.get("text"):
                steps.append(step["text"].strip())
    return [s for s in steps if s]


def _as_str_list(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [str(v).strip() for v in value if str(v).strip()]


def _as_str(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _extract_from_html(html: str, url: str) -> Recipe | None:
    """Run the parsing tiers in order against already-fetched HTML."""
    return (
        _try_recipe_scrapers(html, url)
        or _try_json_ld(html, url)
        or _try_wprm_html(html, url)
    )


async def extract_recipe(url: str) -> Recipe | None:
    """Fetch and extract, with a content-based anti-bot fallback.

    Some sites (e.g. natashaskitchen.com) serve a degraded decoy page with an HTTP
    *200* to non-browser TLS fingerprints, so a status-code-only fallback misses them.
    If the fast `httpx` fetch yields no recipe, we re-fetch with `curl_cffi`'s Chrome
    impersonation and try again before giving up.
    """
    html = await fetch_html(url)
    recipe = _extract_from_html(html, url)
    if recipe is not None:
        return recipe

    # No recipe found. Could be a soft block (200 + decoy body). Retry with
    # impersonation — unless fetch_html already fell back to curl_cffi for this page.
    try:
        impersonated = await _fetch_curl_cffi(url)
    except Exception:
        return None
    if impersonated != html:
        return _extract_from_html(impersonated, url)
    return None
