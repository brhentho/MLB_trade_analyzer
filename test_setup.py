#!/usr/bin/env python3
"""
Test script to verify Supabase setup and data pipeline
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_supabase_connection():
    """Test connection to Supabase and verify schema"""
    print("🔍 Testing Supabase Connection...")
    
    try:
        # Get credentials
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SECRET_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials in .env file")
            return False
        
        if supabase_url == 'https://your-project-id.supabase.co':
            print("❌ Please update .env file with your actual Supabase URL")
            return False
        
        # Create client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection by querying teams
        print("📊 Testing database connection...")
        teams_response = supabase.table('teams').select('*').limit(5).execute()
        
        if teams_response.data:
            print(f"✅ Connected! Found {len(teams_response.data)} teams in database")
            for team in teams_response.data[:3]:
                print(f"   - {team['name']} ({team['abbreviation']})")
            return True
        else:
            print("❌ No teams found. Please run the migration files first.")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_data_fetching():
    """Test basic data fetching functionality"""
    print("\n🏟️  Testing Data Fetching...")
    
    try:
        import pybaseball as pb
        
        # Test a simple pybaseball query (2024 season, limited data)
        print("📈 Fetching sample 2024 batting stats...")
        batting_data = pb.batting_stats(2024)
        
        if not batting_data.empty:
            print(f"✅ Successfully fetched {len(batting_data)} batting records")
            print(f"   Sample players: {', '.join(batting_data['Name'].head(3).tolist())}")
            return True
        else:
            print("❌ No batting data retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Data fetching failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🏟️  Baseball Trade AI - Setup Verification")
    print("=" * 50)
    
    # Test 1: Supabase connection
    supabase_ok = await test_supabase_connection()
    
    # Test 2: Data fetching
    data_ok = await test_data_fetching()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 SETUP VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"🔗 Supabase Connection: {'✅ PASS' if supabase_ok else '❌ FAIL'}")
    print(f"📊 Data Fetching: {'✅ PASS' if data_ok else '❌ FAIL'}")
    
    if supabase_ok and data_ok:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Update your .env file with actual Supabase credentials if you haven't already")
        print("2. Run: python3 seed_historical_data.py")
        print("3. This will populate your database with 3 years of MLB data")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        if not supabase_ok:
            print("   - Check your Supabase URL and service role key in .env")
            print("   - Make sure you ran the migration files in Supabase SQL Editor")
        if not data_ok:
            print("   - Check your internet connection")
            print("   - pybaseball may have rate limiting - try again in a few minutes")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)