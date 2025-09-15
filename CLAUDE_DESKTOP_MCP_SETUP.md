# Claude Desktop MCP Setup for Baseball Trade AI

This guide explains how to integrate the Baseball Trade AI MCP server with Claude Desktop.

## 🚀 Quick Setup

### 1. Test MCP Integration

First, verify that the MCP integration works:

```bash
# Make sure you've set up your .env file with Supabase credentials
python3 test_mcp.py
```

This should show all tests passing if your database is properly configured.

### 2. Configure Claude Desktop

1. **Find your Claude Desktop config directory**:
   - **macOS**: `~/Library/Application Support/Claude/`
   - **Windows**: `%APPDATA%\Claude\`
   - **Linux**: `~/.config/Claude/`

2. **Edit the `claude_desktop_config.json` file** (create if it doesn't exist):

```json
{
  "mcpServers": {
    "baseball-trade-ai": {
      "command": "python3",
      "args": [
        "/Users/brycehenthorn/Desktop/github repos/MLB_trade_analyzer/mcp_server.py",
        "--serve"
      ],
      "env": {
        "SUPABASE_URL": "https://your-actual-project-id.supabase.co",
        "SUPABASE_SECRET_KEY": "your-actual-service-role-key"
      }
    }
  }
}
```

**Important**: Replace the file path and environment variables with your actual values!

### 3. Restart Claude Desktop

Close and reopen Claude Desktop for the changes to take effect.

## 🔧 Available MCP Tools

Once connected, you'll have access to these tools in Claude Desktop:

### Team Operations
- **`get_teams`** - Get MLB teams with filtering
  ```
  Parameters: division, league, budget_level, limit
  Example: Get all AL East teams
  ```

- **`get_team_roster`** - Get complete team roster
  ```
  Parameters: team_identifier (e.g., "NYY", "LAD")
  Example: Get Yankees roster
  ```

- **`get_team_statistics`** - Get aggregated team stats
  ```
  Parameters: team_id, stat_type
  Example: Get team batting/pitching aggregates
  ```

### Player Operations
- **`get_players`** - Get players with filtering
  ```
  Parameters: team_id, position, min_war, name, limit
  Example: Find players with WAR > 3.0
  ```

- **`search_players`** - Search players by name/criteria
  ```
  Parameters: query, min_war, max_age, position
  Example: Search for "Judge" or players with high WAR
  ```

### Trade Analysis
- **`get_trade_analyses`** - Get trade analysis records
  ```
  Parameters: status, team_id, limit
  Example: Get completed trade analyses
  ```

- **`create_trade_analysis`** - Create new trade analysis
  ```
  Parameters: team_id, request_text, urgency
  Example: Request analysis for "Need starting pitcher"
  ```

## 💡 Example Usage in Claude Desktop

Once connected, you can ask Claude to:

1. **"Show me all AL East teams"**
   - Claude will use `get_teams` with division filter

2. **"Who are the Yankees' best players?"**
   - Claude will use `get_team_roster` for NYY and analyze WAR

3. **"Find me players with WAR above 4.0"**
   - Claude will use `get_players` with min_war filter

4. **"Search for pitchers named Smith"**
   - Claude will use `search_players` with name and position filters

5. **"What's the Dodgers' team statistics?"**
   - Claude will use `get_team_statistics` for LAD

## 🛠 Troubleshooting

### MCP Server Not Connecting
1. Check that the file path in the config is correct
2. Verify your environment variables are set
3. Test with `python3 mcp_server.py` manually
4. Check Claude Desktop logs for errors

### Database Connection Issues
1. Run `python3 test_setup.py` to verify database access
2. Check your Supabase credentials in `.env`
3. Ensure you've run the database migrations

### Permission Errors
1. Make sure Python 3 is in your PATH
2. Check file permissions on the MCP server script
3. Try running with full Python path if needed

### No Data Returned
1. Verify you've seeded data with `python3 seed_historical_data.py`
2. Check that teams and players exist in your database
3. Test individual tools with `python3 test_mcp.py`

## 🔍 Debugging

### View MCP Server Logs
Run the server manually to see detailed logs:
```bash
python3 mcp_server.py --serve
```

### Test Individual Tools
```python
# Test in Python
from backend.services.supabase_mcp import get_teams, get_players

# Get teams
teams = await get_teams(limit=5)
print(teams)

# Get players
players = await get_players(min_war=2.0, limit=10)
print(players)
```

## 🎯 Next Steps

Once MCP is working:

1. **Seed your database** with historical data
2. **Explore team rosters** and player statistics
3. **Create trade analyses** for your favorite teams
4. **Build custom queries** using the available tools

The MCP integration makes your Baseball Trade AI database directly accessible through natural language in Claude Desktop!