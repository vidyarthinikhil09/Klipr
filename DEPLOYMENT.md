# 🚀 AutoShorts Deployment Guide

Complete guide to push to GitHub, set up secrets, and enable automated video generation.

---

## Step 1: Push to GitHub

### 1.1 Create a New GitHub Repository
1. Go to [github.com/new](https://github.com/new)
2. Name it `autoshorts` (or whatever you prefer)
3. Make it **Private** (contains API keys references)
4. Don't initialize with README (we already have one)

### 1.2 Initialize Git & Push
```bash
cd "C:\Users\vidya\Desktop\Shorts Automation"

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: AutoShorts Twitch Commentary Bot"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/autoshorts.git

# Push
git branch -M main
git push -u origin main
```

---

## Step 2: Set Up GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets (copy values from your `backend/.env`):

| Secret Name | Value |
|-------------|-------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `TWITCH_CLIENT_ID` | From dev.twitch.tv |
| `TWITCH_CLIENT_SECRET` | From dev.twitch.tv |
| `OPENROUTER_API_KEY` | From openrouter.ai |
| `PEXELS_API_KEY` | From pexels.com/api |
| `YOUTUBE_CLIENT_ID` | From Google Cloud Console |
| `YOUTUBE_CLIENT_SECRET` | From Google Cloud Console |

---

## Step 3: Test GitHub Actions

### 3.1 Manual Trigger
1. Go to your repo → **Actions** tab
2. Click **AutoShorts Daily Run** workflow
3. Click **Run workflow** → **Run workflow**
4. Watch the logs to ensure everything works

### 3.2 Check Cron Schedule
The workflow runs daily at **10:00 AM UTC** by default.

To change the schedule, edit `.github/workflows/daily_run.yml`:
```yaml
schedule:
  - cron: '0 14 * * *'  # 2:00 PM UTC = 7:30 PM IST
```

[Cron Generator](https://crontab.guru/) to help with timing.

---

## Step 4: Deployment Options

### Option A: Run Locally (Recommended for Manual Control)
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```
Access at: `http://localhost:5173`

### Option B: Deploy to Cloud (For 24/7 Access)

#### Backend → Railway/Render/Fly.io
```bash
# Example: Railway
railway login
railway init
railway up
```

#### Frontend → Vercel/Netlify
```bash
# Example: Vercel
cd frontend
npm i -g vercel
vercel
```

#### Environment Variables
Set these in your cloud provider's dashboard (same as GitHub secrets).

---

## Step 5: Enable Full Automation (Optional)

By default, GitHub Actions only **tests** the pipeline. To enable fully automated video generation:

### 5.1 Edit the Workflow
In `.github/workflows/daily_run.yml`, uncomment the "AUTOMATED VIDEO GENERATION" section.

### 5.2 Store YouTube OAuth Token
Since OAuth requires browser login, you need to:

1. Run locally once to generate the token
2. Encode it: `base64 data/youtube_tokens.json > token.txt`
3. Add as GitHub secret: `YOUTUBE_TOKEN_BASE64`

### 5.3 Enable Auto-Upload
Add this secret:
- `AUTO_UPLOAD=true`

⚠️ **Warning**: Full automation uploads without human review. Recommended to keep manual approval.

---

## Quick Reference

### Local Development
```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

### Git Commands
```bash
# Save changes
git add .
git commit -m "Your message"
git push

# Pull latest
git pull
```

### Check Logs
- **GitHub Actions**: Repo → Actions → Click workflow run
- **Local Backend**: Check terminal running uvicorn
- **Supabase**: Dashboard → Database → Logs

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub Action fails | Check secrets are set correctly |
| OpenRouter 404 | Models change - update `metadata_generator.py` |
| YouTube upload fails | Re-authenticate OAuth in dashboard |
| Video not portrait | Check `renderer.py` resize function |
| Captions too big | Adjust font sizes in CSS templates |

---

## File Structure Reminder
```
autoshorts/
├── .github/workflows/daily_run.yml  # GitHub Actions
├── backend/
│   ├── .env                         # API keys (DO NOT COMMIT)
│   ├── app/
│   │   ├── api/                     # FastAPI routes
│   │   ├── services/                # Core logic
│   │   └── main.py                  # Entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                   # React pages
│   │   └── services/                # API client
│   └── package.json
├── temp/                            # Downloaded clips
├── output/                          # Generated videos
└── data/                            # Tokens & history
```

---

## Done! 🎉

Your AutoShorts bot is ready for:
- ✅ Manual video generation via dashboard
- ✅ Daily automated tests via GitHub Actions
- ✅ Optional full automation (uncomment in workflow)

Questions? Check the README.md or open an issue on GitHub.
