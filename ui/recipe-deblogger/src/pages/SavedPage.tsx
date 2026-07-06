import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listRecipes, type Recipe } from '../api'

function SavedPage() {
  const [query, setQuery] = useState('')
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    // Re-fetch as the user types (server does the title filtering + sorting).
    listRecipes(query)
      .then((data) => {
        if (!cancelled) setRecipes(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load')
      })
    return () => {
      cancelled = true
    }
  }, [query])

  return (
    <>
      <h2>Saved recipes</h2>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search by title"
        size={40}
      />

      {error && <p className="error">{error}</p>}
      {recipes.length === 0 ? (
        <p>No recipes{query ? ' match your search' : ' saved yet'}.</p>
      ) : (
        <ul>
          {recipes.map((r) => (
            <li key={r.id}>
              <Link to={`/recipe/${r.id}`}>{r.title ?? r.source_url}</Link>
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

export default SavedPage
