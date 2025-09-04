"""
Players API Endpoints - V1
Player data, search, and statistics with performance optimization
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from ...models import PlayerInfo
from ....services.supabase_service import supabase_service
from ....services.cache_service import CacheService
from ....services.statcast_service import statcast_service
from ...exceptions import DatabaseException, ValidationException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/players", tags=["Players"])
cache_service = CacheService()

# Cache configuration
PLAYER_CACHE_TTL = 300    # 5 minutes
SEARCH_CACHE_TTL = 180    # 3 minutes
STATCAST_CACHE_TTL = 3600 # 1 hour


@router.get("/search", response_model=List[PlayerInfo])
async def search_players(
    q: str = Query(..., min_length=2, description="Search term (player name)"),
    position: Optional[str] = Query(None, description="Filter by position"),
    team: Optional[str] = Query(None, description="Filter by team"),
    min_war: Optional[float] = Query(None, description="Minimum WAR threshold"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return")
) -> List[PlayerInfo]:
    """
    Search players by name with optional filtering
    Results are cached for better performance
    """
    try:
        # Generate cache key
        cache_key = f"search:{q}:{position or 'all'}:{team or 'all'}:{min_war or 'all'}:{limit}"
        
        # Check cache first
        cached_results = await cache_service.get(cache_key)
        if cached_results:
            logger.debug(f"Cache hit for player search: {q}")
            return [PlayerInfo(**p) for p in cached_results]
        
        # Search in database
        players_data = await supabase_service.search_players(q, limit=limit * 2)  # Get more for filtering
        
        # Apply filters
        if position:
            players_data = [p for p in players_data if p.get('position', '').upper() == position.upper()]
        
        if team:
            # Get team ID first
            team_data = await supabase_service.get_team_by_key(team.lower())
            if team_data:
                players_data = [p for p in players_data if p.get('team_id') == team_data['id']]
            else:
                players_data = []  # Invalid team, return empty
        
        if min_war is not None:
            players_data = [p for p in players_data if (p.get('war') or 0) >= min_war]
        
        # Limit results
        players_data = players_data[:limit]
        
        # Convert to response models
        players = [PlayerInfo(**player) for player in players_data]
        
        # Cache the results
        await cache_service.set(cache_key, [p.dict() for p in players], ttl=SEARCH_CACHE_TTL)
        
        logger.info(f"Player search for '{q}' returned {len(players)} results")
        return players
        
    except Exception as e:
        logger.error(f"Error searching players with term '{q}': {e}")
        raise DatabaseException(f"Player search failed: {str(e)}")


@router.get("/{player_name}", response_model=PlayerInfo)
async def get_player(
    player_name: str = Path(..., description="Player name (exact match)")
) -> PlayerInfo:
    """
    Get detailed information for a specific player
    """
    try:
        # Check cache first
        cache_key = f"player:{player_name}"
        cached_player = await cache_service.get(cache_key)
        if cached_player:
            return PlayerInfo(**cached_player)
        
        # Get from database
        player_data = await supabase_service.get_player_by_name(player_name)
        if not player_data:
            raise HTTPException(
                status_code=404,
                detail=f"Player '{player_name}' not found"
            )
        
        player_info = PlayerInfo(**player_data)
        
        # Cache the result
        await cache_service.set(cache_key, player_info.dict(), ttl=PLAYER_CACHE_TTL)
        
        return player_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player {player_name}: {e}")
        raise DatabaseException(f"Failed to retrieve player: {str(e)}")


@router.get("/{player_name}/statcast", response_model=Dict)
async def get_player_statcast(
    player_name: str = Path(..., description="Player name"),
    season: int = Query(2024, description="Season year")
) -> Dict:
    """
    Get Statcast metrics for a player
    """
    try:
        # Check cache first
        cache_key = f"statcast:{player_name}:{season}"
        cached_stats = await cache_service.get(cache_key)
        if cached_stats:
            return cached_stats
        
        # Get from Statcast service
        profile = await statcast_service.fetch_player_statcast_profile(player_name)
        if not profile:
            raise HTTPException(
                status_code=404,
                detail=f"Statcast data not found for player '{player_name}'"
            )
        
        # Convert to dictionary format
        statcast_data = {
            'player_name': profile.player_name,
            'mlb_id': profile.mlb_id,
            'position': profile.position,
            'season': season,
            'hitting_metrics': {
                'avg_exit_velocity': profile.avg_exit_velocity,
                'max_exit_velocity': profile.max_exit_velocity,
                'barrel_percentage': profile.barrel_percentage,
                'hard_hit_percentage': profile.hard_hit_percentage,
                'expected_woba': profile.expected_woba,
                'sprint_speed': profile.sprint_speed
            },
            'pitching_metrics': {
                'avg_fastball_velocity': profile.avg_fastball_velocity,
                'fastball_spin_rate': profile.fastball_spin_rate,
                'release_extension': profile.release_extension
            },
            'last_updated': profile.last_updated.isoformat()
        }
        
        # Cache the result
        await cache_service.set(cache_key, statcast_data, ttl=STATCAST_CACHE_TTL)
        
        return statcast_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Statcast data for {player_name}: {e}")
        raise DatabaseException(f"Failed to retrieve Statcast data: {str(e)}")


@router.get("/position/{position}", response_model=List[PlayerInfo])
async def get_players_by_position(
    position: str = Path(..., description="Position (e.g., SP, C, 1B, OF)"),
    min_war: float = Query(0.0, description="Minimum WAR threshold"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    sort_by: str = Query("war", description="Sort field (war, salary, age)")
) -> List[PlayerInfo]:
    """
    Get all players at a specific position with filtering and sorting
    """
    try:
        # Validate position
        valid_positions = ['SP', 'RP', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'OF', 'DH']
        if position.upper() not in valid_positions:
            raise ValidationException(
                f"Invalid position '{position}'. Valid positions: {', '.join(valid_positions)}"
            )
        
        # Generate cache key
        cache_key = f"position:{position}:{min_war}:{limit}:{sort_by}"
        
        # Check cache
        cached_players = await cache_service.get(cache_key)
        if cached_players:
            return [PlayerInfo(**p) for p in cached_players]
        
        # Get from database
        players_data = await supabase_service.get_players_by_position(position.upper(), min_war)
        
        # Sort players
        reverse_sort = sort_by in ['war', 'salary']
        if sort_by == 'war':
            players_data.sort(key=lambda x: x.get('war', 0) or 0, reverse=True)
        elif sort_by == 'salary':
            players_data.sort(key=lambda x: x.get('salary', 0) or 0, reverse=True)
        elif sort_by == 'age':
            players_data.sort(key=lambda x: x.get('age', 0) or 0, reverse=False)
        
        # Limit results
        players_data = players_data[:limit]
        
        # Convert to response models
        players = [PlayerInfo(**player) for player in players_data]
        
        # Cache the results
        await cache_service.set(cache_key, [p.dict() for p in players], ttl=PLAYER_CACHE_TTL)
        
        logger.info(f"Retrieved {len(players)} players for position {position}")
        return players
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error getting players by position {position}: {e}")
        raise DatabaseException(f"Failed to retrieve players: {str(e)}")


@router.get("/analytics/market/{position}", response_model=Dict)
async def get_position_market_analysis(
    position: str = Path(..., description="Position to analyze")
) -> Dict:
    """
    Get market analysis for a specific position
    Includes salary ranges, WAR distributions, and trade recommendations
    """
    try:
        # Generate cache key
        cache_key = f"market:{position}"
        
        # Check cache
        cached_analysis = await cache_service.get(cache_key)
        if cached_analysis:
            return cached_analysis
        
        # Get market data from database
        market_data = await supabase_service.get_position_market_data(position.upper())
        
        if not market_data:
            raise HTTPException(
                status_code=404,
                detail=f"No market data available for position '{position}'"
            )
        
        # Enhance with additional analysis
        enhanced_analysis = {
            **market_data,
            'trade_targets': {
                'budget_friendly': [
                    p for p in market_data.get('top_performers', [])[:10]
                    if (p.get('salary', 0) or 0) < market_data.get('avg_salary', 0)
                ][:5],
                'premium_talent': [
                    p for p in market_data.get('top_performers', [])[:10]
                    if (p.get('war', 0) or 0) > market_data.get('avg_war', 0) * 1.5
                ][:5],
                'value_plays': [
                    p for p in market_data.get('top_performers', [])[:20]
                    if (p.get('war', 0) or 0) > 2.0 and (p.get('salary', 0) or 0) < 15000000
                ][:5]
            },
            'market_insights': generate_market_insights(market_data, position)
        }
        
        # Cache the enhanced analysis
        await cache_service.set(cache_key, enhanced_analysis, ttl=PLAYER_CACHE_TTL * 2)
        
        return enhanced_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing market for position {position}: {e}")
        raise DatabaseException(f"Market analysis failed: {str(e)}")


def generate_market_insights(market_data: Dict, position: str) -> List[str]:
    """Generate market insights based on position data"""
    insights = []
    
    avg_war = market_data.get('avg_war', 0)
    avg_salary = market_data.get('avg_salary', 0)
    total_players = market_data.get('total_players', 0)
    
    # WAR-based insights
    if avg_war < 1.0:
        insights.append(f"{position} market shows limited impact talent available")
    elif avg_war > 2.5:
        insights.append(f"{position} market has strong talent depth")
    
    # Salary insights
    if avg_salary > 20000000:
        insights.append(f"Premium position with high salary expectations")
    elif avg_salary < 5000000:
        insights.append(f"Cost-effective position for budget-conscious teams")
    
    # Market size insights
    if total_players < 20:
        insights.append(f"Limited {position} options suggest seller's market")
    elif total_players > 50:
        insights.append(f"Deep {position} talent pool favors buyers")
    
    # Position-specific insights
    if position == 'SP':
        insights.append("Starting pitching typically requires multiple pieces in trade packages")
    elif position == 'C':
        insights.append("Catchers often come with premium due to defensive value")
    elif position in ['SS', '2B', '3B']:
        insights.append("Middle infield positions command higher prospect costs")
    
    return insights[:5]  # Limit to top 5 insights