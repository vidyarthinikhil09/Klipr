import { Link, useLocation } from 'react-router-dom'
import { Home, BarChart3, LogOut, Youtube } from 'lucide-react'
import { signOut } from '../services/supabase'

function Navbar({ user }) {
  const location = useLocation()

  const handleSignOut = async () => {
    await signOut()
  }

  const navLinks = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card mx-4 mt-4 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-pink to-neon-purple flex items-center justify-center">
            <span className="text-xl">⚡</span>
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-neon-pink to-neon-blue bg-clip-text text-transparent">
            Klipr
          </span>
        </Link>

        {/* Nav Links */}
        <div className="hidden md:flex items-center gap-2">
          {navLinks.map(({ path, icon: Icon, label }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-300
                ${location.pathname === path 
                  ? 'bg-white/10 text-neon-blue' 
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
            >
              <Icon size={18} />
              <span>{label}</span>
            </Link>
          ))}
        </div>

        {/* User Menu */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5">
            <Youtube size={16} className="text-red-500" />
            <span className="text-sm text-gray-400">
              {user?.email?.split('@')[0]}
            </span>
          </div>
          
          <button
            onClick={handleSignOut}
            className="p-2 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
            title="Sign out"
          >
            <LogOut size={18} className="text-gray-400" />
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
