import axios from 'axios'
import { supabase } from './supabase'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

// Create axios instance with auth interceptor
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

// API Methods

// Clips
export const discoverClip = async (mode, creator = null, game = null, niche = null) => {
  const response = await api.post('/clips/discover', { mode, creator, game, niche, auto: true })
  return response.data
}

export const downloadClip = async (clipUrl) => {
  const response = await api.post('/clips/download', null, { params: { clip_url: clipUrl } })
  return response.data
}

export const getCreators = async () => {
  const response = await api.get('/clips/creators')
  return response.data
}

export const getGames = async () => {
  const response = await api.get('/clips/games')
  return response.data
}

export const getNiches = async () => {
  const response = await api.get('/clips/niches')
  return response.data
}

// Caption styles available
export const CAPTION_STYLES = {
  mrbeast: { name: "MrBeast Style", emoji: "🔥", description: "Bold gold highlights" },
  hormozi: { name: "Hormozi Style", emoji: "💰", description: "Green pop with scale" },
  tiktok: { name: "TikTok Trending", emoji: "📱", description: "Pink & cyan vibes" },
  karaoke: { name: "Karaoke Style", emoji: "🎤", description: "Dimmed with glow" },
  minimalist: { name: "Minimalist", emoji: "✨", description: "Clean & simple" },
  classic: { name: "Classic Viral", emoji: "🎬", description: "Red accent pop" }
}

// Videos
export const generateVideo = async (clipUrl, creator, titleOverride = null, descriptionOverride = null, captionStyle = "mrbeast") => {
  const response = await api.post('/videos/generate', {
    clip_url: clipUrl,
    creator: creator,
    title_override: titleOverride,
    description_override: descriptionOverride,
    caption_style: captionStyle
  })
  return response.data
}

export const getVideos = async (limit = 20) => {
  const response = await api.get('/videos', { params: { limit } })
  return response.data
}

export const getVideo = async (videoId) => {
  const response = await api.get(`/videos/${videoId}`)
  return response.data
}

export const updateVideo = async (videoId, data) => {
  const response = await api.patch(`/videos/${videoId}`, data)
  return response.data
}

export const deleteVideo = async (videoId) => {
  const response = await api.delete(`/videos/${videoId}`)
  return response.data
}

// Video progress - use polling (more reliable than SSE)
export const subscribeToProgress = (taskId, onProgress) => {
  let intervalId = null
  let stopped = false
  
  console.log('[Progress] Starting polling for task:', taskId)
  
  const poll = async () => {
    if (stopped) return
    
    try {
      const response = await api.get(`/videos/status/${taskId}`)
      const data = response.data
      console.log('[Progress] Got update:', data)
      onProgress(data)
      
      if (data.status === 'complete' || data.status === 'error') {
        console.log('[Progress] Task finished:', data.status)
        if (intervalId) clearInterval(intervalId)
        return
      }
    } catch (err) {
      console.error('Progress poll error:', err)
    }
  }
  
  // Poll immediately, then every 1 second
  poll()
  intervalId = setInterval(poll, 1000)
  
  // Return cleanup function
  return () => {
    console.log('[Progress] Stopping polling')
    stopped = true
    if (intervalId) clearInterval(intervalId)
  }
}

// Upload
export const uploadToYouTube = async (videoId, title = null, description = null, tags = null) => {
  const response = await api.post('/upload/youtube', {
    video_id: videoId,
    title,
    description,
    tags
  })
  return response.data
}

export const getYouTubeQuota = async () => {
  const response = await api.get('/upload/youtube/quota')
  return response.data
}

// Analytics
export const getAnalyticsSummary = async () => {
  const response = await api.get('/analytics/summary')
  return response.data
}

export const refreshAnalytics = async (videoId = null) => {
  const response = await api.post('/analytics/refresh', { video_id: videoId })
  return response.data
}

export const getAIFeedback = async () => {
  const response = await api.get('/analytics/feedback')
  return response.data
}

// Auth
export const connectYouTube = async () => {
  const response = await api.get('/auth/youtube/connect')
  return response.data
}

export const getYouTubeStatus = async () => {
  const response = await api.get('/auth/youtube/status')
  return response.data
}

// Health
export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}

export const getConfig = async () => {
  const response = await api.get('/config')
  return response.data
}

// Renderer status (pycaps availability)
export const getRendererStatus = async () => {
  const response = await api.get('/videos/renderer/status')
  return response.data
}

export default api
