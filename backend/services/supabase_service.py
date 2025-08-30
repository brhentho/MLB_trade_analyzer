"""
Supabase Service for Baseball Trade AI
Handles all database operations and queries for the application
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import os
from dataclasses import dataclass, asdict

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradeAnalysisRecord:
    """Trade analysis record for database storage"""
    analysis_id: str
    requesting_team_id: int
    request_text: str
    urgency: str = 'medium'
    status: str = 'queued'
    progress: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    cost_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class SupabaseService:
    """
    Comprehensive Supabase service for Baseball Trade AI
    """
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Cache for frequently accessed data
        self._teams_cache = {}
        self._cache_expiry = {}
        self.cache_duration = 300  # 5 minutes
        
        # Load teams into cache
        self._refresh_teams_cache()
    
    def _refresh_teams_cache(self) -> None:
        """Refresh the teams cache"""
        try:
            response = self.supabase.table('teams').select('*').execute()
            self._teams_cache = {
                team['id']: team for team in response.data
            }
            # Also create mappings by team_key and abbreviation
            for team in response.data:
                self._teams_cache[team['team_key']] = team
                self._teams_cache[team['abbreviation']] = team
            
            self._cache_expiry['teams'] = datetime.now() + timedelta(seconds=self.cache_duration)
            logger.info(f"Refreshed teams cache with {len(response.data)} teams")
        except Exception as e:
            logger.error(f"Failed to refresh teams cache: {e}")
    
    def _is_cache_expired(self, cache_key: str) -> bool:
        """Check if cache is expired"""
        return cache_key not in self._cache_expiry or datetime.now() > self._cache_expiry[cache_key]
    
    # ===================
    # TEAM OPERATIONS
    # ===================
    
    async def get_all_teams(self) -> List[Dict[str, Any]]:
        """Get all MLB teams"""
        if self._is_cache_expired('teams'):
            self._refresh_teams_cache()
        
        return [team for team in self._teams_cache.values() if isinstance(team.get('id'), int)]
    
    async def get_team_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Get team by ID"""
        if self._is_cache_expired('teams'):
            self._refresh_teams_cache()
        
        return self._teams_cache.get(team_id)
    
    async def get_team_by_key(self, team_key: str) -> Optional[Dict[str, Any]]:
        """Get team by team_key or abbreviation"""
        if self._is_cache_expired('teams'):
            self._refresh_teams_cache()
        
        return self._teams_cache.get(team_key.lower()) or self._teams_cache.get(team_key.upper())
    
    async def update_team_info(self, team_id: int, updates: Dict[str, Any]) -> bool:
        """Update team information"""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            response = self.supabase.table('teams').update(updates).eq('id', team_id).execute()
            
            if response.data:
                # Update cache
                self._teams_cache[team_id].update(updates)
                logger.info(f"Updated team {team_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating team {team_id}: {e}")
            return False
    
    # ===================
    # PLAYER OPERATIONS
    # ===================
    
    async def get_player_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get player by exact name match"""
        try:
            response = self.supabase.table('players').select('*').eq('name', name).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching player {name}: {e}")
            return None
    
    async def search_players(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search players by name (fuzzy search)"""
        try:
            response = self.supabase.table('players').select('*').ilike('name', f'%{search_term}%').limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error searching players with term '{search_term}': {e}")
            return []
    
    async def get_team_roster(self, team_id: int) -> List[Dict[str, Any]]:
        """Get all players for a team"""
        try:
            response = self.supabase.table('players').select('*').eq('team_id', team_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching roster for team {team_id}: {e}")
            return []
    
    async def get_players_by_position(self, position: str, min_war: float = 0.0) -> List[Dict[str, Any]]:
        """Get players by position with minimum WAR"""
        try:
            response = (self.supabase.table('players')
                       .select('*')
                       .eq('position', position)
                       .gte('war', min_war)
                       .execute())
            return response.data
        except Exception as e:
            logger.error(f"Error fetching players by position {position}: {e}")
            return []
    
    async def upsert_player(self, player_data: Dict[str, Any]) -> bool:
        """Insert or update player data"""
        try:
            # Check if player exists
            existing = await self.get_player_by_name(player_data['name'])
            
            player_data['last_updated'] = datetime.now().isoformat()
            
            if existing:
                # Update existing player
                response = (self.supabase.table('players')
                           .update(player_data)
                           .eq('id', existing['id'])
                           .execute())
            else:
                # Insert new player
                response = self.supabase.table('players').insert(player_data).execute()
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error upserting player {player_data.get('name', 'Unknown')}: {e}")
            return False
    
    async def bulk_upsert_players(self, players_data: List[Dict[str, Any]]) -> int:
        """Bulk upsert multiple players"""
        success_count = 0
        
        for player_data in players_data:
            if await self.upsert_player(player_data):
                success_count += 1
            
            # Small delay to avoid overwhelming the database
            await asyncio.sleep(0.01)
        
        logger.info(f"Successfully upserted {success_count}/{len(players_data)} players")
        return success_count
    
    # ===================
    # TRADE ANALYSIS OPERATIONS
    # ===================
    
    async def create_trade_analysis(self, analysis: TradeAnalysisRecord) -> str:
        """Create new trade analysis record"""
        try:
            analysis_dict = asdict(analysis)
            analysis_dict['created_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('trade_analyses').insert(analysis_dict).execute()
            
            if response.data:
                logger.info(f"Created trade analysis {analysis.analysis_id}")
                return analysis.analysis_id
            return ""
        except Exception as e:
            logger.error(f"Error creating trade analysis {analysis.analysis_id}: {e}")
            return ""
    
    async def get_trade_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get trade analysis by ID"""
        try:
            response = (self.supabase.table('trade_analyses')
                       .select('*')
                       .eq('analysis_id', analysis_id)
                       .execute())
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching trade analysis {analysis_id}: {e}")
            return None
    
    async def update_trade_analysis_status(self, analysis_id: str, status: str, 
                                         progress: Optional[Dict[str, Any]] = None,
                                         results: Optional[Dict[str, Any]] = None,
                                         cost_info: Optional[Dict[str, Any]] = None,
                                         error_message: Optional[str] = None) -> bool:
        """Update trade analysis status and data"""
        try:
            updates = {
                'status': status
            }
            
            if progress is not None:
                updates['progress'] = progress
            
            if results is not None:
                updates['results'] = results
            
            if cost_info is not None:
                updates['cost_info'] = cost_info
            
            if error_message is not None:
                updates['error_message'] = error_message
            
            if status == 'completed':
                updates['completed_at'] = datetime.now().isoformat()
            
            response = (self.supabase.table('trade_analyses')
                       .update(updates)
                       .eq('analysis_id', analysis_id)
                       .execute())
            
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error updating trade analysis {analysis_id}: {e}")
            return False
    
    async def get_recent_trade_analyses(self, team_id: Optional[int] = None, 
                                      limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trade analyses, optionally filtered by team"""
        try:
            query = self.supabase.table('trade_analyses').select('*')
            
            if team_id:
                query = query.eq('requesting_team_id', team_id)
            
            response = (query.order('created_at', desc=True)
                           .limit(limit)
                           .execute())
            
            return response.data
        except Exception as e:
            logger.error(f"Error fetching recent trade analyses: {e}")
            return []
    
    # ===================
    # TRADE PROPOSAL OPERATIONS
    # ===================
    
    async def create_trade_proposals(self, analysis_id: str, 
                                   proposals: List[Dict[str, Any]]) -> bool:
        """Create trade proposals for an analysis"""
        try:
            # Get the analysis database ID
            analysis = await self.get_trade_analysis(analysis_id)
            if not analysis:
                return False
            
            analysis_db_id = analysis['id']
            
            # Prepare proposal records
            proposal_records = []
            for i, proposal in enumerate(proposals):
                record = {
                    'analysis_id': analysis_db_id,
                    'proposal_rank': i + 1,
                    'teams_involved': proposal.get('teams_involved', []),
                    'players_involved': proposal.get('players_involved', []),
                    'likelihood': proposal.get('likelihood', 'medium'),
                    'financial_impact': proposal.get('financial_impact', {}),
                    'risk_assessment': proposal.get('risk_assessment', {}),
                    'created_at': datetime.now().isoformat()
                }
                proposal_records.append(record)
            
            # Insert all proposals
            response = self.supabase.table('trade_proposals').insert(proposal_records).execute()
            
            if response.data:
                logger.info(f"Created {len(proposal_records)} trade proposals for analysis {analysis_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error creating trade proposals for analysis {analysis_id}: {e}")
            return False
    
    async def get_trade_proposals(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Get all trade proposals for an analysis"""
        try:
            # Get the analysis database ID first
            analysis = await self.get_trade_analysis(analysis_id)
            if not analysis:
                return []
            
            response = (self.supabase.table('trade_proposals')
                       .select('*')
                       .eq('analysis_id', analysis['id'])
                       .order('proposal_rank')
                       .execute())
            
            return response.data
        except Exception as e:
            logger.error(f"Error fetching trade proposals for analysis {analysis_id}: {e}")
            return []
    
    # ===================
    # ANALYTICS OPERATIONS
    # ===================
    
    async def get_team_stats_summary(self, team_id: int) -> Dict[str, Any]:
        """Get comprehensive team statistics summary"""
        try:
            # Get team roster
            roster = await self.get_team_roster(team_id)
            
            if not roster:
                return {}
            
            # Calculate team statistics
            total_war = sum(player.get('war', 0) for player in roster if player.get('war'))
            avg_age = sum(player.get('age', 0) for player in roster if player.get('age')) / len([p for p in roster if p.get('age')])
            total_salary = sum(player.get('salary', 0) for player in roster if player.get('salary'))
            
            # Position breakdown
            positions = {}
            for player in roster:
                pos = player.get('position', 'Unknown')
                positions[pos] = positions.get(pos, 0) + 1
            
            return {
                'team_id': team_id,
                'total_players': len(roster),
                'total_war': round(total_war, 1),
                'average_age': round(avg_age, 1),
                'total_salary': total_salary,
                'position_breakdown': positions,
                'last_calculated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating team stats for team {team_id}: {e}")
            return {}
    
    async def get_position_market_data(self, position: str) -> Dict[str, Any]:
        """Get market data for a specific position"""
        try:
            players = await self.get_players_by_position(position)
            
            if not players:
                return {}
            
            # Calculate market statistics
            wars = [p.get('war', 0) for p in players if p.get('war')]
            salaries = [p.get('salary', 0) for p in players if p.get('salary')]
            ages = [p.get('age', 0) for p in players if p.get('age')]
            
            return {
                'position': position,
                'total_players': len(players),
                'avg_war': round(sum(wars) / len(wars), 2) if wars else 0,
                'median_war': round(sorted(wars)[len(wars)//2], 2) if wars else 0,
                'avg_salary': round(sum(salaries) / len(salaries), 2) if salaries else 0,
                'avg_age': round(sum(ages) / len(ages), 1) if ages else 0,
                'top_performers': sorted(players, key=lambda x: x.get('war', 0), reverse=True)[:10]
            }
        except Exception as e:
            logger.error(f"Error calculating market data for position {position}: {e}")
            return {}
    
    # ===================
    # UTILITY OPERATIONS
    # ===================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database connectivity and basic stats"""
        try:
            # Test basic connectivity
            teams_count = len(await self.get_all_teams())
            
            # Get player count
            players_response = self.supabase.table('players').select('id', count='exact').execute()
            players_count = players_response.count
            
            # Get recent analysis count
            recent_analyses = await self.get_recent_trade_analyses(limit=5)
            
            return {
                'status': 'healthy',
                'teams_count': teams_count,
                'players_count': players_count,
                'recent_analyses_count': len(recent_analyses),
                'last_analysis': recent_analyses[0]['created_at'] if recent_analyses else None,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up old data to manage storage"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            # Clean up old analyses in 'error' or 'completed' status
            old_analyses = (self.supabase.table('trade_analyses')
                           .delete()
                           .lt('created_at', cutoff_date)
                           .in_('status', ['error', 'completed'])
                           .execute())
            
            return {
                'cleaned_analyses': len(old_analyses.data) if old_analyses.data else 0,
                'cutoff_date': cutoff_date
            }
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {'error': str(e)}

# Singleton instance
supabase_service = SupabaseService()