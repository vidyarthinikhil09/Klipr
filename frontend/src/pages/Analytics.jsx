import { useState, useEffect } from 'react'
import { 
  RefreshCw, TrendingUp, Eye, ThumbsUp, 
  Sparkles, BarChart3, Lightbulb
} from 'lucide-react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts'
import { getAnalyticsSummary, refreshAnalytics, getAIFeedback } from '../services/api'

function Analytics({ user }) {
  const [summary, setSummary] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [summaryData, feedbackData] = await Promise.all([
        getAnalyticsSummary(),
        getAIFeedback()
      ])
      setSummary(summaryData)
      setFeedback(feedbackData)
    } catch (err) {
      console.error('Failed to load analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await refreshAnalytics()
      await loadData()
    } catch (err) {
      console.error('Refresh failed:', err)
    } finally {
      setRefreshing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="spinner" />
      </div>
    )
  }

  // Prepare chart data
  const chartData = (summary?.recent_videos || [])
    .slice()
    .reverse()
    .map((v, i) => ({
      name: `#${i + 1}`,
      views: v.views || 0,
      score: v.score || 0,
    }))

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
            <BarChart3 className="text-neon-blue" />
            Analytics Dashboard
          </h1>
          <p className="text-gray-400">Track performance & AI self-improvement</p>
        </div>
        
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn-secondary flex items-center gap-2 mt-4 md:mt-0"
        >
          <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} />
          Refresh Data
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-neon-pink/20 flex items-center justify-center">
              <TrendingUp className="text-neon-pink" size={20} />
            </div>
            <span className="text-gray-400 text-sm">Total Videos</span>
          </div>
          <p className="text-3xl font-bold">{summary?.total_videos || 0}</p>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-neon-blue/20 flex items-center justify-center">
              <Eye className="text-neon-blue" size={20} />
            </div>
            <span className="text-gray-400 text-sm">Total Views</span>
          </div>
          <p className="text-3xl font-bold">{(summary?.total_views || 0).toLocaleString()}</p>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-neon-green/20 flex items-center justify-center">
              <ThumbsUp className="text-neon-green" size={20} />
            </div>
            <span className="text-gray-400 text-sm">Avg Score</span>
          </div>
          <p className="text-3xl font-bold">{summary?.avg_score?.toFixed(1) || '0.0'}</p>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-neon-purple/20 flex items-center justify-center">
              <Sparkles className="text-neon-purple" size={20} />
            </div>
            <span className="text-gray-400 text-sm">Best Hook</span>
          </div>
          <p className="text-xl font-bold capitalize">{summary?.best_hook_style || 'N/A'}</p>
        </div>
      </div>

      {/* AI Insights */}
      {feedback?.has_feedback && (
        <div className="glass-card p-6 mb-8 border border-neon-purple/30">
          <div className="flex items-center gap-3 mb-4">
            <Lightbulb className="text-neon-purple" size={24} />
            <h2 className="text-xl font-bold">AI Self-Improvement Insights</h2>
          </div>
          <p className="text-gray-300 leading-relaxed">{feedback.feedback}</p>
          <p className="text-sm text-gray-500 mt-4">
            💡 This feedback is automatically injected into AI prompts for better results
          </p>
        </div>
      )}

      {/* Chart */}
      {chartData.length > 0 && (
        <div className="glass-card p-6 mb-8">
          <h2 className="text-xl font-bold mb-6">Performance Trend</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="name" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip 
                  contentStyle={{ 
                    background: 'rgba(20,20,30,0.95)', 
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="views" 
                  stroke="#00d4ff" 
                  fillOpacity={1} 
                  fill="url(#colorViews)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Videos Table */}
      {summary?.recent_videos?.length > 0 && (
        <div className="glass-card overflow-hidden">
          <div className="p-6 border-b border-white/10">
            <h2 className="text-xl font-bold">Recent Videos</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-white/5">
                  <th className="text-left p-4 text-gray-400 font-medium">Title</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Creator</th>
                  <th className="text-left p-4 text-gray-400 font-medium">Hook</th>
                  <th className="text-right p-4 text-gray-400 font-medium">Views</th>
                  <th className="text-right p-4 text-gray-400 font-medium">Score</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_videos.map((video, i) => (
                  <tr key={video.id || i} className="border-t border-white/5 hover:bg-white/5">
                    <td className="p-4">
                      <span className="font-medium">
                        {video.title?.substring(0, 40)}
                        {video.title?.length > 40 ? '...' : ''}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-1 bg-white/10 rounded-lg text-sm">
                        {video.creator}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-1 bg-neon-purple/20 text-neon-purple rounded-lg text-sm capitalize">
                        {video.hook_style || 'N/A'}
                      </span>
                    </td>
                    <td className="p-4 text-right font-mono">
                      {(video.views || 0).toLocaleString()}
                    </td>
                    <td className="p-4 text-right">
                      <span className={`px-2 py-1 rounded-lg text-sm font-semibold
                        ${video.score > 50 ? 'bg-green-500/20 text-green-400' : 
                          video.score > 25 ? 'bg-yellow-500/20 text-yellow-400' : 
                          'bg-red-500/20 text-red-400'}`}
                      >
                        {video.score?.toFixed(0) || '0'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!summary?.recent_videos || summary.recent_videos.length === 0) && (
        <div className="glass-card p-12 text-center">
          <div className="text-6xl mb-4">📊</div>
          <h3 className="text-xl font-bold mb-2">No Data Yet</h3>
          <p className="text-gray-400">Generate and upload videos to see analytics here</p>
        </div>
      )}
    </div>
  )
}

export default Analytics
