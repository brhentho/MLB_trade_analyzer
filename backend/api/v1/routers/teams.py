"""
Teams API Endpoints - V1
Team data, rosters, and statistics with caching optimization
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from ...models import TeamInfo, TeamsResponse, PlayerInfo, AnalysisConfiguration
from ....services.supabase_service import supabase_service
from ....services.cache_service import CacheService
from ...exceptions import DatabaseException, InvalidTeamException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teams", tags=["Teams"])
cache_service = CacheService()

# Cache configuration
TEAMS_CACHE_TTL = 300  # 5 minutes
ROSTER_CACHE_TTL = 180  # 3 minutes
STATS_CACHE_TTL = 600   # 10 minutes


async def get_team_or_404(team_key: str) -> Dict:
    """Get team data or raise 404 if not found"""
    team = await supabase_service.get_team_by_key(team_key)
    if not team:
        available_teams = await supabase_service.get_all_teams()
        team_keys = [t['team_key'] for t in available_teams]
        raise InvalidTeamException(team_key, team_keys)
    return team


@router.get("", response_model=TeamsResponse)
async def get_all_teams(
    league: Optional[str] = Query(None, description="Filter by league (AL/NL)"),
    division: Optional[str] = Query(None, description="Filter by division"),
    competitive_window: Optional[str] = Query(None, description="Filter by competitive window")
) -> TeamsResponse:
    """
    Get all MLB teams with optional filtering
    Results are cached for better performance
    """
    try:
        # Generate cache key based on filters
        cache_key = f"teams:all:{league or 'all'}:{division or 'all'}:{competitive_window or 'all'}"
        
        # Check cache first
        cached_response = await cache_service.get(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for teams query: {cache_key}")
            return TeamsResponse(**cached_response)
        
        # Get from database
        teams_data = await supabase_service.get_all_teams()
        
        # Apply filters
        filtered_teams = teams_data
        if league:
            filtered_teams = [t for t in filtered_teams if t['league'].upper() == league.upper()]
        if division:
            filtered_teams = [t for t in filtered_teams if division.lower() in t['division'].lower()]
        if competitive_window:
            filtered_teams = [t for t in filtered_teams if t['competitive_window'] == competitive_window.lower()]
        
        # Convert to response models
        teams_info = [TeamInfo(**team) for team in filtered_teams]
        
        response = TeamsResponse(
            teams=teams_info,
            total_teams=len(teams_info),
            source="database"
        )
        
        # Cache the response
        await cache_service.set(cache_key, response.dict(), ttl=TEAMS_CACHE_TTL)
        logger.debug(f"Cached teams response: {cache_key}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise DatabaseException(f"Failed to retrieve teams: {str(e)}")


@router.get("/{team_key}", response_model=TeamInfo)
async def get_team(team_key: str) -> TeamInfo:
    """
    Get detailed information for a specific team
    """
    try:
        # Check cache first
        cache_key = f"team:{team_key}"
        cached_team = await cache_service.get(cache_key)
        if cached_team:
            return TeamInfo(**cached_team)
        
        # Get from database
        team_data = await get_team_or_404(team_key)
        team_info = TeamInfo(**team_data)
        
        # Cache the result
        await cache_service.set(cache_key, team_info.dict(), ttl=TEAMS_CACHE_TTL)
        
        return team_info
        
    except InvalidTeamException:
        raise
    except Exception as e:
        logger.error(f"Error getting team {team_key}: {e}")
        raise DatabaseException(f"Failed to retrieve team: {str(e)}")


@router.get("/{team_key}/roster", response_model=List[PlayerInfo])
async def get_team_roster(
    team_key: str,
    position: Optional[str] = Query(None, description="Filter by position"),
    min_war: Optional[float] = Query(None, description="Minimum WAR threshold")
) -> List[PlayerInfo]:
    """
    Get current roster for a team with optional filtering
    """
    try:
        # Validate team exists
        team_data = await get_team_or_404(team_key)
        
        # Generate cache key
        cache_key = f"roster:{team_key}:{position or 'all'}:{min_war or 'all'}"
        
        # Check cache
        cached_roster = await cache_service.get(cache_key)
        if cached_roster:
            return [PlayerInfo(**p) for p in cached_roster]
        
        # Get roster from database
        roster_data = await supabase_service.get_team_roster(team_data['id'])
        
        # Apply filters
        if position:
            roster_data = [p for p in roster_data if p.get('position', '').upper() == position.upper()]
        if min_war is not None:
            roster_data = [p for p in roster_data if (p.get('war') or 0) >= min_war]
        
        # Convert to response models
        roster = [PlayerInfo(**player) for player in roster_data]
        
        # Cache the result
        await cache_service.set(cache_key, [p.dict() for p in roster], ttl=ROSTER_CACHE_TTL)
        
        return roster
        
    except InvalidTeamException:
        raise
    except Exception as e:
        logger.error(f"Error getting roster for {team_key}: {e}")
        raise DatabaseException(f"Failed to retrieve roster: {str(e)}")


@router.get("/{team_key}/stats", response_model=Dict)
async def get_team_statistics(team_key: str) -> Dict:
    """
    Get comprehensive team statistics and analytics
    """
    try:
        # Validate team exists
        team_data = await get_team_or_404(team_key)
        
        # Check cache
        cache_key = f"stats:{team_key}"
        cached_stats = await cache_service.get(cache_key)
        if cached_stats:
            return cached_stats
        
        # Get statistics from database
        stats = await supabase_service.get_team_stats_summary(team_data['id'])
        
        if not stats:
            stats = {
                "message": "No statistics available",
                "team_key": team_key,
                "team_name": team_data.get('name', 'Unknown')
            }
        
        # Add additional computed metrics
        roster = await supabase_service.get_team_roster(team_data['id'])
        
        # Position strength analysis
        position_strength = {}
        for player in roster:
            pos = player.get('position', 'Unknown')
            war = player.get('war', 0) or 0
            if pos not in position_strength:
                position_strength[pos] = {'count': 0, 'total_war': 0, 'avg_war': 0}
            position_strength[pos]['count'] += 1
            position_strength[pos]['total_war'] += war
            position_strength[pos]['avg_war'] = position_strength[pos]['total_war'] / position_strength[pos]['count']
        
        # Team needs analysis (simplified)
        needs_analysis = []
        for pos, data in position_strength.items():
            if data['avg_war'] < 1.0 and data['count'] < 3:  # Simple threshold
                needs_analysis.append({
                    'position': pos,
                    'priority': 'high' if data['avg_war'] < 0.5 else 'medium',
                    'current_war': data['avg_war'],
                    'player_count': data['count']
                })
        
        enhanced_stats = {
            **stats,
            'position_strength': position_strength,
            'identified_needs': needs_analysis,
            'last_updated': stats.get('last_calculated')
        }
        
        # Cache the enhanced stats
        await cache_service.set(cache_key, enhanced_stats, ttl=STATS_CACHE_TTL)
        
        return enhanced_stats
        
    except InvalidTeamException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics for {team_key}: {e}")
        raise DatabaseException(f"Failed to retrieve statistics: {str(e)}")


@router.get("/{team_key}/needs", response_model=Dict)
async def get_team_needs(team_key: str) -> Dict:
    """
    Get AI-analyzed team needs and trade priorities
    """
    try:
        # Validate team exists
        team_data = await get_team_or_404(team_key)
        
        # Check cache
        cache_key = f"needs:{team_key}"
        cached_needs = await cache_service.get(cache_key)
        if cached_needs:
            return cached_needs
        
        # Get current roster and stats
        roster = await supabase_service.get_team_roster(team_data['id'])
        team_stats = await supabase_service.get_team_stats_summary(team_data['id'])
        
        # Analyze needs based on roster composition and performance
        needs_analysis = await analyze_team_needs(team_data, roster, team_stats)
        
        # Cache the analysis
        await cache_service.set(cache_key, needs_analysis, ttl=STATS_CACHE_TTL)
        
        return needs_analysis
        
    except InvalidTeamException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing needs for {team_key}: {e}")
        raise DatabaseException(f"Failed to analyze team needs: {str(e)}")


@router.get("/{team_key}/trade-history", response_model=List[Dict])
async def get_team_trade_history(
    team_key: str,
    limit: int = Query(20, ge=1, le=100, description="Number of analyses to return")
) -> List[Dict]:
    """
    Get recent trade analyses for this team
    """
    try:
        # Validate team exists
        team_data = await get_team_or_404(team_key)
        
        # Get trade history from database
        analyses = await supabase_service.get_recent_trade_analyses(
            team_id=team_data['id'],
            limit=limit
        )
        
        # Format for response
        trade_history = []
        for analysis in analyses:
            history_item = {
                'analysis_id': analysis['analysis_id'],
                'request_text': analysis['request_text'],
                'urgency': analysis['urgency'],
                'status': analysis['status'],
                'created_at': analysis['created_at'],
                'completed_at': analysis.get('completed_at'),
                'has_proposals': bool(analysis.get('results', {}).get('trade_recommendations'))
            }
            trade_history.append(history_item)
        
        return trade_history
        
    except InvalidTeamException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade history for {team_key}: {e}")
        raise DatabaseException(f"Failed to retrieve trade history: {str(e)}")


async def analyze_team_needs(team_data: Dict, roster: List[Dict], stats: Dict) -> Dict:
    """
    Analyze team needs based on roster composition and performance
    This is a simplified analysis - in production would use more sophisticated metrics
    """
    needs = {
        'team': team_data['team_key'],
        'competitive_window': team_data['competitive_window'],
        'budget_level': team_data['budget_level'],
        'primary_needs': [],
        'secondary_needs': [],
        'trade_priorities': [],
        'recommendations': []
    }
    
    # Position analysis
    position_war = {}
    position_count = {}
    
    for player in roster:
        pos = player.get('position', 'Unknown')
        war = player.get('war', 0) or 0
        
        if pos not in position_war:
            position_war[pos] = 0
            position_count[pos] = 0
        
        position_war[pos] += war
        position_count[pos] += 1
    
    # Identify needs based on WAR thresholds
    critical_positions = ['SP', 'C', '1B', '2B', '3B', 'SS', 'OF']
    
    for pos in critical_positions:
        total_war = position_war.get(pos, 0)
        player_count = position_count.get(pos, 0)
        avg_war = total_war / max(player_count, 1)
        
        if total_war < 1.0 or (pos == 'SP' and total_war < 3.0):
            priority = 'high' if total_war < 0 else 'medium'
            needs['primary_needs'].append({
                'position': pos,
                'priority': priority,
                'current_war': round(total_war, 1),
                'recommended_target_war': 2.0 if pos != 'SP' else 4.0
            })
    
    # Generate recommendations based on competitive window
    window = team_data['competitive_window']
    if window == 'win-now':
        needs['recommendations'] = [
            'Target proven veterans with immediate impact',
            'Consider rental players if salary allows',
            'Prioritize positions with negative WAR',
            'Look for playoff experience'
        ]
    elif window == 'retool':
        needs['recommendations'] = [
            'Balance immediate help with future assets',
            'Target players with 2-3 years of control',
            'Consider taking on salary for better prospects',
            'Focus on positions of strength to trade from'
        ]
    else:  # rebuild
        needs['recommendations'] = [
            'Trade veteran assets for prospects',
            'Target high-upside young players',
            'Accept short-term performance decline',
            'Build organizational depth'
        ]
    
    return needs