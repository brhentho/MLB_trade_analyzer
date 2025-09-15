#!/usr/bin/env python3
"""
Quick test to seed just 2024 data to verify everything works
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from seed_historical_data import HistoricalDataSeeder

async def main():
    """Seed just 2024 data as a test"""
    print("🏟️  Testing 2024 Data Seeding...")
    
    try:
        seeder = HistoricalDataSeeder()
        
        # Run seeding for just 2024
        result = await seeder.run_historical_seed([2024])
        
        if result['success']:
            print("✅ 2024 data seeding successful!")
            print(f"📊 Players inserted: {result['stats']['players_inserted']}")
            print(f"🔄 Players updated: {result['stats']['players_updated']}")
        else:
            print("❌ 2024 data seeding had errors")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)