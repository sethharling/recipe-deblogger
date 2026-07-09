import { NavLink, Route, Routes } from 'react-router-dom'
import DeblogPage from './pages/DeblogPage'
import SavedPage from './pages/SavedPage'
import RecipeDetailPage from './pages/RecipeDetailPage'

// ponytail: replace with the real repo + tip jar URLs when you have them.
const REPO_URL = 'https://github.com/sethharling/recipe-deblogger'
const TIPJAR_URL = 'https://www.buymeacoffee.com/sethharling'

function Icon({ id }: { id: string }) {
  return (
    <svg className="icon" aria-hidden="true">
      <use href={`/icons.svg#${id}`} />
    </svg>
  )
}

function App() {
  return (
    <div className="app">
      <header>
        <h1>Recipe Deblogger</h1>
        <nav>
          <NavLink to="/">Deblog</NavLink>
          <NavLink to="/saved">Saved</NavLink>
        </nav>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<DeblogPage />} />
          <Route path="/saved" element={<SavedPage />} />
          <Route path="/recipe/:id" element={<RecipeDetailPage />} />
        </Routes>
      </main>

      <footer>
        <a href={REPO_URL} target="_blank" rel="noreferrer">
          <Icon id="github-icon" /> GitHub
        </a>
        <a href={TIPJAR_URL} target="_blank" rel="noreferrer">
          <Icon id="tipjar-icon" /> Tip jar
        </a>
      </footer>
    </div>
  )
}

export default App
