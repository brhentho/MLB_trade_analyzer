"""
Scheduled Task Service for Baseball Trade AI
Handles automatic data updates and maintenance tasks
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading

from data_ingestion import data_service
from supabase_service import supabase_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Service for managing scheduled tasks like data updates
    """
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        
    def start(self):
        """Start the scheduler service"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting scheduler service...")
        
        # Schedule daily data updates at 6 AM ET
        schedule.every().day.at("06:00").do(self._run_daily_update)
        
        # Schedule weekly cleanup on Sundays at 3 AM ET
        schedule.every().sunday.at("03:00").do(self._run_weekly_cleanup)
        
        # Schedule health checks every hour
        schedule.every().hour.do(self._run_health_check)
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Scheduler service started successfully")
    
    def stop(self):
        """Stop the scheduler service"""
        logger.info("Stopping scheduler service...")
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        logger.info("Scheduler service stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _run_daily_update(self):
        """Run daily data update task"""
        logger.info("Starting scheduled daily data update...")
        try:
            asyncio.run(self._async_daily_update())
        except Exception as e:
            logger.error(f"Daily update failed: {e}")
    
    
    def _run_weekly_cleanup(self):
        """Run weekly cleanup task"""
        logger.info("Starting scheduled weekly cleanup...")
        try:
            asyncio.run(self._async_weekly_cleanup())
        except Exception as e:
            logger.error(f"Weekly cleanup failed: {e}")
    
    def _run_health_check(self):
        """Run system health check"""
        try:
            asyncio.run(self._async_health_check())
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def _async_daily_update(self):
        """Async daily update implementation"""
        start_time = datetime.now()
        logger.info("Running comprehensive daily data update...")
        
        try:
            # Run full data ingestion
            result = await data_service.run_daily_update()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Daily update completed in {duration:.2f} seconds")
            logger.info(f"Results: {result}")
            
            # Store update results in database for tracking
            await self._log_update_result("daily_update", result, duration)
            
        except Exception as e:
            logger.error(f"Daily update error: {e}")
            await self._log_update_result("daily_update", {"error": str(e)}, 0, error=True)
    
    
    async def _async_weekly_cleanup(self):
        """Async weekly cleanup implementation"""
        logger.info("Running weekly cleanup...")
        
        try:
            # Clean up old trade analyses (keep last 30 days)
            cleanup_result = await supabase_service.cleanup_old_data(days_old=30)
            
            logger.info(f"Weekly cleanup completed: {cleanup_result}")
            
        except Exception as e:
            logger.error(f"Weekly cleanup error: {e}")
    
    async def _async_health_check(self):
        """Async health check implementation"""
        try:
            health = await supabase_service.health_check()
            
            if health['status'] != 'healthy':
                logger.warning(f"System health issue detected: {health}")
            
            # Could send alerts here if unhealthy
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    async def _log_update_result(self, update_type: str, result: Dict[str, Any], 
                               duration: float, error: bool = False):
        """Log update results to database"""
        try:
            # This could be stored in a separate updates log table
            # For now, just log to console
            logger.info(f"Update logged - Type: {update_type}, Duration: {duration}s, Error: {error}")
        except Exception as e:
            logger.error(f"Failed to log update result: {e}")
    
    # Manual trigger methods (for API endpoints)
    async def trigger_data_update(self) -> Dict[str, Any]:
        """Manually trigger data update"""
        logger.info("Manual data update triggered")
        
        try:
            result = await data_service.run_daily_update()
            return {
                "status": "success",
                "message": "Data update completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Manual data update failed: {e}")
            return {
                "status": "error",
                "message": f"Data update failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "running": self.is_running,
            "next_daily_update": schedule.jobs[0].next_run.isoformat() if schedule.jobs else None,
            "scheduled_jobs": len(schedule.jobs),
            "last_check": datetime.now().isoformat()
        }

# Singleton instance
scheduler_service = SchedulerService()

# Auto-start scheduler when module is imported (optional)
# scheduler_service.start()

if __name__ == "__main__":
    # Test the scheduler
    print("Starting scheduler service test...")
    scheduler_service.start()
    
    try:
        # Keep running for testing
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping scheduler service...")
        scheduler_service.stop()