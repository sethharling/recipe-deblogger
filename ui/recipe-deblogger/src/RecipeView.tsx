import type { Recipe } from './api'

// Shared rendering of a single recipe, used on both the deblog page and the
// saved-recipe detail page.
function RecipeView({ recipe }: { recipe: Recipe }) {
  return (
    <article>
      {recipe.title && <h2>{recipe.title}</h2>}
      {recipe.image && <img src={recipe.image} alt="" width={300} />}
      <p>
        {recipe.yields && <>Serves: {recipe.yields}. </>}
        {recipe.total_time && <>Time: {recipe.total_time} min. </>}
      </p>

      <h3>Ingredients</h3>
      <ul>
        {recipe.ingredients.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>

      <h3>Instructions</h3>
      <ol>
        {recipe.instructions.map((step, i) => (
          <li key={i}>{step}</li>
        ))}
      </ol>

      <p>
        <a href={recipe.source_url} target="_blank" rel="noreferrer">
          Original source
        </a>{' '}
        (extracted via {recipe.extracted_via})
      </p>
    </article>
  )
}

export default RecipeView
