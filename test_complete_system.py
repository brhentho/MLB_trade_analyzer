#!/usr/bin/env python3
"""
Comprehensive System Test for Baseball Trade AI
Tests all components: database, MCP, historical data, daily updates, monitoring
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any

# Import all the services
from backend.services.supabase_mcp import supabase_mcp
from backend.services.data_ingestion import data_service
from backend.services.monitoring_service import monitoring_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTester:
    """
    Comprehensive system testing suite
    """
    
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'failures': [],
            'successes': []
        }
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.test_results['tests_run'] += 1
        
        if success:
            self.test_results['tests_passed'] += 1
            self.test_results['successes'].append({
                'test': test_name,
                'details': details
            })
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   📝 {details}")
        else:
            self.test_results['tests_failed'] += 1
            self.test_results['failures'].append({
                'test': test_name,
                'details': details
            })
            print(f"❌ {test_name}: FAILED")
            if details:
                print(f"   📝 {details}")
    
    async def test_database_connection(self) -> bool:
        """Test basic database connectivity"""
        print("\n🔌 Testing Database Connection...")
        
        try:
            teams_result = await supabase_mcp.execute_tool("get_teams", {})
            
            if teams_result.get('success') and len(teams_result.get('data', [])) == 30:
                self.log_test_result("Database Connection", True, f"Found {len(teams_result['data'])} teams")
                return True
            else:
                self.log_test_result("Database Connection", False, "Could not retrieve teams")
                return False
                
        except Exception as e:
            self.log_test_result("Database Connection", False, f"Exception: {e}")
            return False
    
    async def test_mcp_integration(self) -> bool:
        """Test MCP tool functionality"""
        print("\n🔧 Testing MCP Integration...")
        
        tests_passed = 0
        total_tests = 6
        
        # Test 1: Get Teams
        try:
            result = await supabase_mcp.execute_tool("get_teams", {"limit": 5})
            if result.get('success') and len(result.get('data', [])) == 5:
                self.log_test_result("MCP Get Teams", True, "Retrieved 5 teams")
                tests_passed += 1
            else:
                self.log_test_result("MCP Get Teams", False, "Failed to get teams")
        except Exception as e:
            self.log_test_result("MCP Get Teams", False, f"Exception: {e}")
        
        # Test 2: Get Players
        try:
            result = await supabase_mcp.execute_tool("get_players", {"limit": 10})
            if result.get('success') and len(result.get('data', [])) >= 5:
                self.log_test_result("MCP Get Players", True, f"Retrieved {len(result['data'])} players")
                tests_passed += 1
            else:
                self.log_test_result("MCP Get Players", False, "Failed to get players")
        except Exception as e:
            self.log_test_result("MCP Get Players", False, f"Exception: {e}")
        
        # Test 3: Search Players
        try:
            result = await supabase_mcp.execute_tool("search_players", {"query": "Aaron Judge"})
            if result.get('success') and len(result.get('data', [])) >= 1:
                judge_data = result['data'][0]
                self.log_test_result("MCP Search Players", True, f"Found {judge_data['name']} (WAR: {judge_data['war']})")
                tests_passed += 1
            else:
                self.log_test_result("MCP Search Players", False, "Could not find Aaron Judge")
        except Exception as e:
            self.log_test_result("MCP Search Players", False, f"Exception: {e}")
        
        # Test 4: Get Team Roster
        try:
            result = await supabase_mcp.execute_tool("get_team_roster", {"team_identifier": "NYY"})
            if result.get('success'):
                roster_data = result.get('data', {})
                team_info = roster_data.get('team_info', {})
                roster = roster_data.get('roster', [])
                self.log_test_result("MCP Get Team Roster", True, f"{team_info.get('name', 'Yankees')} has {len(roster)} players")
                tests_passed += 1
            else:
                self.log_test_result("MCP Get Team Roster", False, "Failed to get Yankees roster")
        except Exception as e:
            self.log_test_result("MCP Get Team Roster", False, f"Exception: {e}")
        
        # Test 5: Get Team Statistics
        try:
            result = await supabase_mcp.execute_tool("get_team_statistics", {"team_id": 28})  # Dodgers
            if result.get('success'):
                stats = result.get('data', {})
                self.log_test_result("MCP Get Team Statistics", True, f"Dodgers: {stats.get('total_players', 0)} players")
                tests_passed += 1
            else:
                self.log_test_result("MCP Get Team Statistics", False, "Failed to get team statistics")
        except Exception as e:
            self.log_test_result("MCP Get Team Statistics", False, f"Exception: {e}")
        
        # Test 6: Update Player (non-destructive test)
        try:
            # Get a player first
            players_result = await supabase_mcp.execute_tool("get_players", {"limit": 1})
            if players_result.get('success') and players_result.get('data'):
                player = players_result['data'][0]
                original_war = player['war']
                
                # Update WAR slightly
                new_war = float(original_war) + 0.001
                update_result = await supabase_mcp.execute_tool("update_player", {
                    "player_id": player['id'],
                    "data": {"war": new_war}
                })
                
                if update_result.get('success'):
                    # Revert the change
                    revert_result = await supabase_mcp.execute_tool("update_player", {
                        "player_id": update_result['data']['id'],
                        "data": {"war": original_war}
                    })
                    
                    if revert_result.get('success'):
                        self.log_test_result("MCP Update Player", True, f"Updated and reverted {player['name']}")
                        tests_passed += 1
                    else:
                        self.log_test_result("MCP Update Player", False, "Failed to revert player update")
                else:
                    self.log_test_result("MCP Update Player", False, "Failed to update player")
            else:
                self.log_test_result("MCP Update Player", False, "No players available for update test")
        except Exception as e:
            self.log_test_result("MCP Update Player", False, f"Exception: {e}")
        
        return tests_passed == total_tests
    
    async def test_historical_data(self) -> bool:
        """Test historical data completeness"""
        print("\n📚 Testing Historical Data...")
        
        try:
            # Get player count
            players_result = await supabase_mcp.execute_tool("get_players", {})
            
            if not players_result.get('success'):
                self.log_test_result("Historical Data", False, "Could not retrieve players")
                return False
            
            players = players_result.get('data', [])
            total_players = len(players)
            
            # Check for multiple seasons
            seasons = set()
            teams_with_players = set()
            star_players_found = []
            
            for player in players:
                if player.get('stats') and player['stats'].get('season'):
                    seasons.add(player['stats']['season'])
                if player.get('team_id'):
                    teams_with_players.add(player['team_id'])
                
                # Check for known star players
                if player['name'] in ['Aaron Judge', 'Shohei Ohtani', 'Juan Soto', 'Mookie Betts', 'Francisco Lindor']:
                    star_players_found.append(player['name'])
            
            # Validate data quality
            success = (
                total_players >= 200 and  # At least 200 players total
                len(seasons) >= 2 and     # Multiple seasons represented
                len(teams_with_players) >= 25 and  # Most teams have players
                len(star_players_found) >= 3  # Found some star players
            )
            
            details = f"{total_players} players, {len(seasons)} seasons, {len(teams_with_players)} teams, stars: {', '.join(star_players_found[:3])}"
            self.log_test_result("Historical Data", success, details)
            
            return success
            
        except Exception as e:
            self.log_test_result("Historical Data", False, f"Exception: {e}")
            return False
    
    async def test_daily_update_system(self) -> bool:
        """Test daily update system (without actually running full update)"""
        print("\n🔄 Testing Daily Update System...")
        
        try:
            # Test that the data service is properly initialized
            if not hasattr(data_service, 'supabase') or not data_service._team_cache:
                self.log_test_result("Daily Update System", False, "Data service not properly initialized")
                return False
            
            # Test team mapping functionality
            yankees_id = data_service._get_team_id('NYY')
            dodgers_id = data_service._get_team_id('LAD')
            
            if not yankees_id or not dodgers_id:
                self.log_test_result("Daily Update System", False, "Team mappings not working")
                return False
            
            # Check that update methods exist
            required_methods = ['update_current_season_stats', 'check_roster_moves', 'run_daily_update']
            missing_methods = [method for method in required_methods if not hasattr(data_service, method)]
            
            if missing_methods:
                self.log_test_result("Daily Update System", False, f"Missing methods: {missing_methods}")
                return False
            
            self.log_test_result("Daily Update System", True, f"All methods available, {len(data_service._team_cache)} teams mapped")
            return True
            
        except Exception as e:
            self.log_test_result("Daily Update System", False, f"Exception: {e}")
            return False
    
    async def test_monitoring_system(self) -> bool:
        """Test monitoring and validation system"""
        print("\n📊 Testing Monitoring System...")
        
        try:
            # Generate health report
            health_report = await monitoring_service.generate_health_report()
            
            # Check report structure
            required_sections = ['freshness', 'quality', 'system', 'overall_status', 'summary']
            missing_sections = [section for section in required_sections if section not in health_report]
            
            if missing_sections:
                self.log_test_result("Monitoring System", False, f"Missing report sections: {missing_sections}")
                return False
            
            # Check that it detected our data
            summary = health_report.get('summary', {})
            total_players = summary.get('total_players', 0)
            quality_score = summary.get('quality_score', 0)
            database_accessible = summary.get('database_accessible', False)
            
            success = (
                total_players >= 200 and
                quality_score >= 95 and
                database_accessible
            )
            
            details = f"{total_players} players, {quality_score}% quality, DB: {'✅' if database_accessible else '❌'}"
            self.log_test_result("Monitoring System", success, details)
            
            return success
            
        except Exception as e:
            self.log_test_result("Monitoring System", False, f"Exception: {e}")
            return False
    
    async def test_prospect_seeding_readiness(self) -> bool:
        """Test prospect seeding script readiness"""
        print("\n🌟 Testing Prospect System Readiness...")
        
        try:
            # Check if prospects table exists
            try:
                result = supabase_mcp.supabase.table('prospects').select('count').execute()
                prospects_table_exists = True
                prospect_count = len(result.data)
            except Exception:
                prospects_table_exists = False
                prospect_count = 0
            
            # Check if prospect seeding script exists and is importable
            try:
                import seed_prospects
                script_exists = True
            except Exception:
                script_exists = False
            
            if prospects_table_exists and prospect_count > 0:
                self.log_test_result("Prospect System", True, f"Table exists with {prospect_count} prospects")
                return True
            elif prospects_table_exists and script_exists:
                self.log_test_result("Prospect System", True, "Table exists, ready for seeding")
                return True
            elif script_exists:
                self.log_test_result("Prospect System", False, "Script ready but table needs to be created manually")
                return False
            else:
                self.log_test_result("Prospect System", False, "Missing components")
                return False
                
        except Exception as e:
            self.log_test_result("Prospect System", False, f"Exception: {e}")
            return False
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all system tests"""
        print("🧪 Baseball Trade AI - Comprehensive System Test")
        print("=" * 60)
        
        # Run all tests
        test_functions = [
            ("Database Connection", self.test_database_connection),
            ("MCP Integration", self.test_mcp_integration),
            ("Historical Data", self.test_historical_data),
            ("Daily Update System", self.test_daily_update_system),
            ("Monitoring System", self.test_monitoring_system),
            ("Prospect System", self.test_prospect_seeding_readiness),
        ]
        
        for test_name, test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                self.log_test_result(test_name, False, f"Test crashed: {e}")
        
        # Calculate final results
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['duration'] = (
            datetime.fromisoformat(self.test_results['end_time']) - 
            datetime.fromisoformat(self.test_results['start_time'])
        ).total_seconds()
        
        success_rate = (self.test_results['tests_passed'] / self.test_results['tests_run']) * 100 if self.test_results['tests_run'] > 0 else 0
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Duration: {self.test_results['duration']:.2f} seconds")
        print(f"🧪 Tests Run: {self.test_results['tests_run']}")
        print(f"✅ Tests Passed: {self.test_results['tests_passed']}")
        print(f"❌ Tests Failed: {self.test_results['tests_failed']}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['failures']:
            print("\n❌ FAILURES:")
            for failure in self.test_results['failures']:
                print(f"   • {failure['test']}: {failure['details']}")
        
        if success_rate >= 90:
            print("\n🎉 SYSTEM STATUS: EXCELLENT - Ready for production!")
        elif success_rate >= 75:
            print("\n✅ SYSTEM STATUS: GOOD - Minor issues to resolve")
        elif success_rate >= 50:
            print("\n⚠️  SYSTEM STATUS: FAIR - Several issues need attention")
        else:
            print("\n🚨 SYSTEM STATUS: POOR - Major issues require fixing")
        
        return self.test_results

async def main():
    """Run comprehensive system test"""
    tester = SystemTester()
    results = await tester.run_comprehensive_test()
    
    # Save results to file
    with open('system_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: system_test_results.json")
    
    # Return exit code based on success rate
    success_rate = (results['tests_passed'] / results['tests_run']) * 100 if results['tests_run'] > 0 else 0
    return 0 if success_rate >= 75 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)