#!/usr/bin/env python3
"""
Baseball Trade AI - Startup Health Check
Validates that all core systems are working before starting the server
"""

import asyncio
import os
import sys
from datetime import datetime

def check_environment():
    """Check required environment variables"""
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_SECRET_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ Environment variables configured")
    return True

def check_imports():
    """Check critical imports"""
    try:
        import crewai
        print(f"✅ CrewAI version {crewai.__version__ if hasattr(crewai, '__version__') else 'unknown'}")
    except ImportError:
        print("❌ CrewAI not installed")
        return False
    
    try:
        import fastapi
        print("✅ FastAPI available")
    except ImportError:
        print("❌ FastAPI not installed") 
        return False
    
    try:
        from agents.front_office import FrontOfficeAgents
        commissioner = FrontOfficeAgents.create_commissioner()
        print(f"✅ Agent system working ({len(commissioner.tools)} tools loaded)")
    except Exception as e:
        print(f"⚠️  Agent system has issues: {e}")
        print("   (System can still run with basic functionality)")
    
    return True

async def check_database():
    """Check database connectivity"""
    try:
        from services.supabase_service import supabase_service
        health = await supabase_service.health_check()
        
        if health['status'] == 'healthy':
            print(f"✅ Database connected ({health['teams_count']} teams loaded)")
            return True
        else:
            print(f"❌ Database unhealthy: {health}")
            return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def main():
    """Run all startup checks"""
    print("🚀 Baseball Trade AI - Startup Health Check")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 3
    
    # Environment check
    if check_environment():
        checks_passed += 1
    
    # Import check  
    if check_imports():
        checks_passed += 1
    
    # Database check
    if await check_database():
        checks_passed += 1
    
    print("=" * 50)
    print(f"Health Check Results: {checks_passed}/{total_checks} passed")
    
    if checks_passed == total_checks:
        print("✅ All systems ready! Safe to start server.")
        return 0
    elif checks_passed >= 2:
        print("⚠️  Some issues detected, but core functionality should work.")
        return 0  
    else:
        print("❌ Critical issues detected. Please fix before starting.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)