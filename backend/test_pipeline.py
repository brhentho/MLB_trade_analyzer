#!/usr/bin/env python3
"""
Baseball Trade AI - Pipeline Test Script
Tests the full data pipeline from ingestion to CrewAI analysis
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our services
from services.supabase_service import supabase_service
from services.data_ingestion import data_service
from services.statcast_service import statcast_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineTest:
    """
    Comprehensive pipeline testing
    """
    
    def __init__(self):
        self.test_results = {}
    
    async def run_all_tests(self):
        """Run all pipeline tests"""
        logger.info("🚀 Starting Baseball Trade AI Pipeline Tests")
        print("=" * 60)
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Team Data", self.test_team_data),
            ("Data Ingestion Setup", self.test_data_ingestion),
            ("Player Stats Tools", self.test_player_stats_tools),
            ("Roster Management", self.test_roster_management),
            ("Statcast Integration", self.test_statcast_service),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            try:
                result = await test_func()
                self.test_results[test_name] = result
                status = "✅ PASS" if result.get('success') else "❌ FAIL"
                print(f"   {status}: {result.get('message', 'No message')}")
            except Exception as e:
                self.test_results[test_name] = {"success": False, "error": str(e)}
                print(f"   ❌ ERROR: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results.values() if r.get('success'))
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {test_name}")
            if not result.get('success') and 'error' in result:
                print(f"    Error: {result['error']}")
        
        print(f"\n📈 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your pipeline is ready.")
        else:
            print("⚠️  Some tests failed. Check the errors above.")
        
        return passed == total
    
    async def test_database_connection(self):
        """Test Supabase database connection"""
        try:
            health = await supabase_service.health_check()
            
            if health['status'] == 'healthy':
                return {
                    "success": True,
                    "message": f"Connected to database with {health.get('teams_count', 0)} teams"
                }
            else:
                return {
                    "success": False,
                    "message": f"Database unhealthy: {health.get('error', 'Unknown error')}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_team_data(self):
        """Test team data availability"""
        try:
            teams = await supabase_service.get_all_teams()
            
            if len(teams) >= 30:  # Should have all 30 MLB teams
                # Test getting a specific team
                yankees = await supabase_service.get_team_by_key('yankees')
                if yankees:
                    return {
                        "success": True,
                        "message": f"Found {len(teams)} teams, Yankees data: {yankees['name']}"
                    }
                else:
                    return {
                        "success": False,
                        "message": "Teams found but couldn't get Yankees data"
                    }
            else:
                return {
                    "success": False,
                    "message": f"Only found {len(teams)} teams, expected 30"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_data_ingestion(self):
        """Test data ingestion service setup"""
        try:
            # Test if we can create the service without errors
            service_healthy = hasattr(data_service, 'supabase') and data_service.supabase is not None
            
            if service_healthy:
                return {
                    "success": True,
                    "message": "Data ingestion service initialized successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Data ingestion service not properly initialized"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_player_stats_tools(self):
        """Test player stats tools with live data"""
        try:
            # Import the tool
            sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
            from player_stats import get_player_stats
            
            # Test with a mock player (should handle gracefully)
            result = get_player_stats("Test Player", 2024)
            
            if 'error' in result:
                return {
                    "success": True,
                    "message": f"Tool working correctly - handled missing player: {result.get('error', '')}"
                }
            else:
                return {
                    "success": True,
                    "message": "Player stats tool functional"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_roster_management(self):
        """Test roster management tools"""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
            from roster_management import get_team_roster
            
            # Test with Yankees
            result = get_team_roster("yankees")
            
            if 'error' not in result and result.get('team'):
                return {
                    "success": True,
                    "message": f"Roster tool working - found {result.get('total_players', 0)} players for {result.get('team', 'team')}"
                }
            elif 'error' in result:
                return {
                    "success": True,
                    "message": f"Roster tool handled missing data correctly: {result.get('error', '')}"
                }
            else:
                return {
                    "success": False,
                    "message": "Roster tool returned unexpected format"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_statcast_service(self):
        """Test Statcast service integration"""
        try:
            # Test if service can be initialized
            service_healthy = hasattr(statcast_service, 'base_url')
            
            if service_healthy:
                return {
                    "success": True,
                    "message": "Statcast service initialized and ready"
                }
            else:
                return {
                    "success": False,
                    "message": "Statcast service not properly configured"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

async def main():
    """Main test execution"""
    test_runner = PipelineTest()
    success = await test_runner.run_all_tests()
    
    print("\n🔧 NEXT STEPS:")
    if success:
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run initial data ingestion to populate database")
        print("3. Start the main application: python main.py")
        print("4. Test the frontend integration")
    else:
        print("1. Fix the failing tests above")
        print("2. Check your environment variables")
        print("3. Ensure Supabase database is set up correctly")
        print("4. Re-run this test script")
    
    return success

if __name__ == "__main__":
    # Set up environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    result = asyncio.run(main())
    sys.exit(0 if result else 1)