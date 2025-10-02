# Deploy MVP - Quick Start

## ✅ MVP is Ready!

Your clean MVP is built and tested:
- **Backend**: `backend/mvp_main.py` (150 lines)
- **Frontend**: `frontend/src/app/page.tsx` (200 lines)
- **Total Code**: ~350 lines (down from thousands!)

## 🚀 Deploy in 10 Minutes

### 1. Backend → Railway

```bash
# Railway CLI (or use dashboard)
railway login
railway init
railway add

# Set environment variables in Railway dashboard:
OPENAI_API_KEY=sk-...
PORT=8000

# Deploy
git push
```

**Railway Config** (`railway.json`):
- Build: `pip install -r backend/requirements-mvp.txt`
- Start: `cd backend && python mvp_main.py`

### 2. Frontend → Vercel

```bash
# Vercel CLI (or use dashboard)
vercel login
vercel

# Set environment variable:
NEXT_PUBLIC_API_URL=https://your-app.railway.app
```

**Vercel Config** (`vercel.json`):
- Auto-detects Next.js
- Builds from `frontend/` directory

## 📋 Pre-Deploy Checklist

- [ ] Add credit to OpenAI account (API needs funding)
- [ ] Get OpenAI API key from https://platform.openai.com/api-keys
- [ ] Test locally: `python3 backend/mvp_main.py`
- [ ] Test frontend: `cd frontend && npm run dev`

## 🧪 Test Locally

**Backend:**
```bash
cd backend
pip3 install -r requirements-mvp.txt
echo "OPENAI_API_KEY=sk-..." > .env
python3 mvp_main.py

# Test
curl http://localhost:8000/
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev

# Visit http://localhost:3000
```

## 🔑 Environment Variables

### Backend (Railway)
```
OPENAI_API_KEY=sk-proj-...
PORT=8000
```

### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL=https://mlb-trade-api.railway.app
```

## 💰 Cost Estimate

- **OpenAI**: ~$0.02-0.05 per trade evaluation (GPT-4o)
- **Railway**: Free tier (500 hours/month)
- **Vercel**: Free tier (unlimited)

**Total**: Nearly free for MVP testing!

## 🧹 Optional: Clean Up Old Files

If you want to remove all the bloated old code:

```bash
./cleanup_bloat.sh
```

This removes:
- Old backend files (84 → 2 files)
- CrewAI agents/crews/tools
- Supabase configs
- Test/seed files
- Old documentation

**WARNING**: This is destructive. Commit current state first!

## 📁 Final MVP Structure

```
backend/
  mvp_main.py              # FastAPI server
  requirements-mvp.txt     # 5 dependencies

frontend/
  src/app/page.tsx         # Single page UI
  package.json

Procfile                   # Railway
railway.json              # Railway config
vercel.json               # Vercel config
README-MVP.md             # MVP docs
DEPLOY.md                 # This file
```

## 🐛 Troubleshooting

**OpenAI quota error?**
- Add billing to your OpenAI account
- Check API key is correct

**CORS error?**
- Update `allow_origins` in `mvp_main.py` to include your Vercel domain
- Add your Railway URL to allowed origins

**Import errors?**
- Run: `pip3 install -r backend/requirements-mvp.txt`

## ✨ What's Next?

After MVP is live, you can add:
1. User authentication
2. Save trade history
3. Real player stats from API
4. Better error handling
5. Rate limiting
6. Analytics

But first... **SHIP THE MVP!** 🚢
