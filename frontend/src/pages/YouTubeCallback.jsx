import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle } from 'lucide-react'

function YouTubeCallback({ onSuccess }) {
  const navigate = useNavigate()

  useEffect(() => {
    // Notify parent that YouTube was connected
    if (onSuccess) {
      onSuccess()
    }
    
    // Redirect to dashboard after 2 seconds
    const timer = setTimeout(() => {
      navigate('/')
    }, 2000)

    return () => clearTimeout(timer)
  }, [navigate, onSuccess])

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="glass-card p-8 text-center max-w-md">
        <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
          <CheckCircle size={32} className="text-green-500" />
        </div>
        <h1 className="text-2xl font-bold mb-2">YouTube Connected!</h1>
        <p className="text-gray-400 mb-4">
          Your YouTube account has been successfully linked.
        </p>
        <p className="text-sm text-gray-500">
          Redirecting to dashboard...
        </p>
      </div>
    </div>
  )
}

export default YouTubeCallback
