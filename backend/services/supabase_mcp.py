"""
Supabase MCP-style Integration for Baseball Trade AI
Provides MCP-like tools for database operations with Python 3.9 compatibility
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseTool:
    """Represents a database operation tool"""
    name: str
    description: str
    parameters: Dict[str, Any]

class SupabaseMCP:
    """
    MCP-style interface for Supabase database operations
    Provides tools for querying and manipulating MLB trade data
    """
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Register available tools
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, DatabaseTool]:
        """Register all available database tools"""
        return {
            "get_teams": DatabaseTool(
                name="get_teams",
                description="Get all MLB teams or filter by specific criteria",
                parameters={
                    "division": {"type": "string", "description": "Filter by division (e.g., 'AL East')"},
                    "league": {"type": "string", "description": "Filter by league ('AL' or 'NL')"},
                    "budget_level": {"type": "string", "description": "Filter by budget level ('low', 'medium', 'high')"},
                    "limit": {"type": "integer", "description": "Maximum number of teams to return"}
                }
            ),
            
            "get_players": DatabaseTool(
                name="get_players",
                description="Get players with optional filtering",
                parameters={
                    "team_id": {"type": "integer", "description": "Filter by team ID"},
                    "position": {"type": "string", "description": "Filter by position"},
                    "min_war": {"type": "number", "description": "Minimum WAR value"},
                    "name": {"type": "string", "description": "Player name (partial match)"},
                    "limit": {"type": "integer", "description": "Maximum number of players to return"}
                }
            ),
            
            "get_team_roster": DatabaseTool(
                name="get_team_roster",
                description="Get complete roster for a specific team",
                parameters={
                    "team_identifier": {"type": "string", "description": "Team abbreviation (e.g., 'NYY') or team key"},
                    "position_filter": {"type": "string", "description": "Filter by position ('Pitcher', 'Position Player')"}
                }
            ),
            
            "search_players": DatabaseTool(
                name="search_players",
                description="Search for players by name or statistics",
                parameters={
                    "query": {"type": "string", "description": "Search query (player name)"},
                    "min_war": {"type": "number", "description": "Minimum WAR"},
                    "max_age": {"type": "integer", "description": "Maximum age"},
                    "position": {"type": "string", "description": "Position filter"}
                }
            ),
            
            "get_trade_analyses": DatabaseTool(
                name="get_trade_analyses",
                description="Get trade analysis records",
                parameters={
                    "status": {"type": "string", "description": "Filter by status ('queued', 'analyzing', 'completed', 'error')"},
                    "team_id": {"type": "integer", "description": "Filter by requesting team"},
                    "limit": {"type": "integer", "description": "Maximum number of records to return"}
                }
            ),
            
            "create_trade_analysis": DatabaseTool(
                name="create_trade_analysis",
                description="Create a new trade analysis request",
                parameters={
                    "team_id": {"type": "integer", "description": "Requesting team ID"},
                    "request_text": {"type": "string", "description": "Trade request description"},
                    "urgency": {"type": "string", "description": "Urgency level ('low', 'medium', 'high')"}
                }
            ),
            
            "update_player": DatabaseTool(
                name="update_player",
                description="Update player information",
                parameters={
                    "player_id": {"type": "integer", "description": "Player ID to update"},
                    "data": {"type": "object", "description": "Data to update (stats, team_id, etc.)"}
                }
            ),
            
            "get_team_statistics": DatabaseTool(
                name="get_team_statistics",
                description="Get aggregated statistics for a team",
                parameters={
                    "team_id": {"type": "integer", "description": "Team ID"},
                    "stat_type": {"type": "string", "description": "Type of stats ('batting', 'pitching', 'both')"}
                }
            )
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a database tool with given parameters"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            method = getattr(self, f"_execute_{tool_name}")
            result = await method(parameters)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_get_teams(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get teams with filtering"""
        query = self.supabase.table('teams').select('*')
        
        if params.get('division'):
            query = query.eq('division', params['division'])
        if params.get('league'):
            query = query.eq('league', params['league'])
        if params.get('budget_level'):
            query = query.eq('budget_level', params['budget_level'])
        if params.get('limit'):
            query = query.limit(params['limit'])
        
        response = query.execute()
        return response.data
    
    async def _execute_get_players(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get players with filtering"""
        query = self.supabase.table('players').select('*, teams(name, abbreviation)')
        
        if params.get('team_id'):
            query = query.eq('team_id', params['team_id'])
        if params.get('position'):
            query = query.eq('position', params['position'])
        if params.get('min_war'):
            query = query.gte('war', params['min_war'])
        if params.get('name'):
            query = query.ilike('name', f"%{params['name']}%")
        if params.get('limit'):
            query = query.limit(params['limit'])
        
        response = query.execute()
        return response.data
    
    async def _execute_get_team_roster(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get complete team roster"""
        team_identifier = params.get('team_identifier')
        if not team_identifier:
            raise ValueError("team_identifier is required")
        
        # First, find the team
        team_query = self.supabase.table('teams').select('id, name, abbreviation')
        team_query = team_query.or_(f"abbreviation.eq.{team_identifier},team_key.eq.{team_identifier}")
        team_response = team_query.execute()
        
        if not team_response.data:
            raise ValueError(f"Team not found: {team_identifier}")
        
        team = team_response.data[0]
        
        # Get roster
        roster_query = self.supabase.table('players').select('*').eq('team_id', team['id'])
        
        if params.get('position_filter'):
            roster_query = roster_query.eq('position', params['position_filter'])
        
        roster_response = roster_query.execute()
        
        return {
            "team": team,
            "roster": roster_response.data,
            "count": len(roster_response.data)
        }
    
    async def _execute_search_players(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search players by various criteria"""
        query = self.supabase.table('players').select('*, teams(name, abbreviation)')
        
        if params.get('query'):
            query = query.ilike('name', f"%{params['query']}%")
        if params.get('min_war'):
            query = query.gte('war', params['min_war'])
        if params.get('max_age'):
            query = query.lte('age', params['max_age'])
        if params.get('position'):
            query = query.eq('position', params['position'])
        
        query = query.order('war', desc=True).limit(50)  # Limit to top 50 by WAR
        
        response = query.execute()
        return response.data
    
    async def _execute_get_trade_analyses(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get trade analysis records"""
        query = self.supabase.table('trade_analyses').select('*, teams(name, abbreviation)')
        
        if params.get('status'):
            query = query.eq('status', params['status'])
        if params.get('team_id'):
            query = query.eq('requesting_team_id', params['team_id'])
        if params.get('limit'):
            query = query.limit(params['limit'])
        
        query = query.order('created_at', desc=True)
        
        response = query.execute()
        return response.data
    
    async def _execute_create_trade_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new trade analysis"""
        import uuid
        
        analysis_data = {
            'analysis_id': str(uuid.uuid4()),
            'requesting_team_id': params['team_id'],
            'request_text': params['request_text'],
            'urgency': params.get('urgency', 'medium'),
            'status': 'queued',
            'progress': {},
            'results': {},
            'cost_info': {}
        }
        
        response = self.supabase.table('trade_analyses').insert(analysis_data).execute()
        return response.data[0]
    
    async def _execute_update_player(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update player information"""
        player_id = params.get('player_id')
        data = params.get('data', {})
        
        if not player_id:
            raise ValueError("player_id is required")
        
        # Due to database trigger issues, we'll implement player updates via delete/insert
        # Get the current player data first
        current_player = self.supabase.table('players').select('*').eq('id', player_id).execute()
        
        if not current_player.data:
            raise ValueError(f"Player with ID {player_id} not found")
        
        # Merge the update data with current data
        updated_data = current_player.data[0].copy()
        updated_data.pop('id', None)  # Remove ID for reinsertion
        updated_data.pop('created_at', None)  # Remove timestamps
        updated_data.pop('last_updated', None)
        
        # Apply the updates
        for key, value in data.items():
            if key not in ['id', 'created_at', 'last_updated']:
                updated_data[key] = value
        
        # Delete the old record and insert the new one
        self.supabase.table('players').delete().eq('id', player_id).execute()
        response = self.supabase.table('players').insert(updated_data).execute()
        
        return response.data[0] if response.data else {}
    
    async def _execute_get_team_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get aggregated team statistics"""
        team_id = params.get('team_id')
        stat_type = params.get('stat_type', 'both')
        
        if not team_id:
            raise ValueError("team_id is required")
        
        # Get team info
        team_response = self.supabase.table('teams').select('*').eq('id', team_id).execute()
        if not team_response.data:
            raise ValueError(f"Team not found: {team_id}")
        
        team = team_response.data[0]
        
        # Get players
        players_response = self.supabase.table('players').select('*').eq('team_id', team_id).execute()
        players = players_response.data
        
        # Calculate aggregated stats
        batting_stats = []
        pitching_stats = []
        
        for player in players:
            if player.get('stats'):
                if player['stats'].get('type') == 'batting' and stat_type in ['batting', 'both']:
                    batting_stats.append(player['stats'])
                elif player['stats'].get('type') == 'pitching' and stat_type in ['pitching', 'both']:
                    pitching_stats.append(player['stats'])
        
        return {
            "team": team,
            "total_players": len(players),
            "batting_players": len(batting_stats),
            "pitching_players": len(pitching_stats),
            "average_war": sum(p.get('war', 0) for p in players) / len(players) if players else 0,
            "top_performers": sorted(players, key=lambda p: p.get('war', 0), reverse=True)[:5]
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database connection and basic health"""
        try:
            # Test basic query
            teams_response = self.supabase.table('teams').select('id').limit(1).execute()
            players_response = self.supabase.table('players').select('id').limit(1).execute()
            
            teams_count_response = self.supabase.table('teams').select('id', count='exact').execute()
            players_count_response = self.supabase.table('players').select('id', count='exact').execute()
            
            return {
                "status": "healthy",
                "database_accessible": True,
                "teams_count": teams_count_response.count,
                "players_count": players_count_response.count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Singleton instance
supabase_mcp = SupabaseMCP()

# Convenience functions for direct use
async def get_teams(**kwargs) -> List[Dict[str, Any]]:
    """Get teams with filtering"""
    result = await supabase_mcp.execute_tool("get_teams", kwargs)
    return result.get("data", [])

async def get_players(**kwargs) -> List[Dict[str, Any]]:
    """Get players with filtering"""
    result = await supabase_mcp.execute_tool("get_players", kwargs)
    return result.get("data", [])

async def get_team_roster(team_identifier: str, **kwargs) -> Dict[str, Any]:
    """Get complete team roster"""
    result = await supabase_mcp.execute_tool("get_team_roster", {"team_identifier": team_identifier, **kwargs})
    return result.get("data", {})

async def search_players(query: str, **kwargs) -> List[Dict[str, Any]]:
    """Search for players"""
    result = await supabase_mcp.execute_tool("search_players", {"query": query, **kwargs})
    return result.get("data", [])

if __name__ == "__main__":
    # Test the MCP integration
    async def test_mcp():
        print("🔧 Testing Supabase MCP Integration...")
        
        # Health check
        health = await supabase_mcp.health_check()
        print(f"Health: {health}")
        
        # List tools
        tools = supabase_mcp.list_tools()
        print(f"Available tools: {len(tools)}")
        
        # Test getting teams
        teams = await get_teams(limit=3)
        print(f"Sample teams: {len(teams)}")
        for team in teams:
            print(f"  - {team['name']} ({team['abbreviation']})")
    
    asyncio.run(test_mcp())