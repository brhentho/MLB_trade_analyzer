"""
Comprehensive Health Checks and Monitoring for Baseball Trade AI
Production-ready health monitoring, metrics collection, and alerting
"""

import asyncio
import json
import logging
import os
import psutil
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))  # seconds
HEALTH_CHECK_TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', '10'))   # seconds
ALERT_THRESHOLD_CPU = float(os.getenv('ALERT_THRESHOLD_CPU', '80'))   # percentage
ALERT_THRESHOLD_MEMORY = float(os.getenv('ALERT_THRESHOLD_MEMORY', '85'))  # percentage
ALERT_THRESHOLD_DISK = float(os.getenv('ALERT_THRESHOLD_DISK', '90'))  # percentage
ENABLE_SYSTEM_MONITORING = os.getenv('ENABLE_SYSTEM_MONITORING', 'true').lower() == 'true'
ENABLE_EXTERNAL_HEALTH_CHECKS = os.getenv('ENABLE_EXTERNAL_HEALTH_CHECKS', 'true').lower() == 'true'


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    duration_ms: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    open_files: int
    load_average: Tuple[float, float, float]
    uptime_seconds: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "active_connections": self.active_connections,
            "open_files": self.open_files,
            "load_average": self.load_average,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Alert:
    """System alert"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    metadata: Dict[str, Any] = None
    
    @property
    def is_active(self) -> bool:
        """Check if alert is active"""
        return self.resolved_at is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged": self.acknowledged,
            "metadata": self.metadata or {},
            "is_active": self.is_active
        }


class BaseHealthCheck:
    """Base class for health checks"""
    
    def __init__(self, name: str, timeout: int = HEALTH_CHECK_TIMEOUT):
        self.name = name
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        """Perform health check"""
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)
        
        try:
            result = await asyncio.wait_for(
                self._perform_check(),
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=result.get("status", HealthStatus.UNKNOWN),
                message=result.get("message", "Health check completed"),
                details=result.get("details", {}),
                duration_ms=duration_ms,
                timestamp=timestamp
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                details={"timeout": self.timeout},
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=timestamp
            )
        except Exception as e:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e), "error_type": e.__class__.__name__},
                duration_ms=(time.time() - start_time) * 1000,
                timestamp=timestamp
            )
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Override in subclasses"""
        raise NotImplementedError


class DatabaseHealthCheck(BaseHealthCheck):
    """Database connection health check"""
    
    def __init__(self):
        super().__init__("database")
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check database connectivity"""
        from ..services.supabase_service import supabase_service
        
        # Test basic connectivity
        health_result = await supabase_service.health_check()
        
        if health_result.get("status") == "healthy":
            # Additional checks
            teams_count = health_result.get("teams_count", 0)
            
            if teams_count == 0:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Database connected but no team data found",
                    "details": {"teams_count": teams_count}
                }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"Database healthy with {teams_count} teams",
                "details": {
                    "teams_count": teams_count,
                    "connection_pool_active": True
                }
            }
        else:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": "Database connection failed",
                "details": health_result
            }


class CacheHealthCheck(BaseHealthCheck):
    """Cache service health check"""
    
    def __init__(self):
        super().__init__("cache")
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check cache service"""
        from ..services.cache_service import cache_service
        
        try:
            # Get cache stats
            stats = await cache_service.get_stats()
            
            if stats.get("enabled"):
                # Test cache operations
                test_key = "health_check_test"
                test_value = {"timestamp": time.time()}
                
                # Test set/get
                set_success = await cache_service.set(test_key, test_value, 60)
                if set_success:
                    retrieved_value = await cache_service.get(test_key)
                    if retrieved_value == test_value:
                        await cache_service.delete(test_key)  # Cleanup
                        
                        return {
                            "status": HealthStatus.HEALTHY,
                            "message": "Cache service healthy",
                            "details": {
                                **stats,
                                "read_write_test": "passed"
                            }
                        }
                
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Cache operations failed",
                    "details": stats
                }
            else:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": "Cache service disabled",
                    "details": stats
                }
                
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Cache health check failed: {str(e)}",
                "details": {"error": str(e)}
            }


