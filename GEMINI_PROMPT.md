# 🎨 AutoShorts Frontend Redesign - Complete Prompt for Gemini

> **IMPORTANT**: I need you to redesign the UI of my React frontend while keeping ALL the backend integration code working. The backend is FastAPI and must NOT change.

---

## 🎯 Your Task

Redesign the visual appearance of my AutoShorts dashboard (YouTube Shorts automation tool) while:
1. **KEEPING** all API calls exactly as they are
2. **KEEPING** all routes exactly as they are  
3. **KEEPING** all state management logic
4. **CHANGING** only the visual design (colors, layout, components, animations)

---

## 📁 Required Project Structure

You MUST output files in this exact structure:

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.example
│
└── src/
    ├── main.jsx                 # Entry point
    ├── App.jsx                  # Routes + auth state
    ├── index.css                # Global styles
    │
    ├── services/                # ⚠️ COPY EXACTLY - DO NOT MODIFY
    │   ├── api.js               # Backend API calls
    │   └── supabase.js          # Auth client
    │
    ├── pages/
    │   ├── Login.jsx            # Google sign-in
    │   ├── Dashboard.jsx        # Clip finder + video generator
    │   ├── Preview.jsx          # Video preview + upload
    │   ├── Analytics.jsx        # Performance metrics
    │   └── YouTubeCallback.jsx  # OAuth callback
    │
    └── components/
        ├── Navbar.jsx           # Top navigation
        └── (any new components)
```

---

## 🚨 CRITICAL FILES - COPY EXACTLY (DO NOT MODIFY)

### File: `src/services/api.js`
```javascript
import axios from 'axios'
import { supabase } from './supabase'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

// Clips
export const discoverClip = async (mode, creator = null, game = null, niche = null) => {
  const response = await api.post('/clips/discover', { mode, creator, game, niche, auto: true })
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

// Caption styles
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

// Progress polling
export const subscribeToProgress = (taskId, onProgress) => {
  let intervalId = null
  let stopped = false
  
  const poll = async () => {
    if (stopped) return
    try {
      const response = await api.get(`/videos/status/${taskId}`)
      const data = response.data
      onProgress(data)
      if (data.status === 'complete' || data.status === 'error') {
        if (intervalId) clearInterval(intervalId)
      }
    } catch (err) {
      console.error('Progress poll error:', err)
    }
  }
  
  poll()
  intervalId = setInterval(poll, 1000)
  
  return () => {
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

// YouTube Auth
export const connectYouTube = async () => {
  const response = await api.get('/auth/youtube/connect')
  return response.data
}

export const getYouTubeStatus = async () => {
  const response = await api.get('/auth/youtube/status')
  return response.data
}

// Analytics
export const getAnalyticsSummary = async () => {
  const response = await api.get('/analytics/summary')
  return response.data
}

export const getRendererStatus = async () => {
  const response = await api.get('/videos/renderer/status')
  return response.data
}

export default api
```

### File: `src/services/supabase.js`
```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export const signInWithGoogle = async () => {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin
    }
  })
  return { data, error }
}

export const signOut = async () => {
  const { error } = await supabase.auth.signOut()
  return { error }
}

export const getSession = async () => {
  const { data: { session }, error } = await supabase.auth.getSession()
  return { session, error }
}
```

---

## 📄 Required Routes (App.jsx must have these)

```javascript
// These exact routes MUST exist:
<Route path="/login" element={<Login />} />
<Route path="/" element={<Dashboard />} />           // Protected
<Route path="/preview/:id" element={<Preview />} />  // Protected
<Route path="/analytics" element={<Analytics />} />  // Protected
<Route path="/auth/youtube/success" element={<YouTubeCallback />} />
```

---

## 📄 Required Page Features

### 1. Login Page (`/login`)
- Google sign-in button
- Calls `signInWithGoogle()` from supabase.js
- Redirects to `/` after login

### 2. Dashboard Page (`/`)
Must have these sections:

**A. Mode Selector** (3 tabs/buttons):
- Creator mode
- Game mode  
- Niche mode

**B. Search Controls**:
- Dropdown that changes based on mode:
  - Creator mode: Show creators from `getCreators()` (returns `{tier1: [], tier2: [], tier3: []}`)
  - Game mode: Show games from `getGames()` (returns `{"Game Name": id, ...}`)
  - Niche mode: Show niches from `getNiches()`
- "Find Clip" button → calls `discoverClip(mode, creator, game, niche)`

**C. Clip Preview** (after discovery):
- Thumbnail image from `clip.thumbnail_url`
- Play button that opens `clip.url` in new tab
- Show: `clip.title`, `clip.view_count`, `clip.duration`

**D. Generation Controls**:
- Caption style dropdown (use `CAPTION_STYLES` object)
- "Generate Video" button → calls `generateVideo()`
- Progress bar (0-100%) using `subscribeToProgress(taskId, callback)`
- Status message display

**E. YouTube Connection**:
- If not connected: "Connect YouTube" button → calls `connectYouTube()` and redirects to `oauth_url`
- If connected: Show "✅ YouTube Connected"

### 3. Preview Page (`/preview/:id`)
- Video player: `<video src={API_URL + '/output/' + filename} controls />`
- Editable title input
- Editable description textarea
- Tags display
- "Upload to YouTube" button → calls `uploadToYouTube(videoId, title, description, tags)`
- "Discard" button → calls `deleteVideo(videoId)`
- "Back" button → navigate to `/`

### 4. Analytics Page (`/analytics`)
- Summary cards: total_videos, total_views, avg_score
- Video table with columns: title, views, CTR, watch_time, score
- Data from `getAnalyticsSummary()`

### 5. YouTubeCallback Page (`/auth/youtube/success`)
- Simple page that shows "Connected!" and redirects to `/`

---

## 📦 Required Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.1",
    "@supabase/supabase-js": "^2.39.0",
    "axios": "^1.6.5",
    "lucide-react": "^0.303.0",
    "recharts": "^2.10.3"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.33",
    "vite": "^5.0.11"
  }
}
```

---

## 🎨 Design Direction

Create a modern, professional dashboard with:
- Dark theme preferred (or light with dark accents)
- Clean typography (Inter, JetBrains Mono for code)
- Card-based layouts with subtle shadows/borders
- Smooth animations/transitions
- Mobile responsive
- Professional color palette (not too flashy)

You can use any UI approach:
- Pure Tailwind CSS
- shadcn/ui components
- Custom components
- Framer Motion for animations

---

## ✅ Output Checklist

Before submitting, verify:
- [ ] `services/api.js` copied exactly (no changes)
- [ ] `services/supabase.js` copied exactly (no changes)
- [ ] All 5 routes exist in App.jsx
- [ ] Dashboard has: mode selector, search dropdown, clip preview, caption style selector, progress bar
- [ ] Preview has: video player, editable metadata, upload button
- [ ] Analytics has: summary cards, video table
- [ ] Login has: Google sign-in button
- [ ] Protected routes redirect to /login when not authenticated

---

## 🚀 Start

Please generate the complete frontend code with:
1. All files listed in the structure
2. `services/api.js` and `services/supabase.js` copied EXACTLY as shown above
3. Beautiful, modern UI design
4. All functionality working with the API calls

Output each file with its full path and complete code.
