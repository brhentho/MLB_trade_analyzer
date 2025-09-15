#!/usr/bin/env python3
"""
Test MCP integration with real seeded data
"""

import asyncio
import logging
import json
from backend.services.supabase_mcp import supabase_mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_get_teams():
    """Test getting teams"""
    print("🏟️  Testing get_teams...")
    
    try:
        result = await supabase_mcp.execute_tool("get_teams", {})
        
        if result.get('success'):
            teams = result.get('data', [])
            print(f"✅ Found {len(teams)} teams")
            if teams:
                print(f"   Example: {teams[0]['name']} ({teams[0]['abbreviation']})")
            return True
        else:
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_get_players():
    """Test getting players"""
    print("⚾ Testing get_players...")
    
    try:
        # Get first 5 players
        result = await supabase_mcp.execute_tool("get_players", {"limit": 5})
        
        if result.get('success'):
            players = result.get('data', [])
            print(f"✅ Found {len(players)} players (limited to 5)")
            for player in players:
                print(f"   {player['name']} - {player['position']} (WAR: {player['war']})")
            return True
        else:
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_search_players():
    """Test searching for specific players"""
    print("🔍 Testing search_players...")
    
    try:
        # Search for Aaron Judge
        result = await supabase_mcp.execute_tool("search_players", {"query": "Aaron Judge"})
        
        if result.get('success'):
            players = result.get('data', [])
            print(f"✅ Found {len(players)} players matching 'Aaron Judge'")
            for player in players:
                print(f"   {player['name']} - {player['position']} (WAR: {player['war']})")
                if player.get('stats'):
                    stats = player['stats']
                    if stats.get('type') == 'batting':
                        print(f"      Stats: .{stats.get('avg', 0):.3f} AVG, {stats.get('home_runs', 0)} HR, {stats.get('rbi', 0)} RBI")
            return True
        else:
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_get_team_roster():
    """Test getting team roster"""
    print("👥 Testing get_team_roster...")
    
    try:
        # Get Yankees roster
        result = await supabase_mcp.execute_tool("get_team_roster", {"team_identifier": "NYY"})
        
        if result.get('success'):
            roster_data = result.get('data', {})
            team_info = roster_data.get('team_info', {})
            roster = roster_data.get('roster', [])
            stats = roster_data.get('stats', {})
            
            print(f"✅ {team_info.get('name', 'Unknown')} roster:")
            print(f"   Total players: {len(roster)}")
            print(f"   Batting avg: {stats.get('team_batting_avg', 0):.3f}")
            print(f"   Team ERA: {stats.get('team_era', 0):.2f}")
            
            # Show top 3 players by WAR
            top_players = sorted(roster, key=lambda x: x.get('war', 0), reverse=True)[:3]
            print("   Top players by WAR:")
            for player in top_players:
                print(f"     {player['name']} - {player['position']} (WAR: {player['war']})")
            
            return True
        else:
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_get_team_statistics():
    """Test getting team statistics"""
    print("📊 Testing get_team_statistics...")
    
    try:
        # Get Dodgers statistics
        result = await supabase_mcp.execute_tool("get_team_statistics", {"team_id": 28})  # Dodgers
        
        if result.get('success'):
            stats = result.get('data', {})
            print(f"✅ Team statistics:")
            print(f"   Total players: {stats.get('total_players', 0)}")
            print(f"   Avg WAR: {stats.get('avg_war', 0):.2f}")
            print(f"   Total payroll: ${stats.get('total_salary', 0):,}")
            print(f"   Batting average: {stats.get('team_batting_avg', 0):.3f}")
            print(f"   Team ERA: {stats.get('team_era', 0):.2f}")
            
            return True
        else:
            print(f"❌ Error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_update_player():
    """Test updating a player"""
    print("✏️  Testing update_player...")
    
    try:
        # First, get a player to update
        players_result = await supabase_mcp.execute_tool("get_players", {"limit": 1})
        
        if not players_result.get('success') or not players_result.get('data'):
            print("❌ No players found to update")
            return False
        
        player = players_result['data'][0]
        player_id = player['id']
        original_war = player['war']
        
        print(f"   Updating player: {player['name']} (ID: {player_id})")
        print(f"   Original WAR: {original_war}")
        
        # Update the player's WAR
        new_war = original_war + 0.1
        result = await supabase_mcp.execute_tool("update_player", {
            "player_id": player_id,
            "data": {"war": new_war}
        })
        
        if result.get('success'):
            updated_player = result.get('data', {})
            print(f"   ✅ Updated WAR: {updated_player.get('war')}")
            
            # Revert the change
            revert_result = await supabase_mcp.execute_tool("update_player", {
                "player_id": player_id,
                "data": {"war": original_war}
            })
            
            if revert_result.get('success'):
                print(f"   ✅ Reverted WAR back to: {original_war}")
            
            return True
        else:
            print(f"❌ Error updating player: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def main():
    """Run all MCP integration tests"""
    print("🧪 Baseball Trade AI - MCP Integration Test")
    print("=" * 50)
    
    tests = [
        ("Get Teams", test_get_teams),
        ("Get Players", test_get_players),
        ("Search Players", test_search_players),
        ("Get Team Roster", test_get_team_roster),
        ("Get Team Statistics", test_get_team_statistics),
        ("Update Player", test_update_player),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 {test_name}")
        print("-" * 30)
        success = await test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:8} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All MCP integration tests passed!")
        print("🚀 Ready for production use!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)