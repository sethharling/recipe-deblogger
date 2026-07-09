export const API_BASE = 'https://recipe-deblogger.onrender.com'

export type Recipe = {
  id: number
  source_url: string
  title: string | null
  ingredients: string[]
  instructions: string[]
  image: string | null
  total_time: string | null
  yields: string | null
  extracted_via: string
  created_at: string
}

async function asJsonOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${res.status})`)
  }
  return res.json()
}

export async function debloggRecipe(url: string): Promise<Recipe> {
  const res = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  return asJsonOrThrow(res)
}

export async function listRecipes(query: string): Promise<Recipe[]> {
  const params = new URLSearchParams({ sort: 'title' })
  if (query) params.set('q', query)
  const res = await fetch(`${API_BASE}/recipes?${params}`)
  return asJsonOrThrow(res)
}

export async function getRecipe(id: number): Promise<Recipe> {
  const res = await fetch(`${API_BASE}/recipes/${id}`)
  return asJsonOrThrow(res)
}
