"""
Enhanced Health Check API Endpoints - Production Ready
Comprehensive system health monitoring with advanced features
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from ...optimized_models import SystemHealth
from ....services.supabase_service import supabase_service
from ....services.cache_service import cache_service
from ....services.advanced_queue_service import advanced_queue_service
from ....monitoring.health_checks import health_monitor
from ....middleware.monitoring import get_monitoring_stats
from ....security.auth import get_current_user, require_roles
from ...exceptions import DatabaseException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Enhanced Health"])

# Health check configuration
HEALTH_CACHE_TTL = 30  # 30 seconds
DETAILED_HEALTH_TTL = 60  # 1 minute
STARTUP_TIME = time.time()


@router.get("", response_model=Dict[str, Any])
async def basic_health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for load balancers
    Ultra-fast response with essential system status only
    """
    start_time = time.time()
    
    try:
        # Quick database connectivity check with timeout
        db_health = await asyncio.wait_for(
            supabase_service.health_check(), 
            timeout=2.0
        )
        is_healthy = db_health.get('status') == 'healthy'
        
        response = {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0-production',
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'uptime_seconds': int(time.time() - STARTUP_TIME)
        }
        
        status_code = 200 if is_healthy else 503
        return JSONResponse(status_code=status_code, content=response)
        
    except asyncio.TimeoutError:
        response = {
            'status': 'timeout',
            'error': 'Database health check timed out',
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        return JSONResponse(status_code=503, content=response)
        
    except Exception as e:
        logger.error(f"Basic health check failed: {e}")
        response = {
            'status': 'error',
            'error': 'Health check failed',
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2)
        }
        return JSONResponse(status_code=503, content=response)


