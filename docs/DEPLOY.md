# Deploy

The API runs on Railway (or any Python host) and the web app on Vercel.

## API (Railway)

`railway.json` and `Procfile` start:

```
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
```

The root `requirements.txt` includes `backend/requirements.txt` so Nixpacks detects Python. The health check is `/api/health`.

Environment variables:

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ALLOWED_ORIGINS` | yes | `http://localhost:3000` | Comma-separated web origins allowed by CORS, for example your Vercel URL |
| `OPENAI_API_KEY` | no | — | Turns on AI narratives and natural-language parsing |
| `OPENAI_MODEL` | no | `gpt-4o` | Model used when AI is on |
| `AI_RATE_LIMIT_PER_MINUTE` | no | `10` | Per-IP limit on requests that call the model |
| `STATS_SEASON` / `PLAN_SEASON` | no | `2026` / `2027` | Seasons used for stats and planning |
| `DOLLARS_PER_WAR_M`, `CBT_THRESHOLD_M`, `LEAGUE_MIN_M` | no | `9.0`, `244`, `0.78` | Valuation assumptions ($M) |

`backend/data/players.json` is committed, so deploys don't need network access to MLB sources. Rerun the ingest and commit the result to refresh it.

## Web (Vercel)

- Root directory: `frontend`
- Environment: `NEXT_PUBLIC_API_URL=https://<your-api-host>`

Add the Vercel URL to the API's `ALLOWED_ORIGINS`.

## Checks before deploying

```bash
cd backend && python -m pytest && ruff check .
cd frontend && npm run type-check && npm run lint && npm test && npm run build
```

CI (`.github/workflows/ci.yml`) runs the same checks on every push and pull request.
