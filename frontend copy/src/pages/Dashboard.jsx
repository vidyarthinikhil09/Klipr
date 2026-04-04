import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Search, Zap, Gamepad2, User, RefreshCw, 
  Play, Clock, Eye, AlertCircle, XCircle, Video, Sparkles, Type, Cpu
} from 'lucide-react'
import { 
  discoverClip, generateVideo, subscribeToProgress,
  getCreators, getGames, getNiches, connectYouTube, getVideos,
  CAPTION_STYLES, getRendererStatus
} from '../services/api'

function Dashboard({ user, youtubeConnected: ytConnectedProp, onYouTubeConnect }) {
  const navigate = useNavigate()
  const [mode, setMode] = useState('creator') // 'creator', 'game', or 'niche'
  const [selectedCreator, setSelectedCreator] = useState('')
  const [selectedGame, setSelectedGame] = useState('')
  const [selectedNiche, setSelectedNiche] = useState('')
  const [selectedCaptionStyle, setSelectedCaptionStyle] = useState('mrbeast')
  const [creators, setCreators] = useState({ tier1: [], tier2: [], tier3: [] })
  const [games, setGames] = useState({})
  const [niches, setNiches] = useState({})
  const [clip, setClip] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [progress, setProgress] = useState({ step: '', progress: 0, message: '' })
  const [error, setError] = useState('')
  const [pendingVideo, setPendingVideo] = useState(null) // Video waiting for review
  const [rendererStatus, setRendererStatus] = useState(null) // pycaps availability
  const cancelRef = useRef(null) // To cancel polling

  // Use prop from App (cached) - null means still loading
  const youtubeConnected = ytConnectedProp === true

  useEffect(() => {
    loadConfig()
    checkPendingVideo()
    loadRendererStatus()
  }, [])

  const loadConfig = async () => {
    try {
      const [creatorsData, gamesData, nichesData] = await Promise.all([
        getCreators(),
        getGames(),
        getNiches()
      ])
      setCreators(creatorsData)
      setGames(gamesData)
      setNiches(nichesData)
    } catch (err) {
      console.error('Failed to load config:', err)
    }
  }

  const loadRendererStatus = async () => {
    try {
      const status = await getRendererStatus()
      setRendererStatus(status)
      console.log('[Dashboard] Renderer status:', status)
    } catch (err) {
      console.error('Failed to load renderer status:', err)
    }
  }

  // Check if there's a draft video waiting to be reviewed
  const checkPendingVideo = async () => {
    try {
      const data = await getVideos(1)
      if (data.videos && data.videos.length > 0) {
        const latest = data.videos[0]
        if (latest.status === 'draft') {
          setPendingVideo(latest)
        }
      }
    } catch (err) {
      console.error('Failed to check pending videos:', err)
    }
  }

  const handleConnectYouTube = async () => {
    try {
      const { oauth_url } = await connectYouTube()
      window.location.href = oauth_url
    } catch (err) {
      setError('Failed to start YouTube connection')
    }
  }

  const handleDiscover = async () => {
    setLoading(true)
    setError('')
    setClip(null)

    try {
      const result = await discoverClip(
        mode,
        mode === 'creator' ? selectedCreator || null : null,
        mode === 'game' ? selectedGame || null : null,
        mode === 'niche' ? selectedNiche || null : null
      )

      if (result.success && result.clip) {
        setClip(result.clip)
      } else {
        setError(result.message || 'No clips found')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to discover clip')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!clip) return

    setGenerating(true)
    setError('')
    setProgress({ step: 'starting', progress: 0, message: 'Starting...' })

    try {
      const result = await generateVideo(clip.url, clip.broadcaster_name, null, null, selectedCaptionStyle)

      if (result.success) {
        // Subscribe to progress updates
        const taskId = result.message.split('Task ID: ')[1]
        
        // Store cancel function
        cancelRef.current = subscribeToProgress(taskId, (data) => {
          setProgress(data)

          if (data.status === 'complete' && data.video?.id) {
            setGenerating(false)
            cancelRef.current = null
            navigate(`/preview/${data.video.id}`)
          } else if (data.status === 'error') {
            setError(data.message)
            setGenerating(false)
            cancelRef.current = null
          }
        })
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate video')
      setGenerating(false)
    }
  }

  const handleCancelGeneration = () => {
    if (cancelRef.current) {
      cancelRef.current() // Stop polling
      cancelRef.current = null
    }
    setGenerating(false)
    setProgress({ step: '', progress: 0, message: '' })
    setError('Generation cancelled')
  }

  const allCreators = [...creators.tier1, ...creators.tier2, ...creators.tier3]

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="bg-gradient-to-r from-neon-pink via-neon-purple to-neon-blue bg-clip-text text-transparent">
            Create Viral Shorts
          </span>
        </h1>
        <p className="text-gray-400 text-lg">
          AI-powered clip discovery → Auto-generated captions → YouTube upload
        </p>
      </div>

      {/* YouTube Connection Banner - only show when confirmed not connected */}
      {ytConnectedProp === false && (
        <div className="glass-card p-4 mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="text-yellow-500" />
            <span>Connect your YouTube account to upload videos</span>
          </div>
          <button onClick={handleConnectYouTube} className="btn-primary text-sm">
            Connect YouTube
          </button>
        </div>
      )}

      {/* Pending Video Banner */}
      {pendingVideo && (
        <div className="glass-card p-4 mb-8 border border-neon-green/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Video className="text-neon-green" />
              <div>
                <span className="font-semibold text-neon-green">Video Ready for Review!</span>
                <p className="text-sm text-gray-400 mt-1">
                  "{pendingVideo.title?.substring(0, 50)}..." — Review before creating new clips
                </p>
              </div>
            </div>
            <button 
              onClick={() => navigate(`/preview/${pendingVideo.id}`)} 
              className="btn-primary text-sm flex items-center gap-2"
            >
              <Eye size={16} />
              Review Video
            </button>
          </div>
        </div>
      )}

      {/* Mode Toggle */}
      <div className="flex justify-center gap-4 mb-8 flex-wrap">
        <button
          onClick={() => setMode('creator')}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all duration-300
            ${mode === 'creator' 
              ? 'bg-gradient-to-r from-neon-pink to-neon-purple text-white' 
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
        >
          <User size={20} />
          By Creator
        </button>
        <button
          onClick={() => setMode('game')}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all duration-300
            ${mode === 'game' 
              ? 'bg-gradient-to-r from-neon-blue to-neon-green text-white' 
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
        >
          <Gamepad2 size={20} />
          By Game
        </button>
        <button
          onClick={() => setMode('niche')}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all duration-300
            ${mode === 'niche' 
              ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white' 
              : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
        >
          <Sparkles size={20} />
          By Niche
        </button>
      </div>

      {/* Selection Area */}
      <div className="glass-card p-6 mb-8">
        {mode === 'creator' && (
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Select Creator (or leave empty for auto-selection)
            </label>
            <select
              value={selectedCreator}
              onChange={(e) => setSelectedCreator(e.target.value)}
              className="select-genz"
            >
              <option value="">🔥 Auto - Best Trending Clip</option>
              <optgroup label="Tier 1 - Top Creators">
                {creators.tier1.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </optgroup>
              <optgroup label="Tier 2 - Popular">
                {creators.tier2.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </optgroup>
              <optgroup label="Tier 3 - Rising">
                {creators.tier3.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </optgroup>
            </select>
          </div>
        )}

        {mode === 'game' && (
          <div>
            <label className="block text-sm text-gray-400 mb-4">Select Game</label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(games).map(([name, id]) => (
                <button
                  key={name}
                  onClick={() => setSelectedGame(name)}
                  className={`game-card text-center ${selectedGame === name ? 'selected' : ''}`}
                >
                  <div className="text-2xl mb-2">🎮</div>
                  <div className="text-sm font-medium">{name}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {mode === 'niche' && (
          <div>
            <label className="block text-sm text-gray-400 mb-4">Select Content Niche</label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(niches).map(([name, data]) => (
                <button
                  key={name}
                  onClick={() => setSelectedNiche(name)}
                  className={`game-card text-left ${selectedNiche === name ? 'selected' : ''}`}
                >
                  <div className="text-2xl mb-2">{data.emoji}</div>
                  <div className="text-sm font-medium mb-1">{name}</div>
                  <div className="text-xs text-gray-400">{data.description}</div>
                  <div className="text-xs text-gray-500 mt-2">
                    {data.creators?.slice(0, 3).join(', ')}...
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Discover Button */}
        <button
          onClick={handleDiscover}
          disabled={loading || generating || pendingVideo || (mode === 'game' && !selectedGame) || (mode === 'niche' && !selectedNiche)}
          className="btn-primary w-full mt-6 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <RefreshCw className="animate-spin" size={20} />
              Searching...
            </>
          ) : pendingVideo ? (
            <>
              <AlertCircle size={20} />
              Review Pending Video First
            </>
          ) : (
            <>
              <Search size={20} />
              Find Best Clip
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="glass-card p-4 mb-8 border border-red-500/50 bg-red-500/10">
          <div className="flex items-center gap-3 text-red-400">
            <AlertCircle size={20} />
            {error}
          </div>
        </div>
      )}

      {/* Clip Preview */}
      {clip && !pendingVideo && (
        <div className="glass-card p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Play className="text-neon-green" />
              Found Clip
            </h3>
            {!generating && (
              <button
                onClick={() => setClip(null)}
                className="text-sm text-gray-400 hover:text-neon-pink flex items-center gap-1"
              >
                <XCircle size={16} />
                Clear & Find New
              </button>
            )}
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Thumbnail with Play Button */}
            <div className="aspect-video rounded-xl overflow-hidden bg-black relative group cursor-pointer"
                 onClick={() => window.open(clip.url, '_blank')}>
              <img 
                src={clip.thumbnail_url} 
                alt={clip.title}
                className="w-full h-full object-cover group-hover:opacity-75 transition-opacity"
              />
              {/* Play Button Overlay */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-16 h-16 rounded-full bg-black/60 flex items-center justify-center group-hover:bg-neon-purple/80 transition-all group-hover:scale-110">
                  <Play size={32} className="text-white ml-1" fill="white" />
                </div>
              </div>
              <div className="absolute bottom-2 left-2 bg-black/70 px-2 py-1 rounded text-xs text-white">
                Click to preview clip
              </div>
            </div>

            {/* Details */}
            <div>
              <h4 className="text-lg font-semibold mb-2">{clip.title}</h4>
              <p className="text-gray-400 mb-4">by {clip.broadcaster_name}</p>
              
              <div className="flex flex-wrap gap-3 mb-6">
                <span className="stats-badge flex items-center gap-1">
                  <Eye size={14} />
                  {clip.view_count.toLocaleString()} views
                </span>
                <span className="stats-badge flex items-center gap-1">
                  <Clock size={14} />
                  {Math.round(clip.duration)}s
                </span>
              </div>

              {/* Warning text */}
              <p className="text-xs text-gray-500 mb-3 text-center">
                ⏱️ Generation takes 1-3 minutes. Please wait.
              </p>

              {/* Caption Style Selector */}
              {!generating && (
                <div className="mb-4">
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <Type size={14} />
                    Caption Style
                    {rendererStatus && (
                      <span className={`ml-auto text-xs px-2 py-0.5 rounded-full flex items-center gap-1 ${
                        rendererStatus.pycaps_available 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        <Cpu size={10} />
                        {rendererStatus.pycaps_available ? 'pycaps' : 'MoviePy'}
                      </span>
                    )}
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(CAPTION_STYLES).map(([key, style]) => (
                      <button
                        key={key}
                        onClick={() => setSelectedCaptionStyle(key)}
                        className={`p-2 rounded-lg text-center transition-all ${
                          selectedCaptionStyle === key
                            ? 'bg-gradient-to-r from-neon-pink to-neon-purple text-white'
                            : 'bg-white/5 text-gray-400 hover:bg-white/10'
                        }`}
                      >
                        <div className="text-lg mb-1">{style.emoji}</div>
                        <div className="text-xs font-medium">{style.name}</div>
                      </button>
                    ))}
                  </div>
                  {rendererStatus && !rendererStatus.pycaps_available && (
                    <p className="text-xs text-yellow-500/80 mt-2">
                      💡 Install ffmpeg for CSS animations. Using MoviePy fallback.
                    </p>
                  )}
                </div>
              )}

              {/* Generate Button */}
              {generating ? (
                <button
                  onClick={handleCancelGeneration}
                  className="btn-secondary w-full flex items-center justify-center gap-2 border-red-500/50 hover:bg-red-500/20"
                >
                  <XCircle size={20} className="text-red-400" />
                  <span className="text-red-400">Cancel Generation</span>
                </button>
              ) : (
                <button
                  onClick={handleGenerate}
                  disabled={generating}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  <Zap size={20} />
                  Generate Video
                </button>
              )}

              {/* Progress Bar */}
              {generating && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-neon-green">{progress.message || 'Starting...'}</span>
                    <span className="text-sm font-bold text-neon-blue">{progress.progress}%</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-bar-fill transition-all duration-300"
                      style={{ width: `${progress.progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2 text-center">
                    Step: {progress.step || 'initializing'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
