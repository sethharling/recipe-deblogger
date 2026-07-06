import { Link, Route, Routes } from 'react-router-dom'
import DeblogPage from './pages/DeblogPage'
import SavedPage from './pages/SavedPage'
import RecipeDetailPage from './pages/RecipeDetailPage'

function App() {
  return (
    <main>
      <h1>Recipe Deblogger</h1>
      <nav>
        <Link to="/">Deblog</Link> | <Link to="/saved">Saved</Link>
      </nav>

      <Routes>
        <Route path="/" element={<DeblogPage />} />
        <Route path="/saved" element={<SavedPage />} />
        <Route path="/recipe/:id" element={<RecipeDetailPage />} />
      </Routes>
    </main>
  )
}

export default App
