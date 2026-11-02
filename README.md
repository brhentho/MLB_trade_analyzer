# StatSlugger

Run a real MLB front office. StatSlugger works like *Out of the Park Baseball*, but every player is real: 2026 Statcast and MLB stats, real contracts where they're published, and clearly labeled estimates where they aren't. You can scout for players who fit a niche, build a roster under a budget, and grade trades.

![StatSlugger logo](frontend/public/brand/logo.png)

## What you can do

| Scenario | What it answers |
|---|---|
| Take over a team | What do I have, what do I owe each season, and where are the holes? |
| Find a niche player | "Lefty reliever, elite chase rate, under $6M, 2+ years of control." |
| Find a cheaper comp | Who plays like this player but costs less or is younger? |
| Build the perfect team | Pick real players and watch the depth chart, payroll and sWAR update. |
| Grade a trade | Surplus value, payroll change by season, years of control, and a plain-language read. |

See [docs/SCENARIOS.md](docs/SCENARIOS.md) for how each scenario maps to endpoints and UI.

## Three visual treatments

All three are built on the same API and data, so you can compare them on the same tasks:

- **`/lab/front-office`: front office terminal.** Dense, sortable OOTP-style grids, a payroll ledger, and a player drawer.
- **`/lab/scouting-report`: scouting report.** Players as cards with a 20–80 scouting sheet on the back, kept in a binder. Trades are card swaps.
- **`/lab/war-room`: diamond war room.** The roster lives on a diamond. You find players on a skill map, or by drawing the shape you want, then drop them into a position.

## Quick start

Requires Python 3.11+ and Node 20+.

```bash
# API (http://localhost:8000)
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements-dev.txt   # macOS/Linux: .venv/bin/pip
cp backend/.env.example backend/.env                        # OPENAI_API_KEY is optional
python backend/main.py

# Web (http://localhost:3000)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The repo ships with a generated `backend/data/players.json`, so the app works immediately. To refresh it from live sources:

```bash
python backend/scripts/ingest.py           # downloads, caches raw files in backend/data/raw/
python backend/scripts/ingest.py --cache   # rebuild from the cache only
```

## How it works

```
MLB Stats API ─┐
Baseball Savant ┼─> scripts/ingest.py ─> data/players.json ─> FastAPI (app/) ─> Next.js (frontend/)
contracts.csv ─┘     ratings, sWAR,          in-memory store      search, roster,      three /lab treatments
                     surplus, archetypes                          trade math, AI text
```

- **Ratings (20–80).** Statcast percentiles are mapped onto the scouting scale, where 50 is average and every 10 points is one standard deviation. Hitters get Contact, Power, Eye, Speed, Glove and Arm. Pitchers get Stuff, Weak contact, Control, Velocity and Stamina.
- **sWAR.** StatSlugger's own WAR estimate. For hitters it combines wOBA/xwOBA batting runs with positional and fielding adjustments. For pitchers it's FIP-based. It's labeled as an estimate everywhere.
- **Surplus value.** Projected sWAR × $/WAR minus salary, summed over the years of control. The $/WAR figure is configurable.
- **AI is optional.** Every number is computed in code. When `OPENAI_API_KEY` is set, the model writes the trade narrative and turns plain-language searches into filters, which are validated before they're used. Without a key, a rules-based parser and template narrative take over, and the UI shows which one is in use.

Details and caveats: [docs/DATA.md](docs/DATA.md).

## Repository layout

```
backend/
  app/            FastAPI app: config, store, model (math), search, roster, llm, narrative
  scripts/        ingest.py
  data/           contracts.csv (curated), players.json (generated)
  tests/          pytest
  main.py         local entrypoint
frontend/
  src/app/        home + /lab/{front-office,scouting-report,war-room}
  src/components/ shared UI + viz (RatingBar, Fingerprint, ControlPips, PayrollLedger,
                  BargainField, Constellation, TradeBalance, Diamond)
  src/lib/        API client, types, formatting
docs/             DEPLOY, DATA, SCENARIOS
```

## Development

```bash
# backend
cd backend && ../.venv/Scripts/python -m pytest && ../.venv/Scripts/ruff check .
# frontend
cd frontend && npm run type-check && npm run lint && npm test && npm run build
```

Deployment: [docs/DEPLOY.md](docs/DEPLOY.md).

## License

MIT. Data sources have their own terms; see [docs/DATA.md](docs/DATA.md).
