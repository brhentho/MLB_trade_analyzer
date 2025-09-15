#!/usr/bin/env python3
"""
Quick test to verify seeding works with a small dataset
"""

import asyncio
import logging
from backend.services.supabase_mcp import supabase_mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_player_insert():
    """Test inserting a single player"""
    print("🧪 Testing player insertion...")
    
    # Test player data that matches schema
    test_player = {
        'name': 'Test Player',
        'team_id': 23,  # Yankees
        'position': 'Batter',  # Under 10 chars
        'age': 28,
        'war': 3.5,
        'stats': {
            'type': 'batting',
            'season': 2024,
            'avg': 0.300,
            'hr': 25
        }
    }
    
    try:
        # Try to insert using MCP
        result = await supabase_mcp.execute_tool("update_player", {
            "player_id": 1,  # This will fail, but let's see the error
            "data": test_player
        })
        print(f"MCP result: {result}")
        
        # Try direct insert
        response = supabase_mcp.supabase.table('players').insert(test_player).execute()
        print(f"✅ Successfully inserted test player: {response.data}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inserting test player: {e}")
        return False

async def main():
    print("🏟️  Quick Database Test")
    print("=" * 30)
    
    success = await test_player_insert()
    
    if success:
        print("✅ Database schema is working correctly!")
        print("Ready to run full seeding with: python3 seed_historical_data.py")
    else:
        print("❌ Database schema issues detected.")
        print("Check the error message above.")

if __name__ == "__main__":
    asyncio.run(main())