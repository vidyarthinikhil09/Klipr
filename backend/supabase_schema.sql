-- =============================================
-- AutoShorts v2 - Supabase Database Schema
-- Run this in Supabase SQL Editor
-- =============================================

-- YouTube OAuth Tokens (per user)
CREATE TABLE IF NOT EXISTS youtube_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Generated Videos
CREATE TABLE IF NOT EXISTS videos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    youtube_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT[],
    creator TEXT,
    clip_url TEXT,
    clip_id TEXT,
    hook_style TEXT,
    model_used TEXT,
    local_path TEXT,
    thumbnail_url TEXT,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    watch_time_pct REAL DEFAULT 0,
    ctr REAL DEFAULT 0,
    subs_gained INTEGER DEFAULT 0,
    score REAL DEFAULT 0,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Used Clips (prevent duplicates)
CREATE TABLE IF NOT EXISTS used_clips (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    clip_id TEXT NOT NULL,
    clip_url TEXT,
    creator TEXT,
    used_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, clip_id)
);

-- Analytics History (for tracking over time)
CREATE TABLE IF NOT EXISTS analytics_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    watch_time_pct REAL DEFAULT 0,
    ctr REAL DEFAULT 0,
    score REAL DEFAULT 0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Metadata Styles Performance (for self-learning)
CREATE TABLE IF NOT EXISTS metadata_styles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    hook_style TEXT NOT NULL,
    uses INTEGER DEFAULT 0,
    total_score REAL DEFAULT 0,
    avg_score REAL DEFAULT 0,
    best_score REAL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, hook_style)
);

-- Enable Row Level Security (RLS)
ALTER TABLE youtube_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE used_clips ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE metadata_styles ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own data
CREATE POLICY "Users can view own youtube_tokens" ON youtube_tokens
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own videos" ON videos
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own used_clips" ON used_clips
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own analytics_history" ON analytics_history
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own metadata_styles" ON metadata_styles
    FOR ALL USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_used_clips_user_id ON used_clips(user_id);
CREATE INDEX IF NOT EXISTS idx_used_clips_clip_id ON used_clips(clip_id);
CREATE INDEX IF NOT EXISTS idx_analytics_video_id ON analytics_history(video_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_youtube_tokens_updated_at
    BEFORE UPDATE ON youtube_tokens
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_videos_updated_at
    BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
