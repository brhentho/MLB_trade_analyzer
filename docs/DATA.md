# Data: sources, model and caveats

## Sources

| Data | Source | How |
|---|---|---|
| Teams, 40-man rosters, bio, season stats | [MLB Stats API](https://statsapi.mlb.com) | `teams`, `teams/{id}/roster?rosterType=40Man` with hydrated season stats |
| Percentile rankings (batters, pitchers) | [Baseball Savant](https://baseballsavant.mlb.com/leaderboard/percentile-rankings) | CSV export |
| Expected stats (wOBA, xwOBA, PA) | [Baseball Savant](https://baseballsavant.mlb.com/leaderboard/expected_statistics) | CSV export |
| Guaranteed contracts | `backend/data/contracts.csv`, curated by hand | Reference: [Cot's Baseball Contracts](https://legacy.baseballprospectus.com/compensation/cots/) |

**Terms of use.** MLB Stats API and Baseball Savant data are made available for personal, non-commercial use. Before any public or commercial launch, get a data license (for example from MLB Advanced Media or a commercial provider such as SportsDataIO or Sportradar). Contract data isn't scraped. The curated file records totals from public reporting and should be checked before you rely on it.

## Seasons

- `STATS_SEASON` (default 2026): the stats behind ratings and sWAR.
- `PLAN_SEASON` (default 2027): the season you're building for. Salaries, control and payroll start here.

## Ratings (20–80)

Each rating averages one or more Savant percentiles, which are already oriented so that higher is better. The result is converted with `50 + 10·z`, where `z` is the normal quantile of the percentile, and clamped to 20–80. So the 50th percentile is 50, the 84th is 60, and the 98th is about 70.

| Rating | Inputs |
|---|---|
| Contact | K%, Whiff%, xBA, Squared-up% |
| Power | xSLG, Barrel%, Max EV, Hard-hit%, Bat speed |
| Eye | BB%, Chase% |
| Speed | Sprint speed |
| Glove | OAA (not available for catchers) |
| Arm | Arm strength |
| Stuff | Whiff%, K%, Chase% |
| Weak contact | Barrel%, Hard-hit%, Avg EV, xSLG allowed |
| Control | BB% |
| Velocity | Fastball velocity |
| Stamina | Innings per game (derived, not a percentile) |

Savant only publishes percentiles for players above a playing-time minimum. Players below it show "—" for those ratings.

**OVR and POT.** OVR is the percentile of a player's sample-shrunk sWAR rate within his group (hitters, SP or RP), mapped to 20–80. POT adds an age bonus for young players, and a larger one when the sample is small.

## sWAR (StatSlugger WAR estimate)

- **Hitters.** Batting runs come from `(wOBA − lgwOBA) / 1.2 × PA`, using a 50/50 blend of wOBA and xwOBA. Then add a replacement credit of 20 runs per 600 PA, a positional adjustment, and a fielding proxy based on the Glove rating. Divide the total by 10 runs per win.
- **Pitchers.** FIP uses a league constant computed from the ingested pitchers. Runs above replacement are `((lgERA + gap) − FIP) / 9 × IP`, where the gap is 1.0 for starters and 0.6 for relievers. Divide by 10.
- **Projection.** Last season is regressed toward a fringe baseline, weighted by sample size. Each year then gets an aging step: +0.3 at 25 and under, 0 from 26–29, about −0.3 from 30–32, and −0.5 at 33+.

These are transparent approximations, not FanGraphs or Baseball-Reference WAR.

**Team totals** count only the best 26 by depth chart: 9 starters, 4 bench, 5 SP and 8 RP, not the whole 40-man.

## Contracts

| `status` | Meaning | `verified` |
|---|---|---|
| `guaranteed` | Matched to `contracts.csv`; AAV is applied to each season (deferrals use the CBT AAV column) | `true`, unless the guarantee ended before the planning season |
| `pre-arb` | Not curated. Estimated from MLB debut year: league minimum before arbitration | `false` |
| `arbitration` | Not curated. In arbitration in the planning season, estimated at 20%, 30% or 45% of projected market value, capped at $30M | `false` |
| `estimated` | Veteran not in the curated seed. One-year salary estimated from projected value | `false` |

Service time is approximated from the debut year. Super Two status, options and opt-outs aren't modeled. The UI marks every estimate.

**Surplus value** is `Σ (proj sWAR × $/WAR × 1.03^year − salary)` over the seasons of control. `DOLLARS_PER_WAR_M` defaults to 9.0, and the tax threshold (`CBT_THRESHOLD_M`) defaults to 244.

## Archetypes

Rule-based tags on the ratings, such as Three True Outcomes, Slugger, Contact Artist, Table Setter, Burner, Glove-First, Cannon Arm, Five-Tool, Patient Eye, Strikeout Artist, Flamethrower, Command Pitcher, Weak Contact, Workhorse and High-Leverage Arm. Rules live in `backend/app/model.py`.

## Skill map

The constellation view places each player using the first two principal components of his rating vector, with missing ratings imputed as 50. Hitters and pitchers are mapped separately. Nearby players have similar shapes.

## Refreshing

```bash
python backend/scripts/ingest.py
```

The script prints any curated contracts it couldn't match. Usually that means the player left the 40-man, retired or became a free agent. Update `contracts.csv` and rerun.
