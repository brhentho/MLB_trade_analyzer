#!/usr/bin/env python3
"""
Setup script for Baseball Trade AI Supabase integration
This script will help set up the database schema and initial data
"""

import os
import asyncio
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("Please set these in your .env file:")
        logger.info("SUPABASE_URL=your_supabase_project_url")
        logger.info("SUPABASE_SECRET_KEY=your_supabase_service_role_key")
        return False
    
    return True

async def setup_database():
    """Set up the database schema and initial data"""
    try:
        # Import our service
        from backend.services.supabase_service import supabase_service
        
        # Test connection
        logger.info("Testing database connection...")
        health = await supabase_service.health_check()
        
        if health['status'] == 'healthy':
            logger.info("✅ Database connection successful!")
            logger.info(f"Found {health['teams_count']} teams in database")
            
            # Check if we need to seed data
            if health['teams_count'] == 0:
                logger.warning("⚠️  No teams found in database")
                logger.info("Please run the migration files in supabase/migrations/ to set up your database")
                logger.info("You can do this through the Supabase dashboard or CLI")
            else:
                logger.info("✅ Database appears to be set up correctly!")
                
        else:
            logger.error("❌ Database connection failed")
            logger.error(f"Error: {health.get('error', 'Unknown error')}")
            return False
            
    except ImportError:
        logger.error("❌ Cannot import Supabase service")
        logger.info("Make sure you have installed the required dependencies:")
        logger.info("pip install supabase")
        return False
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False
    
    return True

def show_next_steps():
    """Show next steps for the user"""
    logger.info("\n" + "="*50)
    logger.info("NEXT STEPS:")
    logger.info("="*50)
    logger.info("1. If you haven't already, create a Supabase project at https://supabase.com")
    logger.info("2. Run the migration files in supabase/migrations/:")
    logger.info("   - 20241205000001_initial_schema.sql")
    logger.info("   - 20241205000002_seed_teams.sql")
    logger.info("3. Update your .env file with the correct Supabase credentials")
    logger.info("4. Install required Python packages:")
    logger.info("   pip install supabase")
    logger.info("5. Start your backend server:")
    logger.info("   python main.py")
    logger.info("="*50)

async def main():
    """Main setup function"""
    logger.info("🏟️  Baseball Trade AI - Supabase Setup")
    logger.info("="*50)
    
    # Check environment variables
    if not check_environment():
        logger.info("\n📝 Please update your .env file with Supabase credentials")
        show_next_steps()
        return
    
    # Set up database
    success = await setup_database()
    
    if success:
        logger.info("\n✅ Setup completed successfully!")
        logger.info("Your Baseball Trade AI backend is ready to use with Supabase!")
    else:
        logger.info("\n❌ Setup encountered issues")
        show_next_steps()

if __name__ == "__main__":
    asyncio.run(main())