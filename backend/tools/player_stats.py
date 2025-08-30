"""
Player Statistics Tools for CrewAI Agents - Live Data Integration
"""

from crewai.tools import tool
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_service import supabase_service
from services.statcast_service import statcast_service


@tool
def get_player_stats(player_name: str, season: int = 2024, stat_type: str = "batting") -> Dict[str, Any]:
    """
    Get comprehensive player statistics for evaluation using live Supabase data.
    
    Args:
        player_name: Full player name (e.g., "Aaron Judge")
        season: Season year (default 2024)
        stat_type: Type of stats ("batting", "pitching", "fielding")
    
    Returns:
        Dictionary containing player statistics and metadata
    """
    if not player_name or len(player_name.strip()) < 2:
        raise ValueError("Invalid player name provided")
    
    try:
        # Get player from database
        player_data = asyncio.run(supabase_service.get_player_by_name(player_name))
        
        if not player_data:
            # Try searching with partial match
            search_results = asyncio.run(supabase_service.search_players(player_name, limit=1))
            player_data = search_results[0] if search_results else None
        
        if not player_data:
            return {
                "error": f"Player '{player_name}' not found in database",
                "suggestion": "Check spelling or try searching with partial name",
                "search_term": player_name
            }
        
        # Get team info
        team_data = asyncio.run(supabase_service.get_team_by_id(player_data.get('team_id'))) if player_data.get('team_id') else None
        team_abbr = team_data.get('abbreviation', 'UNK') if team_data else 'UNK'
        
        # Extract stats from JSON field
        stats = player_data.get('stats', {})
        
        # Return formatted stats based on type
        if stat_type.lower() == "pitching" and stats.get('type') == 'pitching':
            return {
                "player_name": player_data['name'],
                "season": stats.get('season', season),
                "team": team_abbr,
                "position": player_data.get('position', 'P'),
                "age": player_data.get('age'),
                "games": stats.get('games', 0),
                "games_started": stats.get('games_started', 0),
                "innings_pitched": stats.get('innings_pitched', 0),
                "strikeouts": stats.get('strikeouts', 0),
                "era": stats.get('era', 0.0),
                "whip": stats.get('whip', 0.0),
                "fip": stats.get('fip', 0.0),
                "wins": stats.get('wins', 0),
                "saves": stats.get('saves', 0),
                "war": player_data.get('war', 0.0),
                "updated_at": player_data.get('last_updated', datetime.now().isoformat()),
                "source": "supabase_live_data"
            }
        else:
            # Return batting stats (default)
            return {
                "player_name": player_data['name'],
                "season": stats.get('season', season),
                "team": team_abbr,
                "position": player_data.get('position', 'Position Player'),
                "age": player_data.get('age'),
                "games": stats.get('games', 0),
                "plate_appearances": stats.get('plate_appearances', 0),
                "home_runs": stats.get('hr', 0),
                "rbi": stats.get('rbi', 0),
                "stolen_bases": stats.get('sb', 0),
                "batting_average": stats.get('avg', 0.0),
                "on_base_percentage": stats.get('obp', 0.0),
                "slugging_percentage": stats.get('slg', 0.0),
                "ops": stats.get('ops', 0.0),
                "war": player_data.get('war', 0.0),
                "salary": player_data.get('salary'),
                "contract_years": player_data.get('contract_years'),
                "updated_at": player_data.get('last_updated', datetime.now().isoformat()),
                "source": "supabase_live_data"
            }
    
    except Exception as e:
        return {
            "error": f"Failed to fetch stats for {player_name}: {str(e)}",
            "player_name": player_name,
            "season": season,
            "fallback": "database_error"
        }