@router.get("/comprehensive", response_model=Dict[str, Any])
async def comprehensive_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check using our advanced monitoring system
    Performs all registered health checks and returns detailed status
    """
    try:
        # Use cached results if available
        cached_health = await cache_service.get('comprehensive_health')
        if cached_health:
            return cached_health
        
        # Perform comprehensive health checks
        health_report = await health_monitor.perform_health_checks()
        
        # Cache the results
        await cache_service.set(
            'comprehensive_health', 
            health_report, 
            ttl=HEALTH_CACHE_TTL
        )
        
        # Return appropriate HTTP status
        overall_status = health_report["overall_status"]
        if overall_status == "healthy":
            status_code = 200
        elif overall_status == "degraded":
            status_code = 200  # Still serving traffic
        else:  # unhealthy or critical
            status_code = 503
        
        return JSONResponse(status_code=status_code, content=health_report)
        
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}")
        error_response = {
            "overall_status": "error",
            "message": f"Health check system failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        return JSONResponse(status_code=500, content=error_response)


@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_system_health() -> Dict[str, Any]:
    """
    Detailed system health with business-specific metrics
    Includes service-specific health information
    """
    try:
        # Get cached detailed health if available
        cached_health = await cache_service.get('detailed_system_health')
        if cached_health:
            return cached_health
        
        start_time = time.time()
        
        # Parallel execution of health checks
        health_tasks = [
            supabase_service.health_check(),
            cache_service.get_stats(),
            advanced_queue_service.get_queue_stats() if advanced_queue_service.running else asyncio.sleep(0),
            _get_teams_info(),
            _get_analyses_info()
        ]
        
        results = await asyncio.gather(*health_tasks, return_exceptions=True)
        db_health, cache_stats, queue_stats, teams_info, analyses_info = results
        
        # Handle any exceptions in results
        if isinstance(db_health, Exception):
            db_health = {"status": "error", "error": str(db_health)}
        if isinstance(cache_stats, Exception):
            cache_stats = {"enabled": False, "error": str(cache_stats)}
        if isinstance(queue_stats, Exception):
            queue_stats = {"running": False, "error": str(queue_stats)}
        if isinstance(teams_info, Exception):
            teams_info = {"total_teams": 0, "error": str(teams_info)}
        if isinstance(analyses_info, Exception):
            analyses_info = {"active_analyses": 0, "error": str(analyses_info)}
        
        # Determine overall system status
        overall_status = "healthy"
        if db_health.get("status") != "healthy":
            overall_status = "unhealthy"
        elif not cache_stats.get("enabled", False):
            overall_status = "degraded"
        elif not queue_stats.get("running", False):
            overall_status = "degraded"
        
        # Build detailed response
        detailed_health = {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "uptime_seconds": int(time.time() - STARTUP_TIME),
            "service_info": {
                "name": "Baseball Trade AI",
                "version": "2.0.0-production",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "api_version": "v1"
            },
            "components": {
                "database": {
                    "status": db_health.get("status", "unknown"),
                    "details": db_health
                },
                "cache": {
                    "status": "healthy" if cache_stats.get("enabled") else "disabled",
                    "details": cache_stats
                },
                "queue": {
                    "status": "healthy" if queue_stats.get("running") else "stopped",
                    "details": queue_stats
                },
                "ai_service": {
                    "status": "configured" if os.getenv('OPENAI_API_KEY') else "not_configured",
                    "details": {
                        "openai_key_present": bool(os.getenv('OPENAI_API_KEY')),
                        "crewai_available": True  # Would check actual import
                    }
                }
            },
            "business_metrics": {
                **teams_info,
                **analyses_info,
                "features_enabled": [
                    "natural_language_processing",
                    "multi_agent_analysis",
                    "real_time_data",
                    "background_processing",
                    "comprehensive_monitoring"
                ]
            }
        }
        
        # Cache the detailed health
        await cache_service.set(
            'detailed_system_health',
            detailed_health,
            ttl=DETAILED_HEALTH_TTL
        )
        
        return detailed_health
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Detailed health check failed: {str(e)}"
        )


@router.get("/readiness", response_model=Dict[str, Any])
async def kubernetes_readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe - checks if service can receive traffic
    """
    checks = {}
    overall_ready = True
    start_time = time.time()
    
    try:
        # Database readiness with timeout
        try:
            db_check = await asyncio.wait_for(
                supabase_service.health_check(),
                timeout=5.0
            )
            checks['database'] = {
                'ready': db_check.get('status') == 'healthy',
                'details': db_check
            }
            if not checks['database']['ready']:
                overall_ready = False
        except asyncio.TimeoutError:
            checks['database'] = {'ready': False, 'error': 'timeout'}
            overall_ready = False
        except Exception as e:
            checks['database'] = {'ready': False, 'error': str(e)}
            overall_ready = False
        
        # Cache readiness (non-blocking)
        try:
            cache_stats = await cache_service.get_stats()
            checks['cache'] = {
                'ready': True,
                'enabled': cache_stats.get('enabled', False),
                'type': 'redis' if cache_stats.get('redis_available') else 'memory'
            }
        except Exception as e:
            checks['cache'] = {'ready': True, 'error': str(e), 'note': 'Cache failure is non-blocking'}
        
        # Queue service readiness (non-blocking)
        try:
            if advanced_queue_service.running:
                queue_stats = advanced_queue_service.get_queue_stats()
                checks['queue'] = {
                    'ready': True,
                    'running': queue_stats.get('running', False),
                    'active_workers': queue_stats.get('active_workers', 0)
                }
            else:
                checks['queue'] = {'ready': True, 'note': 'Queue service not started'}
        except Exception as e:
            checks['queue'] = {'ready': True, 'error': str(e), 'note': 'Queue failure is non-blocking'}
        
        # Environment readiness
        required_env = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
        missing_vars = [var for var in required_env if not os.getenv(var)]
        checks['environment'] = {
            'ready': len(missing_vars) == 0,
            'missing_variables': missing_vars
        }
        if missing_vars:
            overall_ready = False
        
        response = {
            'ready': overall_ready,
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'checks': checks,
            'uptime_seconds': int(time.time() - STARTUP_TIME)
        }
        
        status_code = 200 if overall_ready else 503
        return JSONResponse(status_code=status_code, content=response)
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'ready': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'response_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        )


