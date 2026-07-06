import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getRecipe, type Recipe } from '../api'
import RecipeView from '../RecipeView'

function RecipeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    getRecipe(Number(id))
      .then(setRecipe)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
  }, [id])

  return (
    <>
      <p>
        <Link to="/saved">← Back to saved</Link>
      </p>
      {error && <p className="error">{error}</p>}
      {recipe && <RecipeView recipe={recipe} />}
    </>
  )
}

export default RecipeDetailPage
