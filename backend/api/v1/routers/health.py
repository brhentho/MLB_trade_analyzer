"""
Health Check API Endpoints - V1
Comprehensive system health monitoring for load balancers and monitoring
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ...models import SystemHealth
from ....services.supabase_service import supabase_service
from ....services.cache_service import CacheService
from ....performance_config import monitor, cache
from ...exceptions import DatabaseException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])
cache_service = CacheService()

# Health check configuration
HEALTH_CACHE_TTL = 30  # 30 seconds
DETAILED_HEALTH_TTL = 60  # 1 minute


@router.get("", response_model=Dict)
async def health_check() -> Dict:
    """
    Basic health check endpoint for load balancers
    Fast response with essential system status
    """
    start_time = time.time()
    
    try:
        # Quick database connectivity check
        db_health = await supabase_service.health_check()
        is_healthy = db_health.get('status') == 'healthy'
        
        response = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        
        # Return appropriate HTTP status
        if is_healthy:
            return response
        else:
            return JSONResponse(status_code=503, content=response)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        response = {
            'status': 'unhealthy',
            'error': 'Database connectivity failed',
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        return JSONResponse(status_code=503, content=response)


@router.get("/detailed", response_model=SystemHealth)
async def detailed_health_check() -> SystemHealth:
    """
    Comprehensive health check with system details
    Includes database, cache, and service status
    """
    try:
        # Check if we have cached health data
        cached_health = await cache_service.get('system_health_detailed')
        if cached_health:
            return SystemHealth(**cached_health)
        
        start_time = time.time()
        
        # Database health check
        db_health = await supabase_service.health_check()
        
        # Get available teams
        teams = await supabase_service.get_all_teams()
        available_teams = [team['team_key'] for team in teams]
        
        # Count active analyses
        recent_analyses = await supabase_service.get_recent_trade_analyses(limit=100)
        active_count = len([a for a in recent_analyses if a['status'] in ['queued', 'analyzing']])
        
        # Cache status
        cache_status = "healthy"
        try:
            await cache_service.get('test_key')  # Test cache connectivity
        except:
            cache_status = "degraded"
        
        # Build comprehensive health response
        system_health = SystemHealth(
            service="Baseball Trade AI - V1",
            version="1.0.0",
            status="healthy" if db_health.get('status') == 'healthy' else "degraded",
            timestamp=datetime.now(),
            available_teams=available_teams,
            departments=[
                "Front Office Leadership",
                "Scouting Department",
                "Analytics Department", 
                "Player Development",
                "Business Operations",
                "Team Management",
                "Commissioner Office"
            ],
            database_status=db_health.get('status', 'unknown'),
            cache_status=cache_status,
            active_analyses=active_count
        )
        
        # Cache the health status
        await cache_service.set(
            'system_health_detailed', 
            system_health.dict(), 
            ttl=DETAILED_HEALTH_TTL
        )
        
        # Log health check performance
        response_time = (time.time() - start_time) * 1000
        logger.info(f"Detailed health check completed in {response_time:.2f}ms")
        
        return system_health
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise DatabaseException(f"Health check failed: {str(e)}")


@router.get("/readiness", response_model=Dict)
async def readiness_check() -> Dict:
    """
    Kubernetes readiness probe endpoint
    Checks if service is ready to receive traffic
    """
    checks = {}
    overall_ready = True
    
    try:
        # Database readiness
        try:
            db_health = await asyncio.wait_for(supabase_service.health_check(), timeout=5.0)
            checks['database'] = {
                'ready': db_health.get('status') == 'healthy',
                'teams_count': db_health.get('teams_count', 0)
            }
            if not checks['database']['ready']:
                overall_ready = False
        except asyncio.TimeoutError:
            checks['database'] = {'ready': False, 'error': 'timeout'}
            overall_ready = False
        except Exception as e:
            checks['database'] = {'ready': False, 'error': str(e)}
            overall_ready = False
        
        # Cache readiness
        try:
            await cache_service.get('readiness_test')
            checks['cache'] = {'ready': True}
        except Exception as e:
            checks['cache'] = {'ready': False, 'error': str(e)}
            # Cache failure doesn't make service unready, just degraded
        
        # Environment variables check
        required_env = ['SUPABASE_URL', 'SUPABASE_SECRET_KEY']
        env_ready = all(os.getenv(var) for var in required_env)
        checks['environment'] = {
            'ready': env_ready,
            'missing_vars': [var for var in required_env if not os.getenv(var)]
        }
        if not env_ready:
            overall_ready = False
        
        response = {
            'ready': overall_ready,
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }
        
        if overall_ready:
            return response
        else:
            return JSONResponse(status_code=503, content=response)
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'ready': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


@router.get("/liveness", response_model=Dict)
async def liveness_check() -> Dict:
    """
    Kubernetes liveness probe endpoint
    Checks if service is alive and should not be restarted
    """
    try:
        # Basic application liveness - can we respond to requests?
        return {
            'alive': True,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': time.time() - getattr(liveness_check, 'start_time', time.time()),
            'pid': os.getpid()
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'alive': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

# Store start time for uptime calculation
liveness_check.start_time = time.time()


@router.get("/metrics", response_model=Dict)
async def get_system_metrics() -> Dict:
    """
    System performance metrics endpoint
    Provides detailed performance and usage statistics
    """
    try:
        # Get performance stats from monitor
        performance_stats = {}
        if monitor:
            performance_stats = monitor.get_performance_stats()
        
        # Get cache statistics
        cache_stats = {
            'enabled': cache is not None,
            'type': 'redis' if cache and hasattr(cache, 'redis_client') and cache.redis_client else 'memory'
        }
        
        if hasattr(cache, 'memory_cache'):
            cache_stats['memory_entries'] = len(cache.memory_cache)
        
        # Database statistics
        db_stats = await supabase_service.health_check()
        
        # System resource usage (basic)
        import psutil
        system_stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'performance': performance_stats,
            'cache': cache_stats,
            'database': db_stats,
            'system': system_stats,
            'api_version': '1.0.0'
        }
        
    except ImportError:
        # psutil not available, return basic metrics
        return {
            'timestamp': datetime.now().isoformat(),
            'performance': performance_stats if 'performance_stats' in locals() else {},
            'cache': cache_stats if 'cache_stats' in locals() else {},
            'database': db_stats if 'db_stats' in locals() else {},
            'system': {'note': 'System metrics require psutil package'},
            'api_version': '1.0.0'
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics unavailable: {str(e)}")


@router.get("/startup", response_model=Dict)
async def startup_check() -> Dict:
    """
    Kubernetes startup probe endpoint
    Checks if service has completed startup and is ready for readiness checks
    """
    try:
        startup_checks = {}
        all_started = True
        
        # Check database schema is ready
        try:
            teams = await supabase_service.get_all_teams()
            startup_checks['database_schema'] = {
                'started': len(teams) > 0,
                'teams_loaded': len(teams)
            }
            if len(teams) == 0:
                all_started = False
        except Exception as e:
            startup_checks['database_schema'] = {'started': False, 'error': str(e)}
            all_started = False
        
        # Check cache initialization
        try:
            if cache:
                # Test cache functionality
                await cache_service.set('startup_test', 'ok', ttl=10)
                test_value = await cache_service.get('startup_test')
                startup_checks['cache_system'] = {'started': test_value == 'ok'}
            else:
                startup_checks['cache_system'] = {'started': True, 'note': 'Cache system disabled'}
        except Exception as e:
            startup_checks['cache_system'] = {'started': False, 'error': str(e)}
            # Cache failure doesn't prevent startup
        
        response = {
            'started': all_started,
            'timestamp': datetime.now().isoformat(),
            'startup_checks': startup_checks,
            'startup_duration_seconds': time.time() - getattr(startup_check, 'init_time', time.time())
        }
        
        if all_started:
            return response
        else:
            return JSONResponse(status_code=503, content=response)
            
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'started': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )

# Store initialization time for startup duration calculation
startup_check.init_time = time.time()