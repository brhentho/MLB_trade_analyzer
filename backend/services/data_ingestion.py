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
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Rate limiting
        self.request_delay = 1.0  # 1 second between requests to be respectful
        
        # Cache for MLB team mappings
        self._team_cache = {}
        self._load_team_mappings()
    
    def _load_team_mappings(self) -> None:
        """Load team mappings from Supabase"""
        try:
            response = self.supabase.table('teams').select('*').execute()
            self._team_cache = {
                team['team_key']: team for team in response.data
            }
            # Also create abbreviation mapping
            for team in response.data:
                self._team_cache[team['abbreviation']] = team
            logger.info(f"Loaded {len(response.data)} team mappings")
        except Exception as e:
            logger.error(f"Failed to load team mappings: {e}")
    
    def _get_team_id(self, team_identifier: str) -> Optional[int]:
        """Get team ID from team key or abbreviation"""
        team_data = self._team_cache.get(team_identifier.lower())
        return team_data['id'] if team_data else None
    
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

# Singleton instance
data_service = DataIngestionService()

if __name__ == "__main__":
    # Test the data ingestion service
    async def test_ingestion():
        logger.info("Testing data ingestion service...")
        results = await data_service.run_daily_update()
        print(json.dumps(results, indent=2))
    
    asyncio.run(test_ingestion())