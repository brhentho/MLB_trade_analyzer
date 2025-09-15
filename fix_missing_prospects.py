#!/usr/bin/env python3
"""
Fix Missing Prospects Script
Add prospects for teams that had mapping issues
"""

import sys
import asyncio
import logging
from datetime import datetime

sys.path.append('.')
sys.path.append('./backend')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Missing prospects with correct team keys
MISSING_PROSPECTS = [
    # Red Sox prospects (redsox, not red_sox)
    {"name": "Roman Anthony", "team": "redsox", "position": "OF", "age": 20, "ranking": 6, "future_value": 60, "eta": 2025, "year": 2024},
    {"name": "Marcelo Mayer", "team": "redsox", "position": "SS", "age": 22, "ranking": 8, "future_value": 60, "eta": 2025, "year": 2024},
    {"name": "Kristian Campbell", "team": "redsox", "position": "2B", "age": 22, "ranking": 25, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Kyle Teel", "team": "redsox", "position": "C", "age": 22, "ranking": 30, "future_value": 50, "eta": 2025, "year": 2024},
    {"name": "Miguel Bleis", "team": "redsox", "position": "OF", "age": 20, "ranking": 40, "future_value": 50, "eta": 2026, "year": 2024},
    
    # Blue Jays prospects (bluejays, not blue_jays)
    {"name": "Ricky Tiedemann", "team": "bluejays", "position": "LHP", "age": 22, "ranking": 32, "future_value": 55, "eta": 2024, "year": 2024},
    {"name": "Orelvis Martinez", "team": "bluejays", "position": "SS", "age": 22, "ranking": 38, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Addison Barger", "team": "bluejays", "position": "3B", "age": 24, "ranking": 52, "future_value": 45, "eta": 2024, "year": 2024},
    {"name": "Gabriel Moreno", "team": "bluejays", "position": "C", "age": 22, "ranking": 6, "future_value": 55, "eta": 2022, "year": 2022},
    {"name": "Nate Pearson", "team": "bluejays", "position": "RHP", "age": 24, "ranking": 7, "future_value": 55, "eta": 2020, "year": 2020},
    
    # White Sox prospects (whitesox, not white_sox)
    {"name": "Noah Schultz", "team": "whitesox", "position": "LHP", "age": 21, "ranking": 26, "future_value": 55, "eta": 2025, "year": 2024},
    {"name": "Colson Montgomery", "team": "whitesox", "position": "SS", "age": 22, "ranking": 33, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Brooks Baldwin", "team": "whitesox", "position": "2B", "age": 22, "ranking": 46, "future_value": 45, "eta": 2025, "year": 2024},
    {"name": "Luis Robert", "team": "whitesox", "position": "OF", "age": 23, "ranking": 1, "future_value": 65, "eta": 2020, "year": 2020},
    {"name": "Dylan Cease", "team": "whitesox", "position": "RHP", "age": 24, "ranking": 6, "future_value": 50, "eta": 2020, "year": 2020},
    
    # Additional top prospects for other teams
    {"name": "Cam Collier", "team": "reds", "position": "3B", "age": 19, "ranking": 23, "future_value": 55, "eta": 2026, "year": 2024},
    {"name": "Rhett Lowder", "team": "reds", "position": "RHP", "age": 22, "ranking": 37, "future_value": 50, "eta": 2024, "year": 2024},
    {"name": "Sal Stewart", "team": "reds", "position": "C", "age": 21, "ranking": 43, "future_value": 45, "eta": 2025, "year": 2024},
    
    # Padres prospects
    {"name": "Robby Snelling", "team": "padres", "position": "LHP", "age": 21, "ranking": 34, "future_value": 50, "eta": 2025, "year": 2024},
    {"name": "Leodalis De Vries", "team": "padres", "position": "SS", "age": 18, "ranking": 51, "future_value": 45, "eta": 2027, "year": 2024},
    {"name": "MacKenzie Gore", "team": "padres", "position": "LHP", "age": 22, "ranking": 10, "future_value": 55, "eta": 2021, "year": 2021},
    
    # Giants prospects
    {"name": "Bryce Eldridge", "team": "giants", "position": "1B", "age": 19, "ranking": 53, "future_value": 45, "eta": 2026, "year": 2024},
    {"name": "Carson Whisenhunt", "team": "giants", "position": "OF", "age": 21, "ranking": 60, "future_value": 40, "eta": 2025, "year": 2024},
    
    # Dodgers prospects
    {"name": "Kendall George", "team": "phillies", "position": "OF", "age": 20, "ranking": 14, "future_value": 55, "eta": 2026, "year": 2024},
    {"name": "Josue De Paula", "team": "dodgers", "position": "OF", "age": 19, "ranking": 54, "future_value": 45, "eta": 2026, "year": 2024},
    {"name": "Gavin Lux", "team": "dodgers", "position": "2B", "age": 22, "ranking": 2, "future_value": 55, "eta": 2020, "year": 2020},
    {"name": "Dustin May", "team": "dodgers", "position": "RHP", "age": 22, "ranking": 9, "future_value": 50, "eta": 2020, "year": 2020},
    
    # Cardinals prospects  
    {"name": "Chase Davis", "team": "cardinals", "position": "OF", "age": 22, "ranking": 57, "future_value": 40, "eta": 2025, "year": 2024},
    {"name": "Tink Hence", "team": "cardinals", "position": "RHP", "age": 21, "ranking": 59, "future_value": 45, "eta": 2025, "year": 2024},
    {"name": "Jordan Walker", "team": "cardinals", "position": "OF", "age": 21, "ranking": 8, "future_value": 60, "eta": 2023, "year": 2023},
    {"name": "Dylan Carlson", "team": "cardinals", "position": "OF", "age": 22, "ranking": 7, "future_value": 55, "eta": 2021, "year": 2021},
    
    # Mets prospects
    {"name": "Jett Williams", "team": "mets", "position": "2B", "age": 20, "ranking": 61, "future_value": 40, "eta": 2026, "year": 2024},
    {"name": "Drew Gilbert", "team": "mets", "position": "OF", "age": 23, "ranking": 62, "future_value": 40, "eta": 2025, "year": 2024},
    {"name": "Francisco Alvarez", "team": "mets", "position": "C", "age": 21, "ranking": 5, "future_value": 65, "eta": 2023, "year": 2023},
    
    # Phillies prospects
    {"name": "Aidan Miller", "team": "phillies", "position": "SS", "age": 19, "ranking": 63, "future_value": 40, "eta": 2026, "year": 2024},
    {"name": "Justin Crawford", "team": "phillies", "position": "OF", "age": 20, "ranking": 64, "future_value": 40, "eta": 2026, "year": 2024},
    
    # Braves prospects
    {"name": "Nacho Alvarez Jr.", "team": "braves", "position": "SS", "age": 19, "ranking": 65, "future_value": 40, "eta": 2027, "year": 2024},
    {"name": "JR Ritchie", "team": "braves", "position": "RHP", "age": 20, "ranking": 66, "future_value": 40, "eta": 2026, "year": 2024},
    {"name": "Ian Anderson", "team": "braves", "position": "RHP", "age": 23, "ranking": 4, "future_value": 55, "eta": 2021, "year": 2021},
    {"name": "Cristian Pache", "team": "braves", "position": "OF", "age": 22, "ranking": 9, "future_value": 55, "eta": 2021, "year": 2021},
    
    # Nationals prospects
    {"name": "Dylan Crews", "team": "nationals", "position": "OF", "age": 22, "ranking": 67, "future_value": 40, "eta": 2025, "year": 2024},
    {"name": "James Wood", "team": "nationals", "position": "OF", "age": 21, "ranking": 68, "future_value": 40, "eta": 2025, "year": 2024},
    {"name": "Carter Kieboom", "team": "nationals", "position": "SS", "age": 22, "ranking": 5, "future_value": 55, "eta": 2020, "year": 2020},
    
    # Marlins prospects
    {"name": "Noble Meyer", "team": "marlins", "position": "RHP", "age": 21, "ranking": 69, "future_value": 40, "eta": 2025, "year": 2024},
    {"name": "Thomas White", "team": "marlins", "position": "OF", "age": 19, "ranking": 70, "future_value": 40, "eta": 2027, "year": 2024},
    {"name": "Sixto Sanchez", "team": "marlins", "position": "RHP", "age": 23, "ranking": 8, "future_value": 60, "eta": 2021, "year": 2021},
]

def create_scouting_report(prospect):
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

def determine_risk_level(prospect):
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

async def add_missing_prospects():
    """Add the missing prospects with correct team mappings"""
    try:
        from backend.services.supabase_service import supabase_service
        
        # Get team mapping
        result = supabase_service.supabase.table('teams').select('id, team_key, abbreviation').execute()
        team_mapping = {}
        for team in result.data:
            team_mapping[team['team_key']] = team['id']
            team_mapping[team['abbreviation']] = team['id']
        
        logger.info(f"Loaded team mapping for {len(team_mapping)} teams")
        
        # Prepare prospect records
        prospect_records = []
        for prospect_data in MISSING_PROSPECTS:
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
        
        logger.info(f"Prepared {len(prospect_records)} missing prospect records")
        
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
        
        logger.info(f"Successfully added {total_inserted} missing prospects")
        return True
        
    except Exception as e:
        logger.error(f"Error adding prospects: {e}")
        return False

def verify_final_data():
    """Verify final prospect data"""
    try:
        from backend.services.supabase_service import supabase_service
        
        # Count total prospects
        result = supabase_service.supabase.table('prospects').select('*', count='exact').execute()
        total_count = result.count
        
        logger.info(f"Total prospects in database: {total_count}")
        
        # Count by team
        result = supabase_service.supabase.table('teams').select('id, team_key, abbreviation').execute()
        for team in result.data:
            team_result = supabase_service.supabase.table('prospects').select('name', count='exact').eq('team_id', team['id']).execute()
            if team_result.count > 0:
                logger.info(f"{team['team_key']}: {team_result.count} prospects")
        
        # Sample top prospects by FV
        result = supabase_service.supabase.table('prospects').select('name, future_value, position').order('future_value', desc=True).limit(15).execute()
        logger.info("Top 15 prospects by Future Value:")
        for i, prospect in enumerate(result.data, 1):
            logger.info(f"  {i}. {prospect['name']} ({prospect['position']}) - {prospect['future_value']} FV")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return False

async def main():
    """Main execution function"""
    logger.info("Adding missing prospects with correct team mappings")
    
    # Add missing prospects
    success = await add_missing_prospects()
    if not success:
        logger.error("Failed to add missing prospects")
        return
    
    # Verify final data
    if verify_final_data():
        logger.info("Missing prospect addition completed successfully!")
    else:
        logger.error("Final data verification failed")

if __name__ == "__main__":
    asyncio.run(main())