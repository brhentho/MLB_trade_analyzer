#!/usr/bin/env python3
"""
Prospect Data Seeding Script for Baseball Trade AI
Seeds prospect rankings and data into Supabase database
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
from pybaseball import top_prospects, amateur_draft, amateur_draft_by_team
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
        logging.FileHandler('prospects_seed.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProspectSeeder:
    """
    Seeds prospect rankings and draft data for baseball trade analysis
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
            'prospects_inserted': 0,
            'prospects_updated': 0,
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
    
    def _estimate_future_value(self, ranking: int) -> int:
        """
        Estimate Future Value (FV) grade based on prospect ranking
        FV Scale: 20-80 (20=below average, 50=average, 80=elite)
        """
        if ranking <= 10:
            return random.randint(70, 80)  # Elite prospects
        elif ranking <= 25:
            return random.randint(60, 70)  # High-end prospects
        elif ranking <= 50:
            return random.randint(55, 65)  # Above-average prospects
        elif ranking <= 100:
            return random.randint(50, 60)  # Solid prospects
        elif ranking <= 200:
            return random.randint(45, 55)  # Average prospects
        else:
            return random.randint(40, 50)  # Below-average prospects
    
    def _estimate_eta(self, age: int, level: str = "unknown") -> int:
        """Estimate Expected Time of Arrival (ETA) year"""
        current_year = datetime.now().year
        
        if age <= 18:
            return current_year + random.randint(3, 5)
        elif age <= 20:
            return current_year + random.randint(2, 4)
        elif age <= 22:
            return current_year + random.randint(1, 3)
        elif age <= 24:
            return current_year + random.randint(1, 2)
        else:
            return current_year + 1
    
    def _determine_risk_level(self, age: int, future_value: int) -> str:
        """Determine risk level based on age and FV"""
        if age >= 24:
            return "low"
        elif age <= 19 and future_value >= 60:
            return "high"
        elif future_value >= 65:
            return "medium"
        else:
            return random.choice(["low", "medium"])
    
    async def seed_top_prospects(self) -> Dict[str, Any]:
        """
        Seed top prospect rankings data
        """
        logger.info("🌟 Starting to seed top prospects...")
        start_time = datetime.now()
        
        result = {
            'prospects_processed': 0,
            'errors': [],
            'duration': 0
        }
        
        try:
            # Get top prospects data
            logger.info("📊 Fetching top prospects rankings...")
            prospects_data = top_prospects()
            await self._rate_limit()
            
            logger.info(f"⚾ Processing {len(prospects_data)} prospect records...")
            
            for idx, prospect in tqdm(prospects_data.iterrows(), total=len(prospects_data), desc="Prospects"):
                try:
                    # Extract prospect data
                    name = str(prospect.get('Name', '')).strip()
                    team_abbr = str(prospect.get('Team', '')).strip()
                    position = str(prospect.get('POS', 'N/A')).strip()
                    age = int(prospect.get('Age', 0)) if pd.notna(prospect.get('Age')) else None
                    
                    if not name or team_abbr in ['', '- - -', 'TOT']:
                        continue
                    
                    # Get team ID
                    team_id = self._get_team_id(team_abbr)
                    if not team_id:
                        logger.warning(f"⚠️  Unknown team: {team_abbr} for prospect {name}")
                        continue
                    
                    # Calculate prospect metrics
                    ranking = idx + 1  # Position in top prospects list
                    future_value = self._estimate_future_value(ranking)
                    eta = self._estimate_eta(age) if age else datetime.now().year + 2
                    risk_level = self._determine_risk_level(age, future_value) if age else "medium"
                    
                    # Create prospect data
                    prospect_data = {
                        'name': name,
                        'team_id': team_id,
                        'position': position[:10],  # Limit to 10 chars
                        'age': age,
                        'ranking': ranking,
                        'future_value': future_value,
                        'eta': eta,
                        'risk_level': risk_level,
                        'scouting_report': {
                            'source': 'pybaseball_top_prospects',
                            'ranking_date': datetime.now().isoformat(),
                            'team': team_abbr,
                            'notes': f"Ranked #{ranking} prospect overall"
                        }
                    }
                    
                    # Insert prospect
                    await self._upsert_prospect(prospect_data)
                    result['prospects_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing prospect {prospect.get('Name', 'Unknown')}: {e}"
                    logger.error(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
                    continue
            
            result['duration'] = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Completed top prospects: {result['prospects_processed']} processed in {result['duration']:.1f}s")
            
        except Exception as e:
            error_msg = f"Error fetching top prospects: {e}"
            logger.error(f"❌ {error_msg}")
            result['errors'].append(error_msg)
        
        return result
    
    async def seed_draft_prospects(self, years: List[int] = None) -> Dict[str, Any]:
        """
        Seed recent draft data for prospects
        """
        if years is None:
            years = [2022, 2023, 2024]
        
        logger.info(f"🎯 Starting to seed draft prospects for years: {years}...")
        start_time = datetime.now()
        
        result = {
            'years_processed': 0,
            'prospects_processed': 0,
            'errors': [],
            'duration': 0
        }
        
        for year in years:
            try:
                logger.info(f"📊 Fetching {year} draft data...")
                draft_data = amateur_draft(year)
                await self._rate_limit()
                
                logger.info(f"⚾ Processing {len(draft_data)} draft records for {year}...")
                
                for idx, draftee in tqdm(draft_data.iterrows(), total=len(draft_data), desc=f"{year} Draft"):
                    try:
                        # Extract draft data
                        name = str(draftee.get('Name', '')).strip()
                        team_abbr = str(draftee.get('Team', '')).strip()
                        position = str(draftee.get('POS', 'N/A')).strip()
                        round_num = int(draftee.get('Round', 0)) if pd.notna(draftee.get('Round')) else None
                        overall_pick = int(draftee.get('Overall', 0)) if pd.notna(draftee.get('Overall')) else None
                        
                        if not name or team_abbr in ['', '- - -', 'TOT']:
                            continue
                        
                        # Only process first 10 rounds for manageable dataset
                        if round_num and round_num > 10:
                            continue
                        
                        # Get team ID
                        team_id = self._get_team_id(team_abbr)
                        if not team_id:
                            logger.warning(f"⚠️  Unknown team: {team_abbr} for draftee {name}")
                            continue
                        
                        # Calculate prospect metrics based on draft position
                        ranking = overall_pick if overall_pick else (round_num * 30 if round_num else 999)
                        age = 18 + random.randint(0, 3)  # Draft age range
                        future_value = self._estimate_future_value(ranking)
                        eta = self._estimate_eta(age)
                        risk_level = self._determine_risk_level(age, future_value)
                        
                        # Create prospect data
                        prospect_data = {
                            'name': name,
                            'team_id': team_id,
                            'position': position[:10],
                            'age': age,
                            'ranking': ranking,
                            'future_value': future_value,
                            'eta': eta,
                            'risk_level': risk_level,
                            'scouting_report': {
                                'source': f'{year}_amateur_draft',
                                'draft_year': year,
                                'draft_round': round_num,
                                'overall_pick': overall_pick,
                                'team': team_abbr,
                                'notes': f"Drafted in round {round_num}, pick {overall_pick} in {year}"
                            }
                        }
                        
                        # Insert prospect
                        await self._upsert_prospect(prospect_data)
                        result['prospects_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing {year} draftee {draftee.get('Name', 'Unknown')}: {e}"
                        logger.error(f"❌ {error_msg}")
                        result['errors'].append(error_msg)
                        continue
                
                result['years_processed'] += 1
                logger.info(f"✅ Completed {year} draft data")
                
            except Exception as e:
                error_msg = f"Error processing {year} draft: {e}"
                logger.error(f"❌ {error_msg}")
                result['errors'].append(error_msg)
        
        result['duration'] = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Completed draft prospects: {result['prospects_processed']} processed in {result['duration']:.1f}s")
        
        return result
    
    async def _upsert_prospect(self, prospect_data: Dict[str, Any]) -> None:
        """Insert or update prospect in database"""
        try:
            # Check if prospect exists (by name and team)
            existing = self.supabase.table('prospects').select('*').eq('name', prospect_data['name']).eq('team_id', prospect_data['team_id']).execute()
            
            if existing.data:
                # Prospect exists - use delete/insert approach due to potential trigger issues
                existing_prospect = existing.data[0]
                prospect_id = existing_prospect['id']
                
                # Prepare updated data (remove ID and timestamps)
                updated_data = prospect_data.copy()
                updated_data.pop('id', None)
                updated_data.pop('created_at', None)
                updated_data.pop('updated_at', None)
                
                # Delete existing and insert new
                self.supabase.table('prospects').delete().eq('id', prospect_id).execute()
                self.supabase.table('prospects').insert(updated_data).execute()
                self.stats['prospects_updated'] += 1
            else:
                # Insert new prospect
                self.supabase.table('prospects').insert(prospect_data).execute()
                self.stats['prospects_inserted'] += 1
                
        except Exception as e:
            logger.error(f"❌ Error upserting prospect {prospect_data.get('name', 'Unknown')}: {e}")
            raise
    
    async def run_prospect_seeding(self) -> Dict[str, Any]:
        """
        Run the complete prospect seeding process
        """
        logger.info("🚀 Starting prospect data seeding...")
        self.stats['start_time'] = datetime.now()
        
        results = {
            'top_prospects': None,
            'draft_prospects': None,
            'success': False,
            'total_prospects': 0
        }
        
        try:
            # Seed top prospects
            results['top_prospects'] = await self.seed_top_prospects()
            
            # Seed draft prospects
            results['draft_prospects'] = await self.seed_draft_prospects([2022, 2023, 2024])
            
            # Calculate totals
            results['total_prospects'] = (
                results['top_prospects']['prospects_processed'] + 
                results['draft_prospects']['prospects_processed']
            )
            
            results['success'] = True
            
        except Exception as e:
            logger.error(f"❌ Failed prospect seeding: {e}")
            results['error'] = str(e)
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Final summary
        logger.info("=" * 60)
        logger.info("🏆 PROSPECT DATA SEEDING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"⏱️  Total Duration: {duration/60:.1f} minutes")
        logger.info(f"🌟 Top Prospects: {results['top_prospects']['prospects_processed'] if results['top_prospects'] else 0}")
        logger.info(f"🎯 Draft Prospects: {results['draft_prospects']['prospects_processed'] if results['draft_prospects'] else 0}")
        logger.info(f"👥 Total Prospects: {results['total_prospects']}")
        logger.info(f"🔄 Prospects Updated: {self.stats['prospects_updated']}")
        logger.info(f"➕ Prospects Inserted: {self.stats['prospects_inserted']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("=" * 60)
        
        return results

async def main():
    """Main function"""
    print("🌟 Baseball Trade AI - Prospect Data Seeder")
    print("=" * 50)
    
    try:
        # Check if prospects table exists
        seeder = ProspectSeeder()
        
        # Test prospects table
        test_result = seeder.supabase.table('prospects').select('count').execute()
        logger.info(f"✅ Prospects table accessible (current count: {len(test_result.data)})")
        
        # Run the seeding process
        result = await seeder.run_prospect_seeding()
        
        # Print final results
        if result['success']:
            print("✅ Prospect seeding completed successfully!")
        else:
            print("⚠️  Prospect seeding completed with errors. Check the logs.")
        
        print(f"📊 Results saved to: prospects_seed.log")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        print(f"❌ Fatal error: {e}")
        
        if "Could not find the table 'public.prospects'" in str(e):
            print("\n🔧 MANUAL STEP REQUIRED:")
            print("The prospects table needs to be created. Please:")
            print("1. Go to your Supabase dashboard")
            print("2. Navigate to SQL Editor")
            print("3. Run the SQL script in 'create_prospects_table.sql'")
            print("4. Then run this script again")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)