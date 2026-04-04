# 🎨 AutoShorts Frontend Redesign Guide

> **For AI Assistants (Gemini, Claude, ChatGPT)**: This document contains everything you need to safely redesign the frontend UI without breaking backend integration.

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Folder Structure](#-folder-structure)
3. [Critical Files (DO NOT MODIFY)](#-critical-files-do-not-modify)
4. [Files You CAN Redesign](#-files-you-can-redesign)
5. [Backend API Contract](#-backend-api-contract)
6. [Authentication Flow](#-authentication-flow)
7. [Page Requirements](#-page-requirements)
8. [State Management Rules](#-state-management-rules)
9. [Current Styling System](#-current-styling-system)
10. [Design Freedom & Constraints](#-design-freedom--constraints)
11. [Testing Checklist](#-testing-checklist)

---

## 🎯 Overview

**Project**: AutoShorts - AI-powered Twitch to YouTube Shorts automation  
**Frontend Stack**: React 18 + Vite + Tailwind CSS  
**Backend Stack**: FastAPI (Python) - **DO NOT MODIFY**  
**Auth**: Supabase (Google OAuth)  
**State**: React useState/useEffect (no Redux)

### What You're Redesigning

A 3-page dashboard application:
1. **Dashboard** (`/`) - Find clips, generate videos
2. **Preview** (`/preview/:id`) - Review & upload to YouTube
3. **Analytics** (`/analytics`) - View performance metrics

---

## 📁 Folder Structure

```
frontend/
│
├── index.html                    # Entry HTML (can modify title/meta)
├── package.json                  # Dependencies (can add, don't remove)
├── vite.config.js                # Vite config (usually don't need to change)
├── tailwind.config.js            # Tailwind config (can customize theme)
├── postcss.config.js             # PostCSS config (usually don't change)
│
├── .env                          # Environment variables (DO NOT COMMIT)
├── .env.example                  # Env template
│
└── src/
    │
    ├── main.jsx                  # React entry point (usually don't change)
    ├── App.jsx                   # Root component + routing (keep routes!)
    │
    ├── pages/                    # ✅ CAN REDESIGN (keep functionality)
    │   ├── Login.jsx             # Google sign-in page
    │   ├── Dashboard.jsx         # Main clip finder + generator
    │   ├── Preview.jsx           # Video preview + metadata editor
    │   ├── Analytics.jsx         # Performance dashboard
    │   └── YouTubeCallback.jsx   # OAuth callback (minimal UI)
    │
    ├── components/               # ✅ CAN REDESIGN / ADD NEW
    │   └── Navbar.jsx            # Top navigation bar
    │
    ├── services/                 # ❌ DO NOT MODIFY
    │   ├── api.js                # Backend API integration
    │   └── supabase.js           # Supabase auth client
    │
    ├── hooks/                    # ✅ CAN ADD custom hooks
    │   └── (empty)
    │
    └── styles/                   # ✅ CAN REDESIGN
        └── index.css             # Tailwind + custom CSS
```

---

## 🚨 Critical Files (DO NOT MODIFY)

### 1. `src/services/api.js`
**Why**: Contains all backend API calls with exact endpoint paths, request formats, and response handling.

```javascript
// These functions MUST be used as-is:
discoverClip(mode, creator, game, niche)
generateVideo(clipUrl, creator, titleOverride, descOverride, captionStyle)
subscribeToProgress(taskId, onProgress)
getVideos(limit)
getVideo(videoId)
updateVideo(videoId, data)
deleteVideo(videoId)
uploadToYouTube(videoId, title, description, tags)
connectYouTube()
getYouTubeStatus()
getAnalyticsSummary()
getCreators()
getGames()
getNiches()
getRendererStatus()
healthCheck()
```

### 2. `src/services/supabase.js`
**Why**: Handles Google OAuth authentication.

```javascript
// These functions MUST be used as-is:
signInWithGoogle()
signOut()
getSession()
supabase  // The client instance
```

### 3. Route Paths in `App.jsx`
**Why**: Backend expects these exact callback URLs.

```javascript
// These routes MUST exist:
/login              // Login page
/                   // Dashboard (protected)
/preview/:id        // Video preview (protected)
/analytics          // Analytics (protected)
/auth/youtube/success  // YouTube OAuth callback
```

---

## ✅ Files You CAN Redesign

| File | What You Can Change |
|------|---------------------|
| `pages/Login.jsx` | Entire UI, keep `signInWithGoogle()` call |
| `pages/Dashboard.jsx` | Entire UI, keep all API calls and state logic |
| `pages/Preview.jsx` | Entire UI, keep video player and API calls |
| `pages/Analytics.jsx` | Entire UI, keep data fetching |
| `pages/YouTubeCallback.jsx` | Simple redirect page, minimal changes needed |
| `components/Navbar.jsx` | Entire UI, keep sign-out functionality |
| `styles/index.css` | All styles, can replace entirely |
| `tailwind.config.js` | Theme customization |

---

## 📡 Backend API Contract

### Environment Variables Required
```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
VITE_API_URL=http://localhost:8000
```

### API Base URL
```javascript
const API_BASE = import.meta.env.VITE_API_URL || '/api'
```

### Authentication Header
All API calls automatically include:
```
Authorization: Bearer <supabase_jwt_token>
```

---

### Clip Discovery API

#### `discoverClip(mode, creator, game, niche)`

**Request**:
```javascript
POST /api/clips/discover
{
  "mode": "creator" | "game" | "niche",
  "creator": "xQc" | null,
  "game": "Just Chatting" | null,
  "niche": "comedy" | null,
  "auto": true
}
```

**Response**:
```javascript
{
  "success": true,
  "clip": {
    "id": "AwkwardHelplessSalamanderSwiftRage",
    "url": "https://clips.twitch.tv/...",
    "embed_url": "https://clips.twitch.tv/embed?clip=...",
    "broadcaster_name": "xQc",
    "title": "XQC LOSES IT",
    "view_count": 250000,
    "duration": 30.0,
    "thumbnail_url": "https://clips-media-assets2.twitch.tv/...",
    "created_at": "2024-01-15T12:00:00Z",
    "game_id": "509658"
  },
  "message": "Found trending clip"
}
```

#### `getCreators()`
**Response**:
```javascript
{
  "tier1": ["IShowSpeed", "Kai Cenat", "xQc", "MrBeast Gaming", "Adin Ross"],
  "tier2": ["Tyler1", "Pokimane", "Ninja", ...],
  "tier3": ["QTCinderella", "Penguinz0", ...]
}
```

#### `getGames()`
**Response**:
```javascript
{
  "Just Chatting": 509658,
  "Fortnite": 33214,
  "Grand Theft Auto V": 32982,
  ...
}
```

#### `getNiches()`
**Response**:
```javascript
{
  "comedy": ["creator1", "creator2"],
  "gaming": ["creator3", "creator4"],
  "irl": ["creator5", "creator6"]
}
```

---

### Video Generation API

#### `generateVideo(clipUrl, creator, titleOverride, descOverride, captionStyle)`

**Request**:
```javascript
POST /api/videos/generate
{
  "clip_url": "https://clips.twitch.tv/...",
  "creator": "xQc",
  "title_override": null,           // Optional custom title
  "description_override": null,     // Optional custom description
  "caption_style": "mrbeast"        // See caption styles below
}
```

**Response**:
```javascript
{
  "success": true,
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Video generation started"
}
```

#### Caption Styles (MUST offer these options):
```javascript
const CAPTION_STYLES = {
  mrbeast: { name: "MrBeast Style", emoji: "🔥", description: "Bold gold highlights" },
  hormozi: { name: "Hormozi Style", emoji: "💰", description: "Green pop with scale" },
  tiktok: { name: "TikTok Trending", emoji: "📱", description: "Pink & cyan vibes" },
  karaoke: { name: "Karaoke Style", emoji: "🎤", description: "Dimmed with glow" },
  minimalist: { name: "Minimalist", emoji: "✨", description: "Clean & simple" },
  classic: { name: "Classic Viral", emoji: "🎬", description: "Red accent pop" }
}
```

---

### Progress Tracking API

#### `subscribeToProgress(taskId, onProgress)`

This uses **polling** (not WebSocket). The callback receives:

```javascript
{
  "step": "transcribing" | "generating_metadata" | "rendering" | "complete" | "error",
  "progress": 0-100,
  "message": "Transcribing audio...",
  "status": "running" | "complete" | "error"
}
```

**Usage**:
```javascript
const cleanup = subscribeToProgress(taskId, (data) => {
  setProgress(data.progress)
  setMessage(data.message)
  
  if (data.status === 'complete') {
    // Video is ready, navigate to preview
    navigate(`/preview/${videoId}`)
  }
  if (data.status === 'error') {
    setError(data.message)
  }
})

// Call cleanup() when component unmounts
useEffect(() => () => cleanup?.(), [])
```

---

### Video CRUD API

#### `getVideos(limit)`
**Response**:
```javascript
{
  "videos": [
    {
      "id": "uuid-here",
      "youtube_id": null,  // null if not uploaded
      "title": "😱 xQc's INSANE Gaming moment",
      "description": "Watch xQc lose his mind...",
      "tags": ["xqc", "gaming", "twitch"],
      "creator": "xQc",
      "clip_url": "https://clips.twitch.tv/...",
      "hook_style": "question",
      "model_used": "qwen/qwen3-30b-a3b:free",
      "views": 0,
      "likes": 0,
      "watch_time_pct": 0,
      "ctr": 0,
      "score": 0,
      "status": "draft" | "uploaded" | "failed",
      "local_path": "output/short_abc123.mp4",
      "created_at": "2024-01-15T12:00:00Z"
    }
  ]
}
```

#### `getVideo(videoId)`
Returns single video object (same structure as above).

#### `updateVideo(videoId, data)`
**Request**:
```javascript
PATCH /api/videos/{videoId}
{
  "title": "New Title",
  "description": "New description"
}
```

#### `deleteVideo(videoId)`
**Response**: `{ "success": true }`

---

### YouTube Upload API

#### `connectYouTube()`
**Response**:
```javascript
{
  "oauth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```
**Action**: Redirect user to this URL for OAuth.

#### `getYouTubeStatus()`
**Response**:
```javascript
{
  "connected": true | false,
  "channel_name": "My Channel",  // if connected
  "channel_id": "UC..."          // if connected
}
```

#### `uploadToYouTube(videoId, title, description, tags)`
**Request**:
```javascript
POST /api/upload/youtube
{
  "video_id": "uuid-here",
  "title": "Custom Title",       // Optional override
  "description": "Custom desc",  // Optional override
  "tags": ["tag1", "tag2"]       // Optional override
}
```

**Response**:
```javascript
{
  "success": true,
  "youtube_id": "dQw4w9WgXcQ",
  "youtube_url": "https://youtube.com/shorts/dQw4w9WgXcQ"
}
```

---

### Analytics API

#### `getAnalyticsSummary()`
**Response**:
```javascript
{
  "total_videos": 15,
  "total_views": 125000,
  "avg_score": 72.5,
  "best_hook_style": "question",
  "recent_videos": [...],  // Array of Video objects
  "improvement_tip": "Videos with question hooks performed 2x better"
}
```

---

### Utility APIs

#### `getRendererStatus()`
**Response**:
```javascript
{
  "pycaps_available": true,
  "moviepy_available": true,
  "active_renderer": "pycaps"
}
```

#### `healthCheck()`
**Response**:
```javascript
{
  "status": "healthy",
  "version": "2.0.0"
}
```

---

## 🔐 Authentication Flow

### Login Flow
```
User clicks "Sign in with Google"
         │
         ▼
signInWithGoogle()  →  Supabase OAuth popup
         │
         ▼
Callback to app  →  supabase.auth.onAuthStateChange()
         │
         ▼
App.jsx sets user state  →  Redirect to Dashboard
```

### Protected Routes
```javascript
// In App.jsx
<Route 
  path="/" 
  element={user ? <Dashboard /> : <Navigate to="/login" />} 
/>
```

### User Object Shape
```javascript
user = {
  id: "uuid",
  email: "user@gmail.com",
  user_metadata: {
    full_name: "John Doe",
    avatar_url: "https://..."
  }
}
```

### Sign Out
```javascript
import { signOut } from '../services/supabase'

const handleSignOut = async () => {
  await signOut()
  // User state automatically clears via onAuthStateChange
}
```

---

## 📄 Page Requirements

### Login Page (`/login`)

**Required Elements**:
- Google sign-in button
- Calls `signInWithGoogle()` on click
- Shows loading state during auth
- Redirects to `/` when `user` exists

**Example**:
```jsx
import { signInWithGoogle } from '../services/supabase'

function Login() {
  const handleLogin = async () => {
    await signInWithGoogle()
  }
  
  return (
    <button onClick={handleLogin}>
      Sign in with Google
    </button>
  )
}
```

---

### Dashboard Page (`/`)

**Required Sections**:

#### 1. Mode Selector
```jsx
// Three modes: creator, game, niche
<button onClick={() => setMode('creator')}>By Creator</button>
<button onClick={() => setMode('game')}>By Game</button>
<button onClick={() => setMode('niche')}>By Niche</button>
```

#### 2. Search Controls
```jsx
// Show dropdown based on mode
{mode === 'creator' && (
  <select value={selectedCreator} onChange={...}>
    <optgroup label="Tier 1">
      {creators.tier1.map(c => <option key={c}>{c}</option>)}
    </optgroup>
    {/* ... tier2, tier3 */}
  </select>
)}

{mode === 'game' && (
  <select value={selectedGame} onChange={...}>
    {Object.keys(games).map(g => <option key={g}>{g}</option>)}
  </select>
)}

// Find Clip button
<button onClick={handleDiscover}>Find Best Clip</button>
```

#### 3. Clip Preview
```jsx
{clip && (
  <div>
    <img src={clip.thumbnail_url} />
    {/* Play button - opens Twitch URL */}
    <button onClick={() => window.open(clip.url, '_blank')}>▶</button>
    <p>{clip.title}</p>
    <p>{clip.view_count.toLocaleString()} views</p>
    <p>{clip.duration}s</p>
  </div>
)}
```

#### 4. Generation Controls
```jsx
// Caption style selector
<select value={captionStyle} onChange={...}>
  {Object.entries(CAPTION_STYLES).map(([key, style]) => (
    <option key={key} value={key}>
      {style.emoji} {style.name}
    </option>
  ))}
</select>

// Generate button
<button onClick={handleGenerate} disabled={!clip || generating}>
  Generate Video
</button>

// Progress bar
{generating && (
  <div>
    <div style={{ width: `${progress.progress}%` }} />
    <p>{progress.message}</p>
  </div>
)}
```

#### 5. YouTube Connection Status
```jsx
{!youtubeConnected ? (
  <button onClick={handleConnectYouTube}>
    Connect YouTube
  </button>
) : (
  <span>✅ YouTube Connected</span>
)}
```

---

### Preview Page (`/preview/:id`)

**Required Elements**:

#### 1. Video Player
```jsx
// Video served from backend
<video 
  src={`${API_URL}/output/${video.local_path.split('/').pop()}`}
  controls
/>
```

#### 2. Metadata Editor
```jsx
<input 
  value={title} 
  onChange={(e) => setTitle(e.target.value)}
  placeholder="Video title"
/>

<textarea
  value={description}
  onChange={(e) => setDescription(e.target.value)}
  placeholder="Video description"
/>

<div>Tags: {video.tags.join(', ')}</div>
```

#### 3. Action Buttons
```jsx
<button onClick={handleUpload} disabled={!youtubeConnected}>
  Upload to YouTube
</button>

<button onClick={handleDiscard}>
  Discard
</button>

<button onClick={() => navigate('/')}>
  Back
</button>
```

---

### Analytics Page (`/analytics`)

**Required Elements**:

#### 1. Summary Cards
```jsx
<div>Total Videos: {summary.total_videos}</div>
<div>Total Views: {summary.total_views.toLocaleString()}</div>
<div>Avg Score: {summary.avg_score.toFixed(1)}</div>
```

#### 2. Video Table
```jsx
<table>
  <thead>
    <tr>
      <th>Title</th>
      <th>Views</th>
      <th>CTR</th>
      <th>Watch Time</th>
      <th>Score</th>
    </tr>
  </thead>
  <tbody>
    {summary.recent_videos.map(video => (
      <tr key={video.id}>
        <td>{video.title}</td>
        <td>{video.views}</td>
        <td>{video.ctr}%</td>
        <td>{video.watch_time_pct}%</td>
        <td>{video.score}</td>
      </tr>
    ))}
  </tbody>
</table>
```

#### 3. AI Feedback
```jsx
{summary.improvement_tip && (
  <div>💡 {summary.improvement_tip}</div>
)}
```

---

## 🔄 State Management Rules

### 1. User State
```jsx
// Comes from App.jsx as prop
function Dashboard({ user, youtubeConnected, onYouTubeConnect }) {
  // user.id, user.email, user.user_metadata.full_name
}
```

### 2. YouTube Connection State
```jsx
// Also from App.jsx
// null = still loading, true/false = known state
const youtubeConnected = ytConnectedProp === true
```

### 3. DO NOT Create New Instances
```jsx
// ❌ WRONG
import { createClient } from '@supabase/supabase-js'
const mySupabase = createClient(...)

// ✅ CORRECT
import { supabase } from '../services/supabase'
```

### 4. DO NOT Make Raw API Calls
```jsx
// ❌ WRONG
const res = await axios.post('/api/clips/discover', {...})

// ✅ CORRECT
import { discoverClip } from '../services/api'
const res = await discoverClip(mode, creator, game, niche)
```

---

## 🎨 Current Styling System

### CSS Variables
```css
:root {
  --neon-pink: #ff2e97;
  --neon-blue: #00d4ff;
  --neon-green: #00ff88;
  --neon-purple: #a855f7;
}
```

### Utility Classes
```css
.glass-card     /* Glassmorphism card */
.neon-glow      /* Neon shadow effect */
.neon-text      /* Neon text shadow */
.btn-primary    /* Pink/purple gradient button */
.btn-secondary  /* Transparent button */
.input-genz     /* Styled input */
.select-genz    /* Styled dropdown */
.progress-bar   /* Progress bar container */
.progress-bar-fill  /* Progress bar fill */
.video-preview  /* 9:16 video container */
.spinner        /* Loading spinner */
.toast          /* Toast notification */
```

### Current Theme
- Background: Dark gradient (#0a0a0f → #1a1a2e)
- Cards: Glassmorphism with blur
- Accents: Neon pink, blue, green
- Font: Inter

---

## ✨ Design Freedom & Constraints

### ✅ You CAN Change

| Category | Examples |
|----------|----------|
| **Colors** | New color palette, dark/light mode |
| **Typography** | Fonts, sizes, weights |
| **Layout** | Grid, flexbox, spacing |
| **Animations** | Transitions, keyframes, libraries |
| **Components** | Split into smaller components |
| **Libraries** | Add shadcn, MUI, Chakra, Framer Motion |
| **Icons** | Replace lucide-react with other library |
| **Images** | Add logos, illustrations, backgrounds |

### ❌ You CANNOT Change

| Category | Reason |
|----------|--------|
| API endpoints | Backend expects exact paths |
| Request/response formats | Backend validates schemas |
| Route paths | OAuth callbacks use exact URLs |
| Auth flow | Supabase handles this |
| Progress polling logic | Backend sends specific format |

### ⚠️ Be Careful With

| Item | Notes |
|------|-------|
| `package.json` | Can add deps, don't remove existing |
| `vite.config.js` | Usually no changes needed |
| Environment variables | Must keep same names |

---

## ✅ Testing Checklist

After redesign, verify these work:

### Authentication
- [ ] Can click "Sign in with Google"
- [ ] OAuth popup opens
- [ ] Redirects to Dashboard after login
- [ ] User name/avatar shows in Navbar
- [ ] Can sign out

### Clip Discovery
- [ ] Can switch between Creator/Game/Niche modes
- [ ] Dropdowns populate with data
- [ ] "Find Clip" returns a clip
- [ ] Thumbnail displays
- [ ] Play button opens Twitch URL
- [ ] View count and duration show

### Video Generation
- [ ] Caption style dropdown works
- [ ] "Generate Video" starts generation
- [ ] Progress bar updates (0-100%)
- [ ] Status messages display
- [ ] Redirects to Preview when complete
- [ ] Error messages show on failure

### Preview & Upload
- [ ] Video player loads and plays
- [ ] Title and description are editable
- [ ] Tags display
- [ ] "Upload to YouTube" works (if connected)
- [ ] "Discard" deletes video
- [ ] "Back" returns to Dashboard

### YouTube Connection
- [ ] "Connect YouTube" redirects to Google
- [ ] Callback page handles success
- [ ] Status updates to "Connected"

### Analytics
- [ ] Summary cards show data
- [ ] Video table populates
- [ ] AI tip displays

---

## 🚀 Quick Start for Redesign

1. **Read this entire document first**
2. **Do NOT modify** `services/api.js` or `services/supabase.js`
3. **Start with** `styles/index.css` for global changes
4. **Then modify** pages one at a time
5. **Test each page** before moving to next
6. **Run through checklist** at the end

---

## 📞 API Quick Reference

```javascript
// Import all you need
import { 
  discoverClip, 
  generateVideo, 
  subscribeToProgress,
  getVideos,
  getVideo,
  updateVideo,
  deleteVideo,
  uploadToYouTube,
  connectYouTube,
  getYouTubeStatus,
  getAnalyticsSummary,
  getCreators,
  getGames,
  getNiches,
  getRendererStatus,
  CAPTION_STYLES
} from '../services/api'

import { 
  supabase,
  signInWithGoogle, 
  signOut, 
  getSession 
} from '../services/supabase'
```

---

**Good luck with the redesign! 🎨**
