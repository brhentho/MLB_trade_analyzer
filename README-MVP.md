# MLB Trade Analyzer - MVP

A simple, AI-powered MLB trade evaluation tool using OpenAI GPT-4.

## What It Does

Evaluates baseball trades and provides:
- **Grade** (A-F)
- **Fairness Score** (0-100)
- **Analysis** for each team
- **Risks** to consider
- **Recommendation** (Accept/Reject/Negotiate)

## Tech Stack

**Backend:**
- FastAPI
- OpenAI GPT-4o
- Python 3.11+

**Frontend:**
- Next.js 14
- TypeScript
- Tailwind CSS

## Setup

### 1. Backend

```bash
cd backend
pip install -r requirements-mvp.txt

# Add your OpenAI key to .env
echo "OPENAI_API_KEY=your_key_here" > .env

# Run
python mvp_main.py
```

Backend runs on `http://localhost:8000`

### 2. Frontend

```bash
cd frontend
npm install

# Optional: Point to deployed backend
echo "NEXT_PUBLIC_API_URL=https://your-backend.railway.app" > .env.local

npm run dev
```

Frontend runs on `http://localhost:3000`

## Deploy

### Backend (Railway)
1. Create Railway project
2. Connect GitHub repo
3. Set build command: `pip install -r backend/requirements-mvp.txt`
4. Set start command: `cd backend && python mvp_main.py`
5. Add environment variable: `OPENAI_API_KEY`

### Frontend (Vercel)
1. Create Vercel project
2. Connect GitHub repo
3. Set root directory: `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL` (Railway backend URL)
5. Deploy

## Usage

1. Enter Team A and what they get
2. Enter Team B and what they get
3. (Optional) Add context about team needs
4. Click "Evaluate Trade"
5. Get AI-powered analysis

## Example

**Trade:**
- Yankees get: Juan Soto
- Padres get: Clarke Schmidt, Top Prospect

**AI Evaluates:**
- Grade: B+
- Fairness: 78/100
- Analysis per team
- Risks identified
- Recommendation provided

## Files

```
backend/
  mvp_main.py           # FastAPI server (150 lines)
  requirements-mvp.txt  # Dependencies

frontend/
  src/app/page.tsx      # Main UI (200 lines)

Procfile               # Railway deployment
railway.json           # Railway config
vercel.json           # Vercel config
```

## Cost

- OpenAI API: ~$0.01-0.05 per trade evaluation (GPT-4o)
- Railway: Free tier works
- Vercel: Free tier works

## What's NOT included (yet)

- Database
- User accounts
- Historical data
- Multiple agents
- Real player stats API
- Salary cap calculations

This is an MVP - one endpoint, one AI agent, clean and simple.
