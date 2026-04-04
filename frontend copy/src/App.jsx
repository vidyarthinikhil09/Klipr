import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { supabase } from './services/supabase'
import { getYouTubeStatus } from './services/api'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Preview from './pages/Preview'
import Analytics from './pages/Analytics'
import Login from './pages/Login'
import YouTubeCallback from './pages/YouTubeCallback'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [youtubeConnected, setYoutubeConnected] = useState(null) // null = loading, true/false = known

  useEffect(() => {
    // Check initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null)
        // Reset YouTube status when user changes
        if (!session?.user) {
          setYoutubeConnected(null)
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  // Check YouTube connection once when user logs in
  useEffect(() => {
    if (user && youtubeConnected === null) {
      getYouTubeStatus()
        .then(status => setYoutubeConnected(status.connected))
        .catch(() => setYoutubeConnected(false))
    }
  }, [user])

  // Function to update YouTube status (called after connecting)
  const refreshYouTubeStatus = async () => {
    try {
      const status = await getYouTubeStatus()
      setYoutubeConnected(status.connected)
    } catch {
      setYoutubeConnected(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {user && <Navbar user={user} />}
      
      <main className={user ? 'pt-20' : ''}>
        <Routes>
          <Route 
            path="/login" 
            element={user ? <Navigate to="/" /> : <Login />} 
          />
          <Route 
            path="/" 
            element={user ? <Dashboard user={user} youtubeConnected={youtubeConnected} onYouTubeConnect={refreshYouTubeStatus} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/preview/:id" 
            element={user ? <Preview user={user} youtubeConnected={youtubeConnected} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/analytics" 
            element={user ? <Analytics user={user} youtubeConnected={youtubeConnected} /> : <Navigate to="/login" />} 
          />
          <Route 
            path="/auth/youtube/success" 
            element={<YouTubeCallback onSuccess={refreshYouTubeStatus} />} 
          />
        </Routes>
      </main>
    </div>
  )
}

export default App
