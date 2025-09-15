# Baseball Trade AI - Database Setup Guide

This guide will walk you through setting up your Supabase database and seeding it with historical MLB data.

## 🚀 Quick Start

### 1. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and create a new project
2. Wait for the project to initialize (takes ~2 minutes)
3. Go to **Settings** > **API** and copy:
   - **Project URL** 
   - **Service role key** (service_role - this is your secret key)

### 2. Run Database Migrations

In your Supabase project dashboard:

1. Go to **SQL Editor**
2. Run these files **in order** by copying and pasting their contents:

   **First:** `supabase/migrations/20241205000001_initial_schema.sql`
   - Creates all tables (teams, players, prospects, trade_analyses, etc.)

   **Second:** `supabase/migrations/20241205000002_seed_teams.sql`
   - Adds all 30 MLB teams with metadata

### 3. Configure Environment

1. Update the `.env` file in the project root:
   ```bash
   SUPABASE_URL=https://your-actual-project-id.supabase.co
   SUPABASE_SECRET_KEY=your-actual-service-role-key-here
   SUPABASE_ANON_KEY=your-actual-anon-key-here
   OPENAI_API_KEY=your-openai-key-for-ai-features
   ```

### 4. Install Dependencies

```bash
pip3 install -r requirements-minimal.txt
```

### 5. Test Your Setup

```bash
python3 test_setup.py
```

This will verify:
- ✅ Supabase connection works
- ✅ Database tables exist and have team data
- ✅ Data fetching from baseball APIs works

### 6. Seed Historical Data

Once the test passes, run the historical data seeder:

```bash
python3 seed_historical_data.py
```

This will:
- 📊 Fetch 3 years of MLB data (2022-2024)
- ⚾ Process ~2,000+ players with batting and pitching stats
- 🏟️ Store everything in your Supabase database
- ⏱️ Take about 2-3 hours with respectful rate limiting

## 📋 What Gets Seeded

### Player Statistics (2022-2024)
- **Batting Stats**: AVG, OBP, SLG, OPS, HR, RBI, SB, WAR, etc.
- **Pitching Stats**: ERA, WHIP, FIP, W-L, SV, SO, WAR, etc.
- **Team Assignments**: Current and historical team rosters
- **Metadata**: Age, position, active status

### Team Information
- All 30 MLB teams with complete metadata
- Budget levels, competitive windows, market sizes
- Division/league structure
- Team philosophies and strategies

## 🔄 Daily Updates

After initial seeding, the system can automatically update with new data:

```python
# In your main application
from backend.services.scheduler_service import scheduler_service

# Start automatic daily updates at 6 AM ET
scheduler_service.start()
```

Or manually trigger updates:
```python
from backend.services.data_ingestion import data_service

# Manual update
result = await data_service.run_daily_update()
```

## 🔧 MCP Integration

This project includes a Supabase MCP (Model Context Protocol) integration for seamless database operations:

### Available MCP Tools

- `get_teams` - Get MLB teams with filtering options
- `get_players` - Get players with WAR, position, team filters
- `get_team_roster` - Get complete roster for any team
- `search_players` - Search players by name and stats
- `get_trade_analyses` - Get trade analysis records
- `create_trade_analysis` - Create new trade analysis requests
- `get_team_statistics` - Get aggregated team statistics

### Using MCP with Claude Desktop

1. **Test MCP Integration**:
   ```bash
   python3 test_mcp.py
   ```

2. **Configure Claude Desktop**:
   - Copy `claude_desktop_config.json` to your Claude Desktop MCP config
   - Update the file paths and environment variables
   - Restart Claude Desktop

3. **Start MCP Server**:
   ```bash
   python3 mcp_server.py --serve
   ```

### Using MCP Programmatically

```python
from backend.services.supabase_mcp import get_teams, get_players, search_players

# Get AL East teams
teams = await get_teams(division="AL East")

# Find high-WAR players
stars = await get_players(min_war=3.0, limit=10)

# Search for specific players
results = await search_players("Judge")
```

## 📁 Key Files

### Database & Seeding
- `seed_historical_data.py` - Main seeding script for 3 years of data
- `test_setup.py` - Verification script for your setup
- `backend/services/data_ingestion.py` - Core data fetching service
- `backend/services/scheduler_service.py` - Automated daily updates
- `supabase/migrations/` - Database schema and team data

### MCP Integration
- `backend/services/supabase_mcp.py` - MCP-style tools for database operations
- `mcp_server.py` - MCP server for Claude Desktop integration
- `test_mcp.py` - MCP integration test suite
- `claude_desktop_config.json` - Claude Desktop MCP configuration

## 🛠 Troubleshooting

### "No teams found in database"
- Make sure you ran both migration files in order
- Check that you're using the service role key, not the anon key

### "Connection failed"
- Verify your Supabase URL and service role key in `.env`
- Make sure your Supabase project is running (not paused)

### "Rate limited" or "HTTP 429 errors"
- Baseball data sources have rate limits
- The seeder includes automatic delays to respect these limits
- If you get rate limited, wait 10-15 minutes and try again

### Missing Python packages
- Run `pip3 install -r requirements-minimal.txt`
- For Python 3.9 systems, this installs compatible versions

### "Team not found" warnings during seeding
- This is normal - some players may have invalid team data
- The script will skip these players and continue

## 🎯 Next Steps

After successful setup:

1. **Explore your data** in the Supabase dashboard
2. **Set up automated daily updates** for fresh data
3. **Start the backend API** to begin trade analysis
4. **Launch the frontend** for the full trade analyzer experience

## 📊 Expected Results

After seeding completes, you should have:
- ✅ ~750 players per season × 3 seasons = ~2,250+ player records
- ✅ Complete batting and pitching statistics
- ✅ All 30 MLB teams with metadata
- ✅ Ready for AI-powered trade analysis

The setup process respects data source rate limits and typically completes in 2-3 hours.

---

Need help? Check the logs in `historical_seed.log` or run `test_setup.py` to diagnose issues.