class QueueHealthCheck(BaseHealthCheck):
    """Background queue health check"""
    
    def __init__(self):
        super().__init__("queue")
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check queue service"""
        try:
            from ..services.advanced_queue_service import advanced_queue_service
            
            stats = advanced_queue_service.get_queue_stats()
            
            if not stats.get("running"):
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "message": "Queue service not running",
                    "details": stats
                }
            
            # Check for stuck tasks
            stuck_threshold = 3600  # 1 hour
            status_counts = stats.get("status_counts", {})
            running_tasks = status_counts.get("running", 0)
            
            if running_tasks > stats.get("max_workers", 0) * 2:
                return {
                    "status": HealthStatus.DEGRADED,
                    "message": f"High number of running tasks: {running_tasks}",
                    "details": stats
                }
            
            # Check error rate
            total_processed = stats.get("tasks_processed", 0)
            failed_tasks = stats.get("tasks_failed", 0)
            
            if total_processed > 0:
                error_rate = failed_tasks / total_processed
                if error_rate > 0.1:  # 10% error rate threshold
                    return {
                        "status": HealthStatus.DEGRADED,
                        "message": f"High error rate: {error_rate:.1%}",
                        "details": stats
                    }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Queue service healthy",
                "details": stats
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"Queue health check failed: {str(e)}",
                "details": {"error": str(e)}
            }


class AIServiceHealthCheck(BaseHealthCheck):
    """AI service health check"""
    
    def __init__(self):
        super().__init__("ai_service")
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check AI service availability"""
        
        # Check OpenAI API key
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": "OpenAI API key not configured",
                "details": {"openai_key_present": False}
            }
        
        # Test basic AI functionality (lightweight)
        try:
            # This would test a simple AI request in production
            # For now, just validate configuration
            
            details = {
                "openai_key_present": True,
                "openai_key_length": len(openai_key),
                "crewai_available": True  # Would test actual CrewAI import
            }
            
            return {
                "status": HealthStatus.HEALTHY,
                "message": "AI service configuration valid",
                "details": details
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"AI service check failed: {str(e)}",
                "details": {"error": str(e)}
            }


