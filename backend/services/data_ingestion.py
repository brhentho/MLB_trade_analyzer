"""
Baseball Trade AI - Data Ingestion Service
Fetches live MLB data from multiple sources and stores in Supabase
"""

import asyncio
import logging
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json

import pandas as pd
import pybaseball as pb
from pybaseball import statcast, playerid_lookup, batting_stats, pitching_stats
from supabase import create_client, Client
import requests
from bs4 import BeautifulSoup
import time
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlayerData:
    """Player data structure for database storage"""
    name: str
    team_id: Optional[int] = None
    position: Optional[str] = None
    age: Optional[int] = None
    salary: Optional[float] = None
    contract_years: Optional[int] = None
    war: Optional[float] = None
    stats: Optional[Dict[str, Any]] = None
    mlb_id: Optional[int] = None
    fangraphs_id: Optional[str] = None

class DataIngestionService:
    """
    Main service for ingesting baseball data from multiple sources
    """
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("❌ Supabase credentials not found. Please check your .env file")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Rate limiting - be respectful to data sources
        self.request_delay = float(os.getenv('DATA_UPDATE_DELAY', '1.0'))
        
        # Cache for MLB team mappings
        self._team_cache = {}
        self._load_team_mappings()
        
        # Track stats for monitoring
        self.update_stats = {
            'last_update': None,
            'players_updated': 0,
            'errors': 0,
            'duration': 0
        }
    
    def _load_team_mappings(self) -> None:
        """Load team mappings from Supabase"""
        try:
            response = self.supabase.table('teams').select('*').execute()
            
            if not response.data:
                logger.error("❌ No teams found in database. Please run the migration files first!")
                raise ValueError("Teams table is empty. Run migration files first.")
            
            self._team_cache = {}
            
            # Create comprehensive mapping by team abbreviation and key
            for team in response.data:
                self._team_cache[team['abbreviation']] = team
                self._team_cache[team['team_key']] = team
                # Also handle common abbreviation variations
                self._team_cache[team['abbreviation'].upper()] = team
                self._team_cache[team['abbreviation'].lower()] = team
            
            # Add common variations and fixes for pybaseball data
            abbreviation_fixes = {
                'WSN': 'WSH',  # Washington Nationals
                'CWS': 'CHW',  # White Sox
                'KCR': 'KC',   # Royals
                'SDP': 'SD',   # Padres
                'SFG': 'SF',   # Giants
                'TBR': 'TB',   # Rays
                'LAA': 'ANA',  # Angels (sometimes)
            }
            
            for old_abbr, new_abbr in abbreviation_fixes.items():
                if new_abbr in self._team_cache:
                    self._team_cache[old_abbr] = self._team_cache[new_abbr]
            
            logger.info(f"Loaded {len(response.data)} team mappings")
        except Exception as e:
            logger.error(f"Failed to load team mappings: {e}")
    
    def _get_team_id(self, team_identifier: str) -> Optional[int]:
        """Get team ID from team key or abbreviation"""
        if not team_identifier:
            return None
            
        # Try exact match first
        team_data = self._team_cache.get(team_identifier)
        if team_data:
            return team_data['id']
        
        # Try uppercase match
        team_data = self._team_cache.get(team_identifier.upper())
        if team_data:
            return team_data['id']
            
        # Try lowercase match
        team_data = self._team_cache.get(team_identifier.lower())
        if team_data:
            return team_data['id']
            
        return None
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        await asyncio.sleep(self.request_delay + random.uniform(0, 0.5))
    
    async def fetch_current_rosters(self) -> Dict[str, List[PlayerData]]:
        """
        Fetch current MLB rosters using pybaseball and MLB API
        """
        logger.info("Fetching current MLB rosters...")
        rosters = {}
        
        try:
            # Use pybaseball to get current season data
            current_year = datetime.now().year
            
            # Get batting stats for current season (more reliable for roster)
            batting_data = batting_stats(current_year)
            pitching_data = pitching_stats(current_year)
            
            # Process batting data
            for _, player in batting_data.iterrows():
                team_id = self._get_team_id(player.get('Team', ''))
                if team_id:
                    player_data = PlayerData(
                        name=player.get('Name', ''),
                        team_id=team_id,
                        position='Position Player',  # Will be refined later
                        age=player.get('Age'),
                        war=player.get('WAR'),
                        stats={
                            'type': 'batting',
                            'avg': player.get('AVG'),
                            'obp': player.get('OBP'),
                            'slg': player.get('SLG'),
                            'ops': player.get('OPS'),
                            'hr': player.get('HR'),
                            'rbi': player.get('RBI'),
                            'sb': player.get('SB'),
                            'games': player.get('G'),
                            'plate_appearances': player.get('PA'),
                            'season': current_year
                        }
                    )
                    
                    if player.get('Team', '') not in rosters:
                        rosters[player.get('Team', '')] = []
                    rosters[player.get('Team', '')].append(player_data)
            
            # Process pitching data
            for _, player in pitching_data.iterrows():
                team_id = self._get_team_id(player.get('Team', ''))
                if team_id:
                    player_data = PlayerData(
                        name=player.get('Name', ''),
                        team_id=team_id,
                        position='Pitcher',
                        age=player.get('Age'),
                        war=player.get('WAR'),
                        stats={
                            'type': 'pitching',
                            'era': player.get('ERA'),
                            'whip': player.get('WHIP'),
                            'fip': player.get('FIP'),
                            'wins': player.get('W'),
                            'saves': player.get('SV'),
                            'strikeouts': player.get('SO'),
                            'innings_pitched': player.get('IP'),
                            'games': player.get('G'),
                            'games_started': player.get('GS'),
                            'season': current_year
                        }
                    )
                    
                    if player.get('Team', '') not in rosters:
                        rosters[player.get('Team', '')] = []
                    rosters[player.get('Team', '')].append(player_data)
            
            await self._rate_limit()
            logger.info(f"Successfully fetched rosters for {len(rosters)} teams")
            
        except Exception as e:
            logger.error(f"Error fetching rosters: {e}")
        
        return rosters
    
    async def fetch_statcast_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Fetch Statcast data from Baseball Savant
        """
        logger.info(f"Fetching Statcast data from {start_date} to {end_date}")
        
        try:
            # Use pybaseball's statcast function
            statcast_data = statcast(start_dt=start_date.strftime('%Y-%m-%d'), 
                                   end_dt=end_date.strftime('%Y-%m-%d'))
            
            await self._rate_limit()
            logger.info(f"Fetched {len(statcast_data)} Statcast records")
            return statcast_data
            
        except Exception as e:
            logger.error(f"Error fetching Statcast data: {e}")
            return pd.DataFrame()
    
    async def fetch_fangraphs_leaderboards(self, season: int) -> Dict[str, pd.DataFrame]:
        """
        Fetch FanGraphs leaderboard data
        """
        logger.info(f"Fetching FanGraphs leaderboards for {season}")
        leaderboards = {}
        
        try:
            # Import FanGraphs functions from pybaseball
            from pybaseball import fg_batting_data, fg_pitching_data
            
            # Get batting leaderboard
            batting_leaders = fg_batting_data(season, season, qual=50)  # 50+ PA qualifier
            leaderboards['batting'] = batting_leaders
            await self._rate_limit()
            
            # Get pitching leaderboard  
            pitching_leaders = fg_pitching_data(season, season, qual=20)  # 20+ IP qualifier
            leaderboards['pitching'] = pitching_leaders
            await self._rate_limit()
            
            logger.info(f"Fetched FanGraphs leaderboards: {len(batting_leaders)} batters, {len(pitching_leaders)} pitchers")
            
        except Exception as e:
            logger.error(f"Error fetching FanGraphs data: {e}")
        
        return leaderboards
    
    async def store_players_in_supabase(self, players: List[PlayerData]) -> bool:
        """
        Store or update player data in Supabase
        """
        logger.info(f"Storing {len(players)} players in Supabase...")
        
        try:
            for player in players:
                # Check if player exists
                existing = self.supabase.table('players').select('*').eq('name', player.name).execute()
                
                player_dict = {
                    'name': player.name,
                    'team_id': player.team_id,
                    'position': player.position,
                    'age': player.age,
                    'salary': player.salary,
                    'contract_years': player.contract_years,
                    'war': player.war,
                    'stats': player.stats,
                    'last_updated': datetime.now().isoformat()
                }
                
                if existing.data:
                    # Update existing player
                    self.supabase.table('players').update(player_dict).eq('id', existing.data[0]['id']).execute()
                else:
                    # Insert new player
                    self.supabase.table('players').insert(player_dict).execute()
            
            logger.info(f"Successfully stored {len(players)} players")
            return True
            
        except Exception as e:
            logger.error(f"Error storing players: {e}")
            return False
    
    async def update_player_salaries(self) -> bool:
        """
        Update player salary information from external sources
        """
        logger.info("Updating player salary information...")
        
        try:
            # This would typically connect to a salary database
            # For now, we'll implement a placeholder
            # TODO: Integrate with Cot's Contracts or similar salary database
            
            # Get all players without salary info
            players_without_salaries = self.supabase.table('players').select('*').is_('salary', 'null').execute()
            
            logger.info(f"Found {len(players_without_salaries.data)} players without salary data")
            
            # Placeholder salary updates would go here
            # This could involve web scraping salary sites or using a paid API
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating salaries: {e}")
            return False
    
    async def run_daily_update(self) -> Dict[str, Any]:
        """
        Run the complete daily data update process
        """
        logger.info("Starting daily data update...")
        start_time = datetime.now()
        
        results = {
            'start_time': start_time.isoformat(),
            'rosters_updated': False,
            'statcast_updated': False,
            'fangraphs_updated': False,
            'salaries_updated': False,
            'total_players_updated': 0,
            'errors': []
        }
        
        try:
            # 1. Update rosters
            rosters = await self.fetch_current_rosters()
            if rosters:
                all_players = []
                for team_players in rosters.values():
                    all_players.extend(team_players)
                
                if await self.store_players_in_supabase(all_players):
                    results['rosters_updated'] = True
                    results['total_players_updated'] = len(all_players)
                    logger.info(f"Updated {len(all_players)} players from rosters")
            
            # 2. Update recent Statcast data (last 7 days)
            end_date = date.today()
            start_date = end_date - timedelta(days=7)
            
            statcast_data = await self.fetch_statcast_data(start_date, end_date)
            if not statcast_data.empty:
                # Process and aggregate Statcast data by player
                # This would involve more complex processing
                results['statcast_updated'] = True
                logger.info(f"Processed {len(statcast_data)} Statcast records")
            
            # 3. Update FanGraphs data (weekly)
            current_year = datetime.now().year
            fangraphs_data = await self.fetch_fangraphs_leaderboards(current_year)
            if fangraphs_data:
                results['fangraphs_updated'] = True
                logger.info("Updated FanGraphs leaderboard data")
            
            # 4. Update salary information (weekly)
            if await self.update_player_salaries():
                results['salaries_updated'] = True
            
        except Exception as e:
            error_msg = f"Error in daily update: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        results['end_time'] = datetime.now().isoformat()
        results['duration_minutes'] = (datetime.now() - start_time).total_seconds() / 60
        
        logger.info(f"Daily update completed in {results['duration_minutes']:.2f} minutes")
        return results
    
    async def get_player_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get player data by name from Supabase
        """
        try:
            response = self.supabase.table('players').select('*').eq('name', name).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching player {name}: {e}")
            return None
    
    async def get_team_roster(self, team_key: str) -> List[Dict[str, Any]]:
        """
        Get full team roster from Supabase
        """
        try:
            team_id = self._get_team_id(team_key)
            if not team_id:
                return []
            
            response = self.supabase.table('players').select('*').eq('team_id', team_id).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching roster for {team_key}: {e}")
            return []
    
    async def update_current_season_stats(self) -> Dict[str, Any]:
        """
        Update current season statistics for all players
        """
        logger.info("🔄 Starting current season stats update...")
        start_time = datetime.now()
        
        result = {
            'players_updated': 0,
            'new_players': 0,
            'errors': 0,
            'duration': 0,
            'last_update': start_time.isoformat()
        }
        
        try:
            current_year = datetime.now().year
            
            # Get current season data
            logger.info(f"📊 Fetching {current_year} season data...")
            batting_data = batting_stats(current_year)
            await self._rate_limit()
            
            pitching_data = pitching_stats(current_year)
            await self._rate_limit()
            
            # Update batting players
            for _, player in batting_data.iterrows():
                try:
                    team_abbr = str(player.get('Team', '')).strip()
                    if team_abbr in ['', '- - -', 'TOT']:
                        continue
                    
                    team_id = self._get_team_id(team_abbr)
                    if not team_id:
                        continue
                    
                    # Check if player exists
                    existing = self.supabase.table('players').select('*').eq('name', player.get('Name')).eq('team_id', team_id).execute()
                    
                    player_data = {
                        'name': str(player.get('Name', '')).strip(),
                        'team_id': team_id,
                        'position': 'Batter',
                        'age': int(player.get('Age', 0)) if pd.notna(player.get('Age')) else None,
                        'war': float(player.get('WAR', 0)) if pd.notna(player.get('WAR')) else 0.0,
                        'stats': {
                            'type': 'batting',
                            'season': current_year,
                            'avg': float(player.get('AVG', 0)) if pd.notna(player.get('AVG')) else 0.0,
                            'obp': float(player.get('OBP', 0)) if pd.notna(player.get('OBP')) else 0.0,
                            'slg': float(player.get('SLG', 0)) if pd.notna(player.get('SLG')) else 0.0,
                            'ops': float(player.get('OPS', 0)) if pd.notna(player.get('OPS')) else 0.0,
                            'home_runs': int(player.get('HR', 0)) if pd.notna(player.get('HR')) else 0,
                            'rbi': int(player.get('RBI', 0)) if pd.notna(player.get('RBI')) else 0,
                            'stolen_bases': int(player.get('SB', 0)) if pd.notna(player.get('SB')) else 0,
                            'games': int(player.get('G', 0)) if pd.notna(player.get('G')) else 0,
                            'team': team_abbr
                        }
                    }
                    
                    if existing.data:
                        # Update existing player
                        player_id = existing.data[0]['id']
                        self.supabase.table('players').delete().eq('id', player_id).execute()
                        self.supabase.table('players').insert(player_data).execute()
                        result['players_updated'] += 1
                    else:
                        # Insert new player
                        self.supabase.table('players').insert(player_data).execute()
                        result['new_players'] += 1
                        
                except Exception as e:
                    logger.error(f"Error updating batting player {player.get('Name', 'Unknown')}: {e}")
                    result['errors'] += 1
            
            # Update pitching players
            for _, player in pitching_data.iterrows():
                try:
                    team_abbr = str(player.get('Team', '')).strip()
                    if team_abbr in ['', '- - -', 'TOT']:
                        continue
                    
                    team_id = self._get_team_id(team_abbr)
                    if not team_id:
                        continue
                    
                    # Check if player exists
                    existing = self.supabase.table('players').select('*').eq('name', player.get('Name')).eq('team_id', team_id).execute()
                    
                    player_data = {
                        'name': str(player.get('Name', '')).strip(),
                        'team_id': team_id,
                        'position': 'Pitcher',
                        'age': int(player.get('Age', 0)) if pd.notna(player.get('Age')) else None,
                        'war': float(player.get('WAR', 0)) if pd.notna(player.get('WAR')) else 0.0,
                        'stats': {
                            'type': 'pitching',
                            'season': current_year,
                            'era': float(player.get('ERA', 0)) if pd.notna(player.get('ERA')) else 0.0,
                            'whip': float(player.get('WHIP', 0)) if pd.notna(player.get('WHIP')) else 0.0,
                            'fip': float(player.get('FIP', 0)) if pd.notna(player.get('FIP')) else 0.0,
                            'wins': int(player.get('W', 0)) if pd.notna(player.get('W')) else 0,
                            'saves': int(player.get('SV', 0)) if pd.notna(player.get('SV')) else 0,
                            'strikeouts': int(player.get('SO', 0)) if pd.notna(player.get('SO')) else 0,
                            'innings_pitched': float(player.get('IP', 0)) if pd.notna(player.get('IP')) else 0.0,
                            'games': int(player.get('G', 0)) if pd.notna(player.get('G')) else 0,
                            'team': team_abbr
                        }
                    }
                    
                    if existing.data:
                        # Update existing player
                        player_id = existing.data[0]['id']
                        self.supabase.table('players').delete().eq('id', player_id).execute()
                        self.supabase.table('players').insert(player_data).execute()
                        result['players_updated'] += 1
                    else:
                        # Insert new player
                        self.supabase.table('players').insert(player_data).execute()
                        result['new_players'] += 1
                        
                except Exception as e:
                    logger.error(f"Error updating pitching player {player.get('Name', 'Unknown')}: {e}")
                    result['errors'] += 1
            
            result['duration'] = (datetime.now() - start_time).total_seconds()
            
            # Update internal stats
            self.update_stats.update(result)
            
            logger.info(f"✅ Stats update complete: {result['players_updated']} updated, {result['new_players']} new in {result['duration']:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Error in current season stats update: {e}")
            result['errors'] += 1
        
        return result
    
    async def check_roster_moves(self) -> Dict[str, Any]:
        """
        Check for recent roster moves and transactions
        """
        logger.info("📋 Checking roster moves...")
        
        result = {
            'moves_detected': 0,
            'players_affected': [],
            'errors': 0
        }
        
        try:
            # For now, this is a placeholder - would require MLB transaction API
            # In a real implementation, this would check for:
            # - DFA (Designated for Assignment)
            # - Option to minors
            # - Trades
            # - Free agent signings
            # - Injury list moves
            
            logger.info("📋 Roster moves check complete (placeholder)")
            
        except Exception as e:
            logger.error(f"❌ Error checking roster moves: {e}")
            result['errors'] += 1
        
        return result
    
    async def update_prospect_rankings(self) -> Dict[str, Any]:
        """
        Update prospect rankings (weekly task)
        """
        logger.info("🌟 Updating prospect rankings...")
        
        result = {
            'prospects_updated': 0,
            'errors': 0
        }
        
        try:
            # Check if prospects table exists
            try:
                test_result = self.supabase.table('prospects').select('count').execute()
                logger.info("✅ Prospects table accessible")
            except Exception:
                logger.warning("⚠️  Prospects table not found - skipping prospect updates")
                return result
            
            # This would run the prospect seeding script
            # For now, it's a placeholder
            logger.info("🌟 Prospect rankings update complete (placeholder)")
            
        except Exception as e:
            logger.error(f"❌ Error updating prospect rankings: {e}")
            result['errors'] += 1
        
        return result
    
    async def run_daily_update(self) -> Dict[str, Any]:
        """
        Run comprehensive daily data update
        """
        logger.info("🚀 Starting daily data update...")
        start_time = datetime.now()
        
        overall_result = {
            'success': False,
            'start_time': start_time.isoformat(),
            'stats_update': None,
            'roster_moves': None,
            'total_duration': 0,
            'errors': 0
        }
        
        try:
            # Update current season stats
            overall_result['stats_update'] = await self.update_current_season_stats()
            
            # Check roster moves
            overall_result['roster_moves'] = await self.check_roster_moves()
            
            # Calculate totals
            overall_result['total_duration'] = (datetime.now() - start_time).total_seconds()
            overall_result['errors'] = (
                overall_result['stats_update'].get('errors', 0) +
                overall_result['roster_moves'].get('errors', 0)
            )
            
            overall_result['success'] = overall_result['errors'] == 0
            
            logger.info(f"✅ Daily update complete in {overall_result['total_duration']:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Daily update failed: {e}")
            overall_result['error'] = str(e)
        
        return overall_result

# Singleton instance
data_service = DataIngestionService()

if __name__ == "__main__":
    # Test the data ingestion service
    async def test_ingestion():
        logger.info("Testing data ingestion service...")
        results = await data_service.run_daily_update()
        print(json.dumps(results, indent=2))
    
    asyncio.run(test_ingestion())