@router.get("/liveness", response_model=Dict[str, Any])
async def kubernetes_liveness_probe() -> Dict[str, Any]:
    """
    Kubernetes liveness probe - checks if service is alive
    """
    try:
        return {
            'alive': True,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': int(time.time() - STARTUP_TIME),
            'pid': os.getpid(),
            'memory_usage_mb': _get_memory_usage()
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


@router.get("/metrics", response_model=Dict[str, Any])
async def system_metrics(
    include_detailed: bool = Query(False, description="Include detailed performance metrics")
) -> Dict[str, Any]:
    """
    System performance metrics endpoint
    """
    try:
        start_time = time.time()
        
        # Base metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': int(time.time() - STARTUP_TIME),
            'response_time_ms': 0,  # Will be calculated
            'service_info': {
                'name': 'Baseball Trade AI',
                'version': '2.0.0-production',
                'environment': os.getenv('ENVIRONMENT', 'development')
            }
        }
        
        # Get monitoring stats
        monitoring_stats = get_monitoring_stats()
        if monitoring_stats:
            metrics['monitoring'] = monitoring_stats
        
        # Queue metrics
        if advanced_queue_service.running:
            metrics['queue'] = advanced_queue_service.get_queue_stats()
        
        # Cache metrics
        try:
            cache_stats = await cache_service.get_stats()
            metrics['cache'] = cache_stats
        except Exception as e:
            metrics['cache'] = {'error': str(e)}
        
        # System resource metrics (if detailed requested)
        if include_detailed:
            try:
                import psutil
                metrics['system_resources'] = {
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory': {
                        'percent': psutil.virtual_memory().percent,
                        'available_gb': psutil.virtual_memory().available / (1024**3)
                    },
                    'disk': {
                        'percent': psutil.disk_usage('/').percent,
                        'free_gb': psutil.disk_usage('/').free / (1024**3)
                    }
                }
            except ImportError:
                metrics['system_resources'] = {'note': 'psutil not available'}
            except Exception as e:
                metrics['system_resources'] = {'error': str(e)}
        
        # Calculate and add response time
        metrics['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Metrics collection failed: {str(e)}"
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_system_alerts(
    current_user: Dict = Depends(get_current_user),
    active_only: bool = Query(True, description="Return only active alerts"),
    hours: int = Query(24, ge=1, le=168, description="Alert history in hours")
) -> Dict[str, Any]:
    """
    Get system alerts and monitoring notifications
    Requires authentication
    """
    try:
        if active_only:
            alerts = health_monitor.get_active_alerts()
            alert_type = "active"
        else:
            alerts = health_monitor.get_alert_history(hours=hours)
            alert_type = f"last_{hours}h"
        
        return {
            'alert_type': alert_type,
            'total_alerts': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.now().isoformat(),
            'severity_counts': _count_alerts_by_severity(alerts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: Dict = Depends(require_roles(["admin", "ops"]))
) -> Dict[str, Any]:
    """
    Acknowledge a system alert
    Requires admin or ops role
    """
    try:
        success = health_monitor.acknowledge_alert(alert_id)
        
        if success:
            return {
                'acknowledged': True,
                'alert_id': alert_id,
                'acknowledged_by': current_user.get('username'),
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Alert {alert_id} not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.get("/trends", response_model=Dict[str, Any])
async def health_trends(
    current_user: Dict = Depends(get_current_user),
    hours: int = Query(24, ge=1, le=168, description="Trend period in hours")
) -> Dict[str, Any]:
    """
    Get health trends and patterns over time
    Requires authentication
    """
    try:
        trends = health_monitor.get_health_trends(hours=hours)
        return trends
        
    except Exception as e:
        logger.error(f"Failed to get health trends: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve health trends: {str(e)}"
        )


# Helper functions
async def _get_teams_info() -> Dict[str, Any]:
    """Get teams information for health check"""
    try:
        teams = await supabase_service.get_all_teams()
        return {
            'total_teams': len(teams),
            'teams_available': True
        }
    except Exception as e:
        return {
            'total_teams': 0,
            'teams_available': False,
            'error': str(e)
        }


async def _get_analyses_info() -> Dict[str, Any]:
    """Get trade analyses information for health check"""
    try:
        recent_analyses = await supabase_service.get_recent_trade_analyses(limit=100)
        active_count = len([
            a for a in recent_analyses 
            if a.get('status') in ['queued', 'analyzing', 'processing']
        ])
        
        return {
            'active_analyses': active_count,
            'recent_analyses': len(recent_analyses)
        }
    except Exception as e:
        return {
            'active_analyses': 0,
            'recent_analyses': 0,
            'error': str(e)
        }


def _get_memory_usage() -> float:
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return round(process.memory_info().rss / (1024 * 1024), 2)
    except ImportError:
        return 0.0


def _count_alerts_by_severity(alerts: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count alerts by severity level"""
    severity_counts = {'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
    
    for alert in alerts:
        severity = alert.get('severity', 'unknown')
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    return severity_counts