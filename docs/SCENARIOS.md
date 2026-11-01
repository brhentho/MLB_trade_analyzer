# Key scenarios and endpoints

Every treatment in `/lab/*` has to cover these. The API keeps all numbers deterministic. The optional LLM only writes prose and parses search text into validated filters.

## Scenarios

| # | Scenario | User moment | Must see first | Endpoints |
|---|---|---|---|---|
| S1 | Take over a team | "I'm the GM of the Mariners. What do I have?" | Payroll against the tax line, holes by position, expiring deals | `GET /api/teams`, `GET /api/teams/{abbrev}/roster` |
| S2 | Find a niche player | "Lefty reliever, elite chase rate, ≤$6M, 2+ years of control" | Ranked matches and why each one matched | `POST /api/players/search/natural`, `POST /api/players/search`, `GET /api/archetypes` |
| S3 | Find a cheaper comp | "Who plays like Isaac Paredes but cheaper?" | Nearest skill shapes with salary and control deltas | `GET /api/players/{id}/similar`, `POST /api/players/shape` |
| S4 | Build the perfect team | Swap real players into a roster | Payroll room, projected sWAR, uncovered positions | `POST /api/rosters/evaluate` |
| S5 | Grade a trade | Pick players from two real rosters | Surplus balance, payroll change by season, a plain-language verdict | `POST /api/trades/evaluate` |
| S6 | Compare players | Two to four players side by side | Overlaid skill shapes, contract runway | `GET /api/players/{id}` (fingerprint overlay in the UI) |

## Endpoints

| Method and path | Notes |
|---|---|
| `GET /api/health` | Player count, and whether AI is available |
| `GET /api/meta` | Seasons, league constants, assumptions, rating labels |
| `GET /api/teams` | Teams with payroll by season and team sWAR |
| `GET /api/teams/{abbrev}/roster` | 40-man players and an evaluation: depth chart, needs, payroll, active-26 sWAR |
| `GET /api/players?group=&team=&mapped=` | Compact player list (used by the skill map) |
| `GET /api/players/{id}` | Full player: ratings, percentiles, stats, contract by year, projection |
| `GET /api/players/{id}/similar?limit=&salary_max=&control_min_years=` | Nearest rating shapes, same group and role |
| `POST /api/players/search` | Structured filters (see `SearchFilters` in `backend/app/schemas.py`). Every result includes `reasons` |
| `POST /api/players/search/natural` | Text in; filters, notes and results out. Uses the LLM when configured, otherwise a deterministic parser. Rate limited when AI is used |
| `POST /api/players/shape` | "Draw the shape": nearest players to a rating profile |
| `GET /api/archetypes` | Archetype definitions and counts |
| `POST /api/rosters/evaluate` | Any set of player ids in; depth chart, needs, payroll and sWAR out |
| `POST /api/trades/evaluate` | Player ids for each side in. Returns grade, fairness, winner, surplus by side, payroll delta and narrative (`narrative_source`: `ai` or `rules`) |
| `POST /api/evaluate` | Deprecated free-text endpoint kept for compatibility. Names are resolved against the database |

## Ways of showing the data (implemented as shared components)

| Component | Idea |
|---|---|
| `RatingBar`, `RatingCell` | 20–80 scouting bars and heat cells. The real value is in the tooltip |
| `Fingerprint` | Radial skill shape. Comparisons overlay a dashed second shape |
| `ControlPips` | Seasons of control. Filled pips are guaranteed; outlined pips are estimated or arbitration |
| `PayrollLedger` | Salary by season, stacked by player, with the tax line |
| `BargainField` | Projected sWAR against salary, with a market-rate diagonal |
| `Constellation` | 2D skill map with archetype labels and lasso selection |
| `TradeBalance` | Beam that tilts toward the side receiving more surplus |
| `Diamond` | Field diagram with interactive slots for a depth chart |
