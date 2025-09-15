#!/usr/bin/env python3
"""
Historical Prospect Database Seeding Script
Seeds comprehensive historical prospect data (2020-2024) for Baseball Trade AI
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Add backend to path
sys.path.append('.')
sys.path.append('./backend')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_team_mapping() -> Dict[str, int]:
    """Load team mapping from database"""
    try:
        from backend.services.supabase_service import supabase_service
        result = supabase_service.supabase.table('teams').select('id, team_key, abbreviation').execute()
        
        # Create mapping for both team_key and abbreviation
        mapping = {}
        for team in result.data:
            mapping[team['team_key']] = team['id']
            mapping[team['abbreviation']] = team['id']
        
        return mapping
    except Exception as e:
        logger.error(f"Error loading team mapping: {e}")
        return {}

# Historical Top Prospects Database (2020-2024)
HISTORICAL_PROSPECTS = [
    # 2024 Top Prospects
    {"name": "Jackson Chourio", "team": "brewers", "position": "OF", "age": 20, "ranking": 1, "future_value": 65, "eta": 2024, "year": 2024},
    {"name": "Junior Caminero", "team": "rays", "position": "3B", "age": 20, "ranking": 2, "future_value": 65, "eta": 2025, "year": 2024},
    {"name": "Wyatt Langford", "team": "rangers", "position": "OF", "age": 22, "ranking": 3, "future_value": 60, "eta": 2024, "year": 2024},
    {"name": "Paul Skenes", "team": "pirates", "position": "RHP", "age": 22, "ranking": 4, "future_value": 70, "eta": 2024, "year": 2024},
    {"name": "Coby Mayo", "team": "orioles", "position": "3B", "age": 22, "ranking": 5, "future_value": 60, "eta": 2024, "year": 2024},
    {"name": "Roman Anthony", "team": "red_sox", "position": "OF", "age": 20, "ranking": 6, "future_value": 60, "eta": 2025, "year": 2024},
    {"name": "Samuel Basallo", "team": "orioles", "position": "C", "age": 20, "ranking": 7, "future_value": 60, "eta": 2025, "year": 2024},
    {"name": "Marcelo Mayer", "team": "red_sox", "position": "SS", "age": 22, "ranking": 8, "future_value": 60, "eta": 2025, "year": 2024},
    {"name": "Walker Jenkins", "team": "twins", "position": "OF", "age": 19, "ranking": 9, "future_value": 60, "eta": 2026, "year": 2024},
    {"name": "Druw Jones", "team": "diamondbacks", "position": "OF", "age": 21, "ranking": 10, "future_value": 60, "eta": 2025, "year": 2024},
    
    # Additional 2024 Top 50
    {"name": "Termarr Johnson", "team": "pirates", "position": "2B", "age": 20, "ranking": 11, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Jace Jung", "team": "tigers", "position": "3B", "age": 23, "ranking": 12, "future_value": 55, "eta": 2024, "year": 2024},
    {"name": "Brady House", "team": "nationals", "position": "3B", "age": 22, "ranking": 13, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Kendall George", "team": "phillies", "position": "OF", "age": 20, "ranking": 14, "future_value": 55, "eta": 2026, "year": 2024},
    {"name": "Jacob Wilson", "team": "athletics", "position": "SS", "age": 23, "ranking": 15, "future_value": 55, "eta": 2024, "year": 2024},
    {"name": "Jackson Holliday", "team": "orioles", "position": "2B", "age": 20, "ranking": 16, "future_value": 65, "eta": 2024, "year": 2024},
    {"name": "Jasson Dominguez", "team": "yankees", "position": "OF", "age": 21, "ranking": 17, "future_value": 60, "eta": 2024, "year": 2024},
    {"name": "Jordan Lawlar", "team": "diamondbacks", "position": "SS", "age": 22, "ranking": 18, "future_value": 60, "eta": 2024, "year": 2024},
    {"name": "Jackson Merrill", "team": "padres", "position": "SS", "age": 21, "ranking": 19, "future_value": 55, "eta": 2024, "year": 2024},
    {"name": "Max Clark", "team": "tigers", "position": "OF", "age": 20, "ranking": 20, "future_value": 55, "eta": 2025, "year": 2024},
    
    # 2023 Historical Prospects
    {"name": "Corbin Carroll", "team": "diamondbacks", "position": "OF", "age": 23, "ranking": 1, "future_value": 70, "eta": 2023, "year": 2023},
    {"name": "Grayson Rodriguez", "team": "orioles", "position": "RHP", "age": 23, "ranking": 2, "future_value": 65, "eta": 2023, "year": 2023},
    {"name": "Gunnar Henderson", "team": "orioles", "position": "SS", "age": 22, "ranking": 3, "future_value": 65, "eta": 2023, "year": 2023},
    {"name": "Anthony Volpe", "team": "yankees", "position": "SS", "age": 22, "ranking": 4, "future_value": 60, "eta": 2023, "year": 2023},
    {"name": "Francisco Alvarez", "team": "mets", "position": "C", "age": 21, "ranking": 5, "future_value": 65, "eta": 2023, "year": 2023},
    {"name": "Elly De La Cruz", "team": "reds", "position": "SS", "age": 21, "ranking": 6, "future_value": 60, "eta": 2023, "year": 2023},
    {"name": "Evan Carter", "team": "rangers", "position": "OF", "age": 21, "ranking": 7, "future_value": 55, "eta": 2023, "year": 2023},
    {"name": "Jordan Walker", "team": "cardinals", "position": "OF", "age": 21, "ranking": 8, "future_value": 60, "eta": 2023, "year": 2023},
    {"name": "Eury Perez", "team": "marlins", "position": "RHP", "age": 20, "ranking": 9, "future_value": 60, "eta": 2023, "year": 2023},
    {"name": "Termarr Johnson", "team": "pirates", "position": "2B", "age": 19, "ranking": 10, "future_value": 55, "eta": 2024, "year": 2023},
    
    # 2022 Historical Prospects  
    {"name": "Adley Rutschman", "team": "orioles", "position": "C", "age": 24, "ranking": 1, "future_value": 70, "eta": 2022, "year": 2022},
    {"name": "Bobby Witt Jr.", "team": "royals", "position": "SS", "age": 22, "ranking": 2, "future_value": 65, "eta": 2022, "year": 2022},
    {"name": "Julio Rodriguez", "team": "mariners", "position": "OF", "age": 21, "ranking": 3, "future_value": 65, "eta": 2022, "year": 2022},
    {"name": "Riley Greene", "team": "tigers", "position": "OF", "age": 21, "ranking": 4, "future_value": 60, "eta": 2022, "year": 2022},
    {"name": "Spencer Torkelson", "team": "tigers", "position": "1B", "age": 22, "ranking": 5, "future_value": 60, "eta": 2022, "year": 2022},
    {"name": "Gabriel Moreno", "team": "blue_jays", "position": "C", "age": 22, "ranking": 6, "future_value": 55, "eta": 2022, "year": 2022},
    {"name": "Oneil Cruz", "team": "pirates", "position": "SS", "age": 23, "ranking": 7, "future_value": 55, "eta": 2022, "year": 2022},
    {"name": "George Kirby", "team": "mariners", "position": "RHP", "age": 24, "ranking": 8, "future_value": 55, "eta": 2022, "year": 2022},
    {"name": "Shane Baz", "team": "rays", "position": "RHP", "age": 23, "ranking": 9, "future_value": 55, "eta": 2022, "year": 2022},
    {"name": "Matt Brash", "team": "mariners", "position": "RHP", "age": 24, "ranking": 10, "future_value": 50, "eta": 2022, "year": 2022},
    
    # 2021 Historical Prospects
    {"name": "Wander Franco", "team": "rays", "position": "SS", "age": 20, "ranking": 1, "future_value": 70, "eta": 2021, "year": 2021},
    {"name": "Jarred Kelenic", "team": "mariners", "position": "OF", "age": 22, "ranking": 2, "future_value": 60, "eta": 2021, "year": 2021},
    {"name": "Casey Mize", "team": "tigers", "position": "RHP", "age": 24, "ranking": 3, "future_value": 55, "eta": 2021, "year": 2021},
    {"name": "Ian Anderson", "team": "braves", "position": "RHP", "age": 23, "ranking": 4, "future_value": 55, "eta": 2021, "year": 2021},
    {"name": "Ke'Bryan Hayes", "team": "pirates", "position": "3B", "age": 24, "ranking": 5, "future_value": 55, "eta": 2021, "year": 2021},
    {"name": "Randy Arozarena", "team": "rays", "position": "OF", "age": 26, "ranking": 6, "future_value": 55, "eta": 2021, "year": 2021},
    {"name": "Dylan Carlson", "team": "cardinals", "position": "OF", "age": 22, "ranking": 7, "future_value": 55, "eta": 2021, "year": 2021},
    {"name": "Sixto Sanchez", "team": "marlins", "position": "RHP", "age": 23, "ranking": 8, "future_value": 60, "eta": 2021, "year": 2021},
    {"name": "Cristian Pache", "team": "braves", "position": "OF", "age": 22, "ranking": 9, "future_value": 55, "eta": 2021, "year": 2021},
    {"name": "MacKenzie Gore", "team": "padres", "position": "LHP", "age": 22, "ranking": 10, "future_value": 55, "eta": 2021, "year": 2021},
    
    # 2020 Historical Prospects
    {"name": "Luis Robert", "team": "white_sox", "position": "OF", "age": 23, "ranking": 1, "future_value": 65, "eta": 2020, "year": 2020},
    {"name": "Gavin Lux", "team": "dodgers", "position": "2B", "age": 22, "ranking": 2, "future_value": 55, "eta": 2020, "year": 2020},
    {"name": "Alex Kirilloff", "team": "twins", "position": "OF", "age": 22, "ranking": 3, "future_value": 55, "eta": 2020, "year": 2020},
    {"name": "Jo Adell", "team": "angels", "position": "OF", "age": 21, "ranking": 4, "future_value": 55, "eta": 2020, "year": 2020},
    {"name": "Carter Kieboom", "team": "nationals", "position": "SS", "age": 22, "ranking": 5, "future_value": 55, "eta": 2020, "year": 2020},
    {"name": "Dylan Cease", "team": "white_sox", "position": "RHP", "age": 24, "ranking": 6, "future_value": 50, "eta": 2020, "year": 2020},
    {"name": "Nate Pearson", "team": "blue_jays", "position": "RHP", "age": 24, "ranking": 7, "future_value": 55, "eta": 2020, "year": 2020},
    {"name": "Jesus Luzardo", "team": "athletics", "position": "LHP", "age": 22, "ranking": 8, "future_value": 55, "eta": 2020, "year": 2020},
    {"name": "Dustin May", "team": "dodgers", "position": "RHP", "age": 22, "ranking": 9, "future_value": 50, "eta": 2020, "year": 2020},
    {"name": "Brendan McKay", "team": "rays", "position": "LHP", "age": 24, "ranking": 10, "future_value": 50, "eta": 2020, "year": 2020},
]

# Add more prospect depth for each team
TEAM_SPECIFIC_PROSPECTS = [
    # Yankees prospects
    {"name": "Spencer Jones", "team": "yankees", "position": "OF", "age": 22, "ranking": 35, "future_value": 50, "eta": 2025, "year": 2024},
    {"name": "Drew Thorpe", "team": "yankees", "position": "RHP", "age": 23, "ranking": 45, "future_value": 45, "eta": 2024, "year": 2024},
    {"name": "Chase Hampton", "team": "yankees", "position": "LHP", "age": 21, "ranking": 55, "future_value": 45, "eta": 2025, "year": 2024},
    
    # Red Sox prospects
    {"name": "Kristian Campbell", "team": "red_sox", "position": "2B", "age": 22, "ranking": 25, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Kyle Teel", "team": "red_sox", "position": "C", "age": 22, "ranking": 30, "future_value": 50, "eta": 2025, "year": 2024},
    {"name": "Miguel Bleis", "team": "red_sox", "position": "OF", "age": 20, "ranking": 40, "future_value": 50, "eta": 2026, "year": 2024},
    
    # Orioles prospects
    {"name": "Heston Kjerstad", "team": "orioles", "position": "OF", "age": 25, "ranking": 28, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Dylan Beavers", "team": "orioles", "position": "OF", "age": 23, "ranking": 42, "future_value": 45, "eta": 2025, "year": 2024},
    {"name": "Connor Norby", "team": "orioles", "position": "2B", "age": 24, "ranking": 48, "future_value": 45, "eta": 2024, "year": 2024},
    
    # Blue Jays prospects
    {"name": "Ricky Tiedemann", "team": "blue_jays", "position": "LHP", "age": 22, "ranking": 32, "future_value": 55, "eta": 2024, "year": 2024},
    {"name": "Orelvis Martinez", "team": "blue_jays", "position": "SS", "age": 22, "ranking": 38, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Addison Barger", "team": "blue_jays", "position": "3B", "age": 24, "ranking": 52, "future_value": 45, "eta": 2024, "year": 2024},
    
    # Rays prospects
    {"name": "Carson Williams", "team": "rays", "position": "SS", "age": 20, "ranking": 22, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Brayden Taylor", "team": "rays", "position": "OF", "age": 21, "ranking": 47, "future_value": 45, "eta": 2025, "year": 2024},
    {"name": "Mason Montgomery", "team": "rays", "position": "LHP", "age": 22, "ranking": 58, "future_value": 45, "eta": 2024, "year": 2024},
    
    # Add prospects for other teams...
    {"name": "Colt Keith", "team": "tigers", "position": "2B", "age": 22, "ranking": 21, "future_value": 55, "eta": 2024, "year": 2024},
    {"name": "Jackson Jobe", "team": "tigers", "position": "RHP", "age": 22, "ranking": 24, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Justyn-Henry Malloy", "team": "tigers", "position": "OF", "age": 24, "ranking": 41, "future_value": 45, "eta": 2024, "year": 2024},
    
    # White Sox prospects
    {"name": "Noah Schultz", "team": "white_sox", "position": "LHP", "age": 21, "ranking": 26, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Colson Montgomery", "team": "white_sox", "position": "SS", "age": 22, "ranking": 33, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Brooks Baldwin", "team": "white_sox", "position": "2B", "age": 22, "ranking": 46, "future_value": 45, "eta": 2025, "year": 2024},
    
    # Guardians prospects
    {"name": "Kyle Manzardo", "team": "guardians", "position": "1B", "age": 23, "ranking": 27, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Chase DeLauter", "team": "guardians", "position": "OF", "age": 23, "ranking": 36, "future_value": 50, "eta": 2025, "year": 2024},
    {"name": "Jaison Chourio", "team": "guardians", "position": "OF", "age": 19, "ranking": 49, "future_value": 45, "eta": 2026, "year": 2024},
    
    # Twins prospects
    {"name": "Brooks Lee", "team": "twins", "position": "SS", "age": 23, "ranking": 29, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Emmanuel Rodriguez", "team": "twins", "position": "OF", "age": 21, "ranking": 39, "future_value": 50, "eta": 2025, "year": 2024},
    {"name": "Marco Raya", "team": "twins", "position": "SS", "age": 19, "ranking": 56, "future_value": 45, "eta": 2026, "year": 2024},
    
    # Royals prospects
    {"name": "Gavin Cross", "team": "royals", "position": "OF", "age": 22, "ranking": 31, "future_value": 50, "eta": 2025, "year": 2024},
    {"name": "Ben Kudrna", "team": "royals", "position": "RHP", "age": 21, "ranking": 44, "future_value": 45, "eta": 2025, "year": 2024},
    {"name": "Cayden Wallace", "team": "royals", "position": "3B", "age": 21, "ranking": 50, "future_value": 45, "eta": 2025, "year": 2024},
]

def create_scouting_report(prospect: Dict) -> Dict:
    """Generate realistic scouting report based on position and future value"""
    base_report = {
        "overall": f"{prospect['future_value']}/80",
        "risk": determine_risk_level(prospect),
        "summary": f"Ranked #{prospect['ranking']} prospect with {prospect['future_value']} FV ceiling",
        "updated": datetime.now().isoformat()
    }
    
    # Position-specific tools
    if prospect['position'] in ['OF', 'CF', 'RF', 'LF']:
        base_report.update({
            "hit": f"{min(prospect['future_value'] - 5, 60)}/80",
            "power": f"{min(prospect['future_value'], 65)}/80",
            "run": f"{min(prospect['future_value'] - 10, 55)}/80",
            "arm": f"{min(prospect['future_value'] - 5, 60)}/80",
            "field": f"{min(prospect['future_value'] - 5, 60)}/80"
        })
    elif prospect['position'] in ['RHP', 'LHP']:
        base_report.update({
            "fastball": f"{min(prospect['future_value'], 65)}/80",
            "breaking_ball": f"{min(prospect['future_value'] - 5, 60)}/80", 
            "changeup": f"{min(prospect['future_value'] - 10, 55)}/80",
            "control": f"{min(prospect['future_value'] - 5, 60)}/80",
            "command": f"{min(prospect['future_value'] - 10, 55)}/80"
        })
    elif prospect['position'] in ['C']:
        base_report.update({
            "hit": f"{min(prospect['future_value'] - 10, 55)}/80",
            "power": f"{min(prospect['future_value'] - 5, 60)}/80",
            "arm": f"{min(prospect['future_value'], 65)}/80",
            "field": f"{min(prospect['future_value'], 65)}/80",
            "receiving": f"{min(prospect['future_value'] + 5, 70)}/80"
        })
    else:  # Infielders
        base_report.update({
            "hit": f"{min(prospect['future_value'] - 5, 60)}/80",
            "power": f"{min(prospect['future_value'], 65)}/80",
            "run": f"{min(prospect['future_value'] - 15, 50)}/80",
            "arm": f"{min(prospect['future_value'] - 5, 60)}/80",
            "field": f"{min(prospect['future_value'], 65)}/80"
        })
    
    return base_report

def determine_risk_level(prospect: Dict) -> str:
    """Determine risk level based on age, position, and future value"""
    age = prospect.get('age', 22)
    fv = prospect.get('future_value', 45)
    position = prospect.get('position', 'OF')
    
    # Pitchers generally higher risk
    if position in ['RHP', 'LHP']:
        if fv >= 60:
            return "high"
        elif fv >= 50:
            return "medium"
        else:
            return "low"
    
    # Position players
    if age <= 20 and fv >= 60:
        return "medium"
    elif age >= 24:
        return "low"
    elif fv >= 60:
        return "medium"
    else:
        return "low"

async def seed_prospects():
    """Seed historical prospect data"""
    try:
        from backend.services.supabase_service import supabase_service
        
        # Get team mapping
        team_mapping = get_team_mapping()
        if not team_mapping:
            logger.error("Failed to load team mapping")
            return False
            
        logger.info(f"Loaded team mapping for {len(team_mapping)} teams")
        
        # Combine all prospect data
        all_prospects = HISTORICAL_PROSPECTS + TEAM_SPECIFIC_PROSPECTS
        
        # Prepare prospect records
        prospect_records = []
        for prospect_data in all_prospects:
            # Get team ID
            team_key = prospect_data['team']
            team_id = team_mapping.get(team_key)
            
            if not team_id:
                logger.warning(f"Team not found: {team_key}")
                continue
            
            # Create scouting report
            scouting_report = create_scouting_report(prospect_data)
            
            # Prepare record
            record = {
                'name': prospect_data['name'],
                'team_id': team_id,
                'position': prospect_data['position'],
                'age': prospect_data['age'],
                'ranking': prospect_data['ranking'],
                'future_value': prospect_data['future_value'],
                'eta': prospect_data['eta'],
                'risk_level': determine_risk_level(prospect_data),
                'scouting_report': scouting_report
            }
            
            prospect_records.append(record)
        
        logger.info(f"Prepared {len(prospect_records)} prospect records")
        
        # Insert in batches
        batch_size = 50
        total_inserted = 0
        
        for i in range(0, len(prospect_records), batch_size):
            batch = prospect_records[i:i + batch_size]
            
            try:
                result = supabase_service.supabase.table('prospects').insert(batch).execute()
                total_inserted += len(batch)
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} prospects (total: {total_inserted})")
                
            except Exception as e:
                logger.error(f"Error inserting batch {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"Successfully seeded {total_inserted} historical prospects")
        return True
        
    except Exception as e:
        logger.error(f"Error seeding prospects: {e}")
        return False

def verify_data():
    """Verify seeded prospect data"""
    try:
        from backend.services.supabase_service import supabase_service
        
        # Count total prospects
        result = supabase_service.supabase.table('prospects').select('*', count='exact').execute()
        total_count = result.count
        
        logger.info(f"Total prospects in database: {total_count}")
        
        # Sample by position
        positions = ['OF', 'RHP', 'LHP', 'SS', 'C', '3B', '2B', '1B']
        for pos in positions:
            result = supabase_service.supabase.table('prospects').select('name', count='exact').eq('position', pos).execute()
            logger.info(f"{pos}: {result.count} prospects")
        
        # Sample by risk level
        risk_levels = ['low', 'medium', 'high']
        for risk in risk_levels:
            result = supabase_service.supabase.table('prospects').select('name', count='exact').eq('risk_level', risk).execute()
            logger.info(f"{risk} risk: {result.count} prospects")
        
        # Show top 10 prospects
        result = supabase_service.supabase.table('prospects').select('name, ranking, future_value, position').order('ranking').limit(10).execute()
        logger.info("Top 10 prospects:")
        for i, prospect in enumerate(result.data, 1):
            logger.info(f"  {i}. {prospect['name']} ({prospect['position']}) - {prospect['future_value']} FV")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return False

async def main():
    """Main execution function"""
    logger.info("Starting historical prospect database seeding")
    
    # Seed prospects
    success = await seed_prospects()
    if not success:
        logger.error("Failed to seed prospects")
        return
    
    # Verify data
    if verify_data():
        logger.info("Prospect seeding completed successfully!")
    else:
        logger.error("Data verification failed")

if __name__ == "__main__":
    asyncio.run(main())