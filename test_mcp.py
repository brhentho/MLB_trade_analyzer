#!/usr/bin/env python3
"""
Test script for Baseball Trade AI MCP Integration
Verifies that the MCP server and tools work correctly
"""

import asyncio
import json
import sys
from datetime import datetime

# Import our MCP components
from backend.services.supabase_mcp import supabase_mcp, get_teams, get_players, search_players, get_team_roster
from mcp_server import MCPServer

async def test_health_check():
    """Test basic health check"""
    print("🏥 Testing health check...")
    health = await supabase_mcp.health_check()
    
    if health['status'] == 'healthy':
        print(f"✅ Database healthy: {health['teams_count']} teams, {health['players_count']} players")
        return True
    else:
        print(f"❌ Database unhealthy: {health.get('error')}")
        return False

async def test_list_tools():
    """Test listing available tools"""
    print("\n🔧 Testing tool listing...")
    tools = supabase_mcp.list_tools()
    
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    return len(tools) > 0

async def test_get_teams():
    """Test getting teams"""
    print("\n🏟️  Testing get_teams...")
    
    # Test basic teams query
    teams = await get_teams(limit=5)
    if teams:
        print(f"✅ Retrieved {len(teams)} teams:")
        for team in teams[:3]:
            print(f"  - {team['name']} ({team['abbreviation']}) - {team['division']}")
        return True
    else:
        print("❌ No teams found")
        return False

async def test_get_players():
    """Test getting players"""
    print("\n⚾ Testing get_players...")
    
    # Test players with WAR filter
    players = await get_players(min_war=2.0, limit=10)
    if players:
        print(f"✅ Retrieved {len(players)} players with WAR >= 2.0:")
        for player in players[:3]:
            team_info = player.get('teams', {})
            team_name = team_info.get('name', 'Unknown') if team_info else 'Unknown'
            print(f"  - {player['name']} ({team_name}) - WAR: {player.get('war', 'N/A')}")
        return True
    else:
        print("❌ No players found")
        return False

async def test_search_players():
    """Test player search functionality"""
    print("\n🔍 Testing search_players...")
    
    # Search for players with common names
    search_terms = ["Mike", "John", "Jose"]
    
    for term in search_terms:
        results = await search_players(term, limit=3)
        if results:
            print(f"✅ Search '{term}' found {len(results)} players:")
            for player in results[:2]:
                team_info = player.get('teams', {})
                team_name = team_info.get('abbreviation', 'UNK') if team_info else 'UNK'
                print(f"  - {player['name']} ({team_name})")
            break
    else:
        print("❌ No search results found")
        return False
    
    return True

async def test_team_roster():
    """Test getting team roster"""
    print("\n📋 Testing get_team_roster...")
    
    # Test with a few common team abbreviations
    test_teams = ["NYY", "LAD", "BOS"]
    
    for team_abbr in test_teams:
        try:
            roster = await get_team_roster(team_abbr)
            if roster and roster.get('roster'):
                team = roster['team']
                players = roster['roster']
                print(f"✅ {team['name']} roster: {len(players)} players")
                
                # Show position breakdown
                pitchers = [p for p in players if p.get('position') == 'Pitcher']
                position_players = [p for p in players if p.get('position') == 'Position Player']
                print(f"  - Pitchers: {len(pitchers)}, Position Players: {len(position_players)}")
                return True
        except Exception as e:
            print(f"⚠️  Could not get roster for {team_abbr}: {e}")
            continue
    
    print("❌ No team rosters found")
    return False

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("\n🖥️  Testing MCP Server...")
    
    server = MCPServer()
    
    # Test initialize
    init_response = await server.handle_request({
        "method": "initialize",
        "params": {}
    })
    
    if init_response.get("serverInfo"):
        print(f"✅ Server initialized: {init_response['serverInfo']['name']}")
    else:
        print("❌ Server initialization failed")
        return False
    
    # Test list tools
    tools_response = await server.handle_request({
        "method": "tools/list",
        "params": {}
    })
    
    if tools_response.get("tools"):
        print(f"✅ Tools listed: {len(tools_response['tools'])} available")
    else:
        print("❌ Tools listing failed")
        return False
    
    # Test tool call
    call_response = await server.handle_request({
        "method": "tools/call",
        "params": {
            "name": "get_teams",
            "arguments": {"limit": 3}
        }
    })
    
    if call_response.get("content"):
        print("✅ Tool call successful")
        return True
    else:
        print("❌ Tool call failed")
        return False

async def test_tool_execution():
    """Test direct tool execution"""
    print("\n⚙️  Testing direct tool execution...")
    
    # Test get_teams tool
    result = await supabase_mcp.execute_tool("get_teams", {"limit": 3})
    if result.get("success"):
        teams = result["data"]
        print(f"✅ get_teams executed: {len(teams)} teams returned")
    else:
        print(f"❌ get_teams failed: {result.get('error')}")
        return False
    
    # Test get_players tool
    result = await supabase_mcp.execute_tool("get_players", {"limit": 5, "min_war": 1.0})
    if result.get("success"):
        players = result["data"]
        print(f"✅ get_players executed: {len(players)} players returned")
    else:
        print(f"❌ get_players failed: {result.get('error')}")
        return False
    
    return True

async def main():
    """Run all MCP tests"""
    print("🏟️  Baseball Trade AI - MCP Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("List Tools", test_list_tools),
        ("Get Teams", test_get_teams),
        ("Get Players", test_get_players),
        ("Search Players", test_search_players),
        ("Team Roster", test_team_roster),
        ("Tool Execution", test_tool_execution),
        ("MCP Server", test_mcp_server),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All MCP tests passed! Your Supabase MCP integration is working correctly.")
        print("\nNext steps:")
        print("1. Update claude_desktop_config.json with your actual Supabase credentials")
        print("2. Add the MCP server to your Claude Desktop configuration")
        print("3. Start using MCP tools for database operations!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check your setup:")
        print("- Ensure your .env file has correct Supabase credentials")
        print("- Verify you've run the database migrations")
        print("- Check that you have some data in your database")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)