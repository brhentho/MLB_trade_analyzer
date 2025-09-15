#!/usr/bin/env python3
"""
Historical Data Seeding Script for Baseball Trade AI
Seeds 3 years of MLB data (2022-2024) into Supabase database
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import json

import pandas as pd
import pybaseball as pb
from pybaseball import batting_stats, pitching_stats, playerid_lookup
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm
import time
import random

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('historical_seed.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HistoricalDataSeeder:
    """
    Seeds historical MLB data for the past 3 years
    """
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("❌ Supabase credentials not found. Please check your .env file")
        
        if supabase_url == 'https://your-project-id.supabase.co':
            raise ValueError("❌ Please update your .env file with actual Supabase credentials")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Rate limiting - be respectful to data sources
        self.request_delay = float(os.getenv('DATA_UPDATE_DELAY', '1.0'))
        
        # Cache for MLB team mappings
        self._team_cache = {}
        self._load_team_mappings()
        
        # Track progress
        self.stats = {
            'seasons_processed': 0,
            'players_inserted': 0,
            'players_updated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _load_team_mappings(self) -> None:
        """Load team mappings from Supabase"""
        try:
            response = self.supabase.table('teams').select('*').execute()
            
            if not response.data:
                logger.error("❌ No teams found in database. Please run the migration files first!")
                raise ValueError("Teams table is empty. Run migration files first.")
            
            self._team_cache = {}
            
            # Create mapping by team abbreviation and key
            for team in response.data:
                self._team_cache[team['abbreviation']] = team
                self._team_cache[team['team_key']] = team
                # Also handle common abbreviation variations
                self._team_cache[team['abbreviation'].upper()] = team
            
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
            
            logger.info(f"✅ Loaded {len(response.data)} team mappings")
            
        except Exception as e:
            logger.error(f"❌ Failed to load team mappings: {e}")
            raise
    
    def _get_team_id(self, team_identifier: str) -> Optional[int]:
        """Get team ID from team key or abbreviation"""
        if not team_identifier:
            return None
            
        team_data = self._team_cache.get(team_identifier) or self._team_cache.get(team_identifier.upper())
        return team_data['id'] if team_data else None
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        await asyncio.sleep(self.request_delay + random.uniform(0, 0.5))
    
    def _normalize_team_name(self, team_name: str) -> str:
        """Normalize team names from different sources"""
        if not team_name:
            return team_name
            
        # Common variations in baseball data
        team_mapping = {
            'Angels': 'LAA',
            'Astros': 'HOU', 
            'Athletics': 'OAK',
            'Blue Jays': 'TOR',
            'Braves': 'ATL',
            'Brewers': 'MIL',
            'Cardinals': 'STL',
            'Cubs': 'CHC',
            'Diamondbacks': 'ARI',
            'Dodgers': 'LAD',
            'Giants': 'SF',
            'Guardians': 'CLE',
            'Indians': 'CLE',  # Historical
            'Mariners': 'SEA',
            'Marlins': 'MIA',
            'Mets': 'NYM',
            'Nationals': 'WSH',
            'Orioles': 'BAL',
            'Padres': 'SD',
            'Phillies': 'PHI',
            'Pirates': 'PIT',
            'Rangers': 'TEX',
            'Rays': 'TB',
            'Red Sox': 'BOS',
            'Reds': 'CIN',
            'Rockies': 'COL',
            'Royals': 'KC',
            'Tigers': 'DET',
            'Twins': 'MIN',
            'White Sox': 'CWS',
            'Yankees': 'NYY'
        }
        
        return team_mapping.get(team_name, team_name)
    
    async def seed_season_data(self, season: int) -> Dict[str, Any]:
        """
        Seed data for a specific season
        """
        logger.info(f"🏟️  Starting to seed data for {season} season...")
        season_start = datetime.now()
        
        season_stats = {
            'season': season,
            'batting_players': 0,
            'pitching_players': 0,
            'total_players': 0,
            'errors': [],
            'duration': 0
        }
        
        try:
            # Get batting stats for the season
            logger.info(f"📊 Fetching batting statistics for {season}...")
            batting_data = batting_stats(season)
            await self._rate_limit()
            
            logger.info(f"📊 Fetching pitching statistics for {season}...")
            pitching_data = pitching_stats(season)
            await self._rate_limit()
            
            # Process batting data
            logger.info(f"⚾ Processing {len(batting_data)} batting records...")
            batting_count = await self._process_batting_data(batting_data, season)
            season_stats['batting_players'] = batting_count
            
            # Process pitching data
            logger.info(f"⚾ Processing {len(pitching_data)} pitching records...")
            pitching_count = await self._process_pitching_data(pitching_data, season)
            season_stats['pitching_players'] = pitching_count
            
            season_stats['total_players'] = batting_count + pitching_count
            season_stats['duration'] = (datetime.now() - season_start).total_seconds()
            
            logger.info(f"✅ Completed {season}: {season_stats['total_players']} players processed in {season_stats['duration']:.1f}s")
            
        except Exception as e:
            error_msg = f"Error processing {season}: {e}"
            logger.error(f"❌ {error_msg}")
            season_stats['errors'].append(error_msg)
            self.stats['errors'] += 1
        
        return season_stats
    
    async def _process_batting_data(self, batting_data: pd.DataFrame, season: int) -> int:
        """Process batting statistics data"""
        count = 0
        
        for _, player in tqdm(batting_data.iterrows(), total=len(batting_data), desc="Batting"):
            try:
                team_abbr = str(player.get('Team', '')).strip()
                if team_abbr in ['', '- - -', 'TOT']:  # Skip invalid teams
                    continue
                
                # Normalize team abbreviation
                team_abbr = self._normalize_team_name(team_abbr)
                team_id = self._get_team_id(team_abbr)
                
                if not team_id:
                    logger.warning(f"⚠️  Unknown team: {team_abbr} for player {player.get('Name', 'Unknown')}")
                    continue
                
                # Create player data
                player_data = {
                    'name': str(player.get('Name', '')).strip(),
                    'team_id': team_id,
                    'position': 'Batter',  # Batting data doesn't specify position
                    'age': int(player.get('Age', 0)) if pd.notna(player.get('Age')) else None,
                    'war': float(player.get('WAR', 0)) if pd.notna(player.get('WAR')) else 0.0,
                    'stats': {
                        'type': 'batting',
                        'season': season,
                        'games': int(player.get('G', 0)) if pd.notna(player.get('G')) else 0,
                        'plate_appearances': int(player.get('PA', 0)) if pd.notna(player.get('PA')) else 0,
                        'at_bats': int(player.get('AB', 0)) if pd.notna(player.get('AB')) else 0,
                        'runs': int(player.get('R', 0)) if pd.notna(player.get('R')) else 0,
                        'hits': int(player.get('H', 0)) if pd.notna(player.get('H')) else 0,
                        'doubles': int(player.get('2B', 0)) if pd.notna(player.get('2B')) else 0,
                        'triples': int(player.get('3B', 0)) if pd.notna(player.get('3B')) else 0,
                        'home_runs': int(player.get('HR', 0)) if pd.notna(player.get('HR')) else 0,
                        'rbi': int(player.get('RBI', 0)) if pd.notna(player.get('RBI')) else 0,
                        'stolen_bases': int(player.get('SB', 0)) if pd.notna(player.get('SB')) else 0,
                        'caught_stealing': int(player.get('CS', 0)) if pd.notna(player.get('CS')) else 0,
                        'walks': int(player.get('BB', 0)) if pd.notna(player.get('BB')) else 0,
                        'strikeouts': int(player.get('SO', 0)) if pd.notna(player.get('SO')) else 0,
                        'avg': float(player.get('AVG', 0)) if pd.notna(player.get('AVG')) else 0.0,
                        'obp': float(player.get('OBP', 0)) if pd.notna(player.get('OBP')) else 0.0,
                        'slg': float(player.get('SLG', 0)) if pd.notna(player.get('SLG')) else 0.0,
                        'ops': float(player.get('OPS', 0)) if pd.notna(player.get('OPS')) else 0.0,
                        'ops_plus': int(player.get('OPS+', 100)) if pd.notna(player.get('OPS+')) else 100,
                        'team': team_abbr
                    },
                }
                
                # Insert or update player
                await self._upsert_player(player_data)
                count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing batting player {player.get('Name', 'Unknown')}: {e}")
                continue
        
        return count
    
    async def _process_pitching_data(self, pitching_data: pd.DataFrame, season: int) -> int:
        """Process pitching statistics data"""
        count = 0
        
        for _, player in tqdm(pitching_data.iterrows(), total=len(pitching_data), desc="Pitching"):
            try:
                team_abbr = str(player.get('Team', '')).strip()
                if team_abbr in ['', '- - -', 'TOT']:  # Skip invalid teams
                    continue
                
                # Normalize team abbreviation
                team_abbr = self._normalize_team_name(team_abbr)
                team_id = self._get_team_id(team_abbr)
                
                if not team_id:
                    logger.warning(f"⚠️  Unknown team: {team_abbr} for player {player.get('Name', 'Unknown')}")
                    continue
                
                # Create player data
                player_data = {
                    'name': str(player.get('Name', '')).strip(),
                    'team_id': team_id,
                    'position': 'Pitcher',
                    'age': int(player.get('Age', 0)) if pd.notna(player.get('Age')) else None,
                    'war': float(player.get('WAR', 0)) if pd.notna(player.get('WAR')) else 0.0,
                    'stats': {
                        'type': 'pitching',
                        'season': season,
                        'wins': int(player.get('W', 0)) if pd.notna(player.get('W')) else 0,
                        'losses': int(player.get('L', 0)) if pd.notna(player.get('L')) else 0,
                        'saves': int(player.get('SV', 0)) if pd.notna(player.get('SV')) else 0,
                        'games': int(player.get('G', 0)) if pd.notna(player.get('G')) else 0,
                        'games_started': int(player.get('GS', 0)) if pd.notna(player.get('GS')) else 0,
                        'complete_games': int(player.get('CG', 0)) if pd.notna(player.get('CG')) else 0,
                        'shutouts': int(player.get('SHO', 0)) if pd.notna(player.get('SHO')) else 0,
                        'innings_pitched': float(player.get('IP', 0)) if pd.notna(player.get('IP')) else 0.0,
                        'hits_allowed': int(player.get('H', 0)) if pd.notna(player.get('H')) else 0,
                        'runs_allowed': int(player.get('R', 0)) if pd.notna(player.get('R')) else 0,
                        'earned_runs': int(player.get('ER', 0)) if pd.notna(player.get('ER')) else 0,
                        'home_runs_allowed': int(player.get('HR', 0)) if pd.notna(player.get('HR')) else 0,
                        'walks_allowed': int(player.get('BB', 0)) if pd.notna(player.get('BB')) else 0,
                        'strikeouts': int(player.get('SO', 0)) if pd.notna(player.get('SO')) else 0,
                        'era': float(player.get('ERA', 0)) if pd.notna(player.get('ERA')) else 0.0,
                        'whip': float(player.get('WHIP', 0)) if pd.notna(player.get('WHIP')) else 0.0,
                        'fip': float(player.get('FIP', 0)) if pd.notna(player.get('FIP')) else 0.0,
                        'era_plus': int(player.get('ERA+', 100)) if pd.notna(player.get('ERA+')) else 100,
                        'team': team_abbr
                    },
                }
                
                # Insert or update player
                await self._upsert_player(player_data)
                count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing pitching player {player.get('Name', 'Unknown')}: {e}")
                continue
        
        return count
    
    async def _upsert_player(self, player_data: Dict[str, Any]) -> None:
        """Insert or update player in database"""
        try:
            # Check if player exists (by name and team)
            existing = self.supabase.table('players').select('*').eq('name', player_data['name']).eq('team_id', player_data['team_id']).execute()
            
            if existing.data:
                # Player exists - use delete/insert approach due to trigger issues
                existing_player = existing.data[0]
                player_id = existing_player['id']
                
                # Prepare updated data (remove ID and timestamps)
                updated_data = player_data.copy()
                updated_data.pop('id', None)
                updated_data.pop('created_at', None)
                updated_data.pop('last_updated', None)
                
                # Delete existing and insert new
                self.supabase.table('players').delete().eq('id', player_id).execute()
                self.supabase.table('players').insert(updated_data).execute()
                self.stats['players_updated'] += 1
            else:
                # Insert new player
                self.supabase.table('players').insert(player_data).execute()
                self.stats['players_inserted'] += 1
                
        except Exception as e:
            logger.error(f"❌ Error upserting player {player_data.get('name', 'Unknown')}: {e}")
            raise
    
    async def run_historical_seed(self, seasons: List[int] = None) -> Dict[str, Any]:
        """
        Run the complete historical data seeding process
        """
        if seasons is None:
            seasons = [2022, 2023, 2024]
        
        logger.info(f"🚀 Starting historical data seeding for seasons: {seasons}")
        self.stats['start_time'] = datetime.now()
        
        season_results = []
        
        for season in seasons:
            try:
                season_result = await self.seed_season_data(season)
                season_results.append(season_result)
                self.stats['seasons_processed'] += 1
                
                # Brief pause between seasons
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Failed to process season {season}: {e}")
                self.stats['errors'] += 1
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Final summary
        logger.info("="*60)
        logger.info("🏆 HISTORICAL DATA SEEDING COMPLETE!")
        logger.info("="*60)
        logger.info(f"⏱️  Total Duration: {duration/60:.1f} minutes")
        logger.info(f"📊 Seasons Processed: {self.stats['seasons_processed']}/{len(seasons)}")
        logger.info(f"👥 Players Inserted: {self.stats['players_inserted']}")
        logger.info(f"🔄 Players Updated: {self.stats['players_updated']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("="*60)
        
        return {
            'stats': self.stats,
            'seasons': season_results,
            'duration_minutes': duration / 60,
            'success': self.stats['errors'] == 0
        }

async def main():
    """Main function"""
    print("🏟️  Baseball Trade AI - Historical Data Seeder")
    print("=" * 50)
    
    try:
        # Create seeder instance
        seeder = HistoricalDataSeeder()
        
        # Run the seeding process
        result = await seeder.run_historical_seed([2022, 2023, 2024])
        
        # Print final results
        if result['success']:
            print("✅ Historical seeding completed successfully!")
        else:
            print("⚠️  Historical seeding completed with errors. Check the logs.")
        
        print(f"📊 Results saved to: historical_seed.log")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        print(f"❌ Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)