@tool
def get_player_career_stats(player_name: str, years: int = 3) -> Dict[str, Any]:
    """
    Get multi-year career statistics for trend analysis.
    
    Args:
        player_name: Full player name
        years: Number of recent years to include (default 3)
    
    Returns:
        Dictionary with multi-year statistics and trends
    """
    # Mock implementation showing career progression
    return {
        "player_name": player_name,
        "years_analyzed": years,
        "career_summary": {
            "seasons": 8,
            "games": 982,
            "career_war": 42.1,
            "avg_war_per_season": 5.3
        },
        "recent_trends": {
            "power_trend": "increasing",
            "contact_trend": "stable", 
            "health_trend": "concerning",
            "performance_trajectory": "peak_years"
        },
        "yearly_stats": [
            {"season": 2024, "games": 148, "war": 10.5, "ops": 1.109},
            {"season": 2023, "games": 133, "war": 8.9, "ops": 1.000},
            {"season": 2022, "games": 157, "war": 11.2, "ops": 1.111}
        ],
        "updated_at": datetime.now().isoformat()
    }


@tool  
def compare_players(player_names: List[str], metric: str = "war") -> Dict[str, Any]:
    """
    Compare multiple players on specific metrics.
    
    Args:
        player_names: List of player names to compare
        metric: Primary metric for comparison ("war", "ops", "era", etc.)
    
    Returns:
        Comparison analysis with rankings and insights
    """
    if not player_names or len(player_names) < 2:
        raise ValueError("Need at least 2 players for comparison")
    
    # Mock comparison data
    return {
        "comparison_metric": metric,
        "players_compared": len(player_names),
        "rankings": [
            {"player": player_names[0], "value": 10.5, "rank": 1},
            {"player": player_names[1], "value": 8.2, "rank": 2},
        ],
        "analysis": {
            "leader": player_names[0],
            "gap_to_second": 2.3,
            "competitive_level": "significant_difference"
        },
        "contextual_notes": [
            f"{player_names[0]} significantly outperforms in {metric}",
            "Consider park factors and team context"
        ],
        "updated_at": datetime.now().isoformat()
    }


@tool
def get_advanced_metrics(player_name: str, season: int = 2024) -> Dict[str, Any]:
    """
    Get advanced sabermetric and Statcast statistics for deeper analysis.
    
    Args:
        player_name: Full player name
        season: Season year
    
    Returns:
        Advanced metrics including Statcast data and context-dependent stats
    """
    try:
        # Get Statcast profile
        statcast_metrics = asyncio.run(statcast_service.get_trade_relevant_metrics(player_name))
        
        if not statcast_metrics:
            return {
                "player_name": player_name,
                "season": season,
                "error": "No advanced metrics available",
                "message": "Player not found in Statcast database or insufficient data"
            }
        
        # Get basic player stats for context
        basic_stats = get_player_stats(player_name, season)
        
        return {
            "player_name": player_name,
            "season": season,
            "statcast_grade": statcast_metrics.get('statcast_grade', 'Unknown'),
            "key_strengths": statcast_metrics.get('key_strengths', []),
            "concerns": statcast_metrics.get('concerns', []),
            "trade_value_factors": statcast_metrics.get('trade_value_factors', {}),
            "basic_context": {
                "war": basic_stats.get('war', 0),
                "team": basic_stats.get('team', 'Unknown'),
                "position": basic_stats.get('position', 'Unknown')
            },
            "updated_at": datetime.now().isoformat(),
            "data_source": "statcast_service"
        }
        
    except Exception as e:
        return {
            "player_name": player_name,
            "season": season,
            "error": f"Failed to fetch advanced metrics: {str(e)}",
            "fallback": "statcast_service_error"
        }


@tool
async def get_real_time_stats(player_name: str) -> Dict[str, Any]:
    """
    Get most recent statistics with minimal delay.
    
    Args:
        player_name: Full player name
    
    Returns:
        Current season statistics with recent game performance
    """
    # Mock real-time data
    return {
        "player_name": player_name,
        "last_updated": datetime.now().isoformat(),
        "current_season": {
            "games": 148,
            "last_10_games": {
                "batting_average": 0.295,
                "ops": 1.150,
                "home_runs": 4
            },
            "season_totals": {
                "batting_average": 0.273,
                "ops": 1.109,
                "home_runs": 58
            }
        },
        "injury_status": "active",
        "recent_performance_trend": "hot_streak",
        "next_game": "2024-09-15 vs BOS"
    }

# Create aliases for backward compatibility with agent imports
stats_tool = get_player_stats