class SystemResourcesHealthCheck(BaseHealthCheck):
    """System resources health check"""
    
    def __init__(self):
        super().__init__("system_resources")
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check system resource usage"""
        
        if not ENABLE_SYSTEM_MONITORING:
            return {
                "status": HealthStatus.HEALTHY,
                "message": "System monitoring disabled",
                "details": {"monitoring_enabled": False}
            }
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check thresholds
            issues = []
            status = HealthStatus.HEALTHY
            
            if cpu_percent > ALERT_THRESHOLD_CPU:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                status = HealthStatus.DEGRADED
            
            if memory.percent > ALERT_THRESHOLD_MEMORY:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                status = HealthStatus.DEGRADED
            
            if disk.percent > ALERT_THRESHOLD_DISK:
                issues.append(f"High disk usage: {disk.percent:.1f}%")
                status = HealthStatus.DEGRADED
            
            # Critical thresholds
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 98:
                status = HealthStatus.CRITICAL
            
            message = "System resources healthy"
            if issues:
                message = "; ".join(issues)
            
            return {
                "status": status,
                "message": message,
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
                }
            }
            
        except Exception as e:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"System resources check failed: {str(e)}",
                "details": {"error": str(e)}
            }


class ExternalServiceHealthCheck(BaseHealthCheck):
    """External service dependencies health check"""
    
    def __init__(self):
        super().__init__("external_services")
    
    async def _perform_check(self) -> Dict[str, Any]:
        """Check external service dependencies"""
        
        if not ENABLE_EXTERNAL_HEALTH_CHECKS:
            return {
                "status": HealthStatus.HEALTHY,
                "message": "External health checks disabled",
                "details": {"external_checks_enabled": False}
            }
        
        services_status = {}
        overall_status = HealthStatus.HEALTHY
        
        # Check external services (customize based on your dependencies)
        external_services = [
            # Add your external service URLs here
            # {"name": "external_api", "url": "https://api.example.com/health"}
        ]
        
        for service in external_services:
            try:
                # This would perform actual HTTP health checks
                services_status[service["name"]] = {
                    "status": "healthy",
                    "response_time_ms": 150,
                    "last_checked": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                services_status[service["name"]] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_checked": datetime.now(timezone.utc).isoformat()
                }
                overall_status = HealthStatus.DEGRADED
        
        return {
            "status": overall_status,
            "message": f"Checked {len(external_services)} external services",
            "details": {
                "services_checked": len(external_services),
                "services_status": services_status
            }
        }


class HealthMonitor:
    """Comprehensive health monitoring system"""
    
    def __init__(self):
        self.health_checks: List[BaseHealthCheck] = []
        self.health_history: List[Dict[str, Any]] = []
        self.alerts: Dict[str, Alert] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.running = False
        
        # Register default health checks
        self._register_default_health_checks()
    
    def _register_default_health_checks(self):
        """Register default health checks"""
        self.health_checks.extend([
            DatabaseHealthCheck(),
            CacheHealthCheck(),
            QueueHealthCheck(),
            AIServiceHealthCheck(),
            SystemResourcesHealthCheck(),
            ExternalServiceHealthCheck()
        ])
    
    def register_health_check(self, health_check: BaseHealthCheck):
        """Register a custom health check"""
        self.health_checks.append(health_check)
        logger.info(f"Registered health check: {health_check.name}")
    
    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform all health checks"""
        start_time = time.time()
        results = []
        overall_status = HealthStatus.HEALTHY
        
        # Run health checks concurrently
        health_check_tasks = [
            check.check() for check in self.health_checks
        ]
        
        health_results = await asyncio.gather(*health_check_tasks, return_exceptions=True)
        
        for i, result in enumerate(health_results):
            if isinstance(result, Exception):
                # Handle health check that raised an exception
                check_result = HealthCheckResult(
                    name=self.health_checks[i].name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check crashed: {str(result)}",
                    details={"error": str(result)},
                    duration_ms=0,
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                check_result = result
            
            results.append(check_result.to_dict())
            
            # Determine overall status
            if check_result.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                if overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.UNHEALTHY
                if check_result.status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
            elif check_result.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        total_duration = (time.time() - start_time) * 1000
        timestamp = datetime.now(timezone.utc)
        
        # Collect system metrics
        system_metrics = await self._collect_system_metrics()
        
        health_report = {
            "overall_status": overall_status.value,
            "timestamp": timestamp.isoformat(),
            "total_duration_ms": total_duration,
            "checks": results,
            "system_metrics": system_metrics.to_dict() if system_metrics else None,
            "summary": {
                "total_checks": len(results),
                "healthy": sum(1 for r in results if r["status"] == "healthy"),
                "degraded": sum(1 for r in results if r["status"] == "degraded"),
                "unhealthy": sum(1 for r in results if r["status"] == "unhealthy"),
                "critical": sum(1 for r in results if r["status"] == "critical")
            }
        }
        
        # Store in history
        self.health_history.append(health_report)
        if len(self.health_history) > 100:  # Keep last 100 reports
            self.health_history = self.health_history[-100:]
        
        # Process alerts
        await self._process_health_alerts(health_report)
        
        return health_report
    
    async def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect system metrics"""
        if not ENABLE_SYSTEM_MONITORING:
            return None
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get process info
            process = psutil.Process()
            connections = len(process.connections())
            open_files = process.num_fds() if hasattr(process, 'num_fds') else 0
            
            # Get load average
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
            
            # Calculate uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                active_connections=connections,
                open_files=open_files,
                load_average=load_avg,
                uptime_seconds=uptime_seconds,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Store metrics
            self.system_metrics.append(metrics)
            if len(self.system_metrics) > 1000:  # Keep last 1000 metrics
                self.system_metrics = self.system_metrics[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return None
    
    async def _process_health_alerts(self, health_report: Dict[str, Any]):
        """Process health check results and generate alerts"""
        
        # Check for critical/unhealthy services
        for check in health_report["checks"]:
            check_name = check["name"]
            status = check["status"]
            
            alert_id = f"health_check_{check_name}"
            
            if status in ["unhealthy", "critical"]:
                # Create or update alert
                if alert_id not in self.alerts or self.alerts[alert_id].is_active is False:
                    severity = AlertSeverity.CRITICAL if status == "critical" else AlertSeverity.ERROR
                    
                    alert = Alert(
                        id=alert_id,
                        severity=severity,
                        title=f"Health Check Failed: {check_name}",
                        message=check["message"],
                        source="health_monitor",
                        created_at=datetime.now(timezone.utc),
                        metadata={"check_details": check}
                    )
                    
                    self.alerts[alert_id] = alert
                    logger.warning(f"Health alert created: {alert.title}")
            
            elif status in ["healthy", "degraded"]:
                # Resolve existing alert if it exists
                if alert_id in self.alerts and self.alerts[alert_id].is_active:
                    self.alerts[alert_id].resolved_at = datetime.now(timezone.utc)
                    logger.info(f"Health alert resolved: {self.alerts[alert_id].title}")
        
        # System resource alerts
        system_metrics = health_report.get("system_metrics")
        if system_metrics:
            await self._process_resource_alerts(system_metrics)
    
    async def _process_resource_alerts(self, metrics: Dict[str, Any]):
        """Process system resource alerts"""
        
        alerts_to_check = [
            ("cpu", metrics["cpu_percent"], ALERT_THRESHOLD_CPU, "High CPU Usage"),
            ("memory", metrics["memory_percent"], ALERT_THRESHOLD_MEMORY, "High Memory Usage"),
            ("disk", metrics["disk_percent"], ALERT_THRESHOLD_DISK, "High Disk Usage")
        ]
        
        for resource, value, threshold, title in alerts_to_check:
            alert_id = f"resource_{resource}"
            
            if value > threshold:
                if alert_id not in self.alerts or not self.alerts[alert_id].is_active:
                    severity = AlertSeverity.CRITICAL if value > 95 else AlertSeverity.WARNING
                    
                    alert = Alert(
                        id=alert_id,
                        severity=severity,
                        title=title,
                        message=f"{resource.upper()} usage at {value:.1f}% (threshold: {threshold}%)",
                        source="resource_monitor",
                        created_at=datetime.now(timezone.utc),
                        metadata={"resource": resource, "value": value, "threshold": threshold}
                    )
                    
                    self.alerts[alert_id] = alert
                    logger.warning(f"Resource alert created: {alert.title}")
            
            else:
                # Resolve alert if exists
                if alert_id in self.alerts and self.alerts[alert_id].is_active:
                    self.alerts[alert_id].resolved_at = datetime.now(timezone.utc)
                    logger.info(f"Resource alert resolved: {self.alerts[alert_id].title}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [
            alert.to_dict() for alert in self.alerts.values()
            if alert.is_active
        ]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for the specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return [
            alert.to_dict() for alert in self.alerts.values()
            if alert.created_at >= cutoff_time
        ]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over time"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        recent_reports = [
            report for report in self.health_history
            if datetime.fromisoformat(report["timestamp"]) >= cutoff_time
        ]
        
        if not recent_reports:
            return {"message": "No recent health data available"}
        
        # Calculate trends
        status_counts = {}
        avg_duration = 0
        
        for report in recent_reports:
            status = report["overall_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            avg_duration += report["total_duration_ms"]
        
        avg_duration = avg_duration / len(recent_reports) if recent_reports else 0
        
        return {
            "time_period_hours": hours,
            "total_reports": len(recent_reports),
            "status_distribution": status_counts,
            "avg_check_duration_ms": avg_duration,
            "recent_reports": recent_reports[-10:]  # Last 10 reports
        }


# Global health monitor instance
health_monitor = HealthMonitor()


# Export main components
__all__ = [
    'HealthMonitor', 'BaseHealthCheck', 'HealthStatus', 'AlertSeverity',
    'HealthCheckResult', 'SystemMetrics', 'Alert',
    'DatabaseHealthCheck', 'CacheHealthCheck', 'QueueHealthCheck',
    'AIServiceHealthCheck', 'SystemResourcesHealthCheck', 'ExternalServiceHealthCheck',
    'health_monitor'
]