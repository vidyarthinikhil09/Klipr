import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, Upload, Trash2, Edit3, Save, X,
  Youtube, Eye, Clock, Tag, RefreshCw
} from 'lucide-react'
import { getVideo, uploadToYouTube, deleteVideo, updateVideo } from '../services/api'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function Preview({ user }) {
  const { id } = useParams()
  const navigate = useNavigate()
  const [video, setVideo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editData, setEditData] = useState({ title: '', description: '', tags: '' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    loadVideo()
  }, [id])

  const loadVideo = async () => {
    try {
      const data = await getVideo(id)
      setVideo(data)
      setEditData({
        title: data.title || '',
        description: data.description || '',
        tags: (data.tags || []).join(', ')
      })
    } catch (err) {
      setError('Failed to load video')
    } finally {
      setLoading(false)
    }
  }

  // Get video URL - extract filename from path
  const getVideoUrl = () => {
    if (!video?.local_path) return ''
    const filename = video.local_path.split(/[/\\]/).pop()
    // Use the backend server to serve the video file
    return `${API_BASE.replace('/api', '')}/videos/${filename}`
  }

  const handleUpload = async () => {
    setUploading(true)
    setError('')

    try {
      const tags = editData.tags.split(',').map(t => t.trim()).filter(Boolean)
      const result = await uploadToYouTube(
        id,
        editData.title,
        editData.description,
        tags
      )

      if (result.success) {
        setSuccess(`Uploaded! ${result.youtube_url}`)
        setVideo({ ...video, status: 'uploaded', youtube_id: result.youtube_id })
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this video?')) return

    try {
      console.log('[Preview] Deleting video:', id)
      const result = await deleteVideo(id)
      console.log('[Preview] Delete result:', result)
      navigate('/')
    } catch (err) {
      console.error('[Preview] Delete error:', err)
      // If 404, video is already gone - treat as success
      if (err.response?.status === 404) {
        console.log('[Preview] Video already deleted, navigating home')
        navigate('/')
        return
      }
      setError(err.response?.data?.detail || 'Failed to delete video')
    }
  }

  const handleSave = () => {
    // Save locally - update displayed video with edited values
    const tags = editData.tags.split(',').map(t => t.trim()).filter(Boolean)
    setVideo({
      ...video,
      title: editData.title,
      description: editData.description,
      tags: tags
    })
    setEditing(false)
    setSuccess('Changes saved locally. Click "Upload" to publish.')
    setTimeout(() => setSuccess(''), 3000)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner" />
      </div>
    )
  }

  if (!video) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="glass-card p-8 text-center">
          <p className="text-gray-400">Video not found</p>
          <button onClick={() => navigate('/')} className="btn-primary mt-4">
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Back Button */}
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft size={20} />
        Back to Dashboard
      </button>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Preview & Upload</h1>
          <p className="text-gray-400">Review your video before publishing</p>
        </div>
        
        {video.status === 'uploaded' && (
          <a
            href={`https://youtube.com/shorts/${video.youtube_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 bg-red-600 rounded-xl mt-4 md:mt-0"
          >
            <Youtube size={20} />
            View on YouTube
          </a>
        )}
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="glass-card p-4 mb-6 border border-red-500/50 bg-red-500/10 text-red-400">
          {error}
        </div>
      )}
      {success && (
        <div className="glass-card p-4 mb-6 border border-green-500/50 bg-green-500/10 text-green-400">
          {success}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-8">
        {/* Video Player */}
        <div className="glass-card p-4">
          <div className="video-preview mx-auto">
            <video
              src={getVideoUrl()}
              controls
              className="w-full h-full object-contain"
              onError={(e) => console.error('Video load error:', e)}
            />
          </div>
          
          <div className="flex justify-center gap-2 mt-4">
            <span className="stats-badge flex items-center gap-1">
              <Clock size={14} />
              {video.hook_style || 'N/A'} hook
            </span>
            <span className="stats-badge">
              {video.creator}
            </span>
          </div>
        </div>

        {/* Metadata Form */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">Video Details</h2>
            {!editing && video.status !== 'uploaded' && (
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-2 text-neon-blue hover:underline"
              >
                <Edit3 size={16} />
                Edit
              </button>
            )}
          </div>

          {/* Title */}
          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-2">Title</label>
            {editing ? (
              <input
                type="text"
                value={editData.title}
                onChange={(e) => setEditData({ ...editData, title: e.target.value })}
                className="input-genz"
                maxLength={100}
              />
            ) : (
              <p className="text-lg font-medium">{video.title}</p>
            )}
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-2">Description</label>
            {editing ? (
              <textarea
                value={editData.description}
                onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                className="input-genz h-32 resize-none"
                maxLength={500}
              />
            ) : (
              <p className="text-gray-300 whitespace-pre-wrap">{video.description}</p>
            )}
          </div>

          {/* Tags */}
          <div className="mb-6">
            <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
              <Tag size={14} />
              Tags
            </label>
            {editing ? (
              <input
                type="text"
                value={editData.tags}
                onChange={(e) => setEditData({ ...editData, tags: e.target.value })}
                className="input-genz"
                placeholder="gaming, twitch, clips (comma-separated)"
              />
            ) : (
              <div className="flex flex-wrap gap-2">
                {(video.tags || []).map((tag, i) => (
                  <span key={i} className="px-2 py-1 bg-white/10 rounded-lg text-sm">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Edit Buttons */}
          {editing && (
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => {
                  setEditing(false)
                  // Reset to original values
                  setEditData({
                    title: video.title || '',
                    description: video.description || '',
                    tags: (video.tags || []).join(', ')
                  })
                }}
                className="btn-secondary flex-1 flex items-center justify-center gap-2"
              >
                <X size={18} />
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="btn-primary flex-1 flex items-center justify-center gap-2"
              >
                <Save size={18} />
                Save Changes
              </button>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            {video.status !== 'uploaded' ? (
              <>
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="animate-spin" size={18} />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload size={18} />
                      Upload to YouTube
                    </>
                  )}
                </button>
                <button
                  onClick={handleDelete}
                  className="btn-secondary flex items-center justify-center gap-2 px-4"
                >
                  <Trash2 size={18} />
                </button>
              </>
            ) : (
              <div className="w-full text-center py-4 bg-green-500/10 rounded-xl border border-green-500/30">
                <span className="text-green-400 flex items-center justify-center gap-2">
                  <Youtube size={20} />
                  Video uploaded successfully!
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Preview
