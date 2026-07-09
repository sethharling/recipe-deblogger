import { useState } from 'react'
import { debloggRecipe, type Recipe } from '../api'
import RecipeView from '../RecipeView'

function DeblogPage() {
  const [url, setUrl] = useState('')
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setRecipe(null)
    try {
      setRecipe(await debloggRecipe(url))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <p className="intro">
        Every online recipe is buried under a life story, a dozen ads, and three
        pop-ups that keep you from the one thing you came for. Paste a recipe link and
        we&rsquo;ll strip all of it away — just the ingredients and steps, in a clean
        page, saved to your collection.
      </p>

      <form onSubmit={handleSubmit}>
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste a recipe URL"
          size={50}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Working…' : 'Deblog'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {recipe && (
        <>
          <p>Saved to your collection.</p>
          <RecipeView recipe={recipe} />
        </>
      )}
    </>
  )
}

export default DeblogPage
