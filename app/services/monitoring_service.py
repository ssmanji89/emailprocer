import asyncio
import logging
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.config.settings import settings
from app.services.database_service import database_service
from app.utils.retry import AsyncRetry

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    """Alert data structure."""
    severity: AlertSeverity
    component: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime


class SystemMonitor:
    """Automated system monitoring with alerting."""
    
    def __init__(self, alert_webhook: Optional[str] = None):
        self.alert_webhook = alert_webhook or settings.alert_webhook_url
        self.thresholds = {
            "max_queue_size": 100,
            "min_success_rate": 0.95,
            "max_processing_time": 30.0,  # seconds
            "max_response_time": 5.0,     # seconds
            "min_availability": 0.99,
            "max_cpu_usage": 80.0,        # percent
            "max_memory_usage": 85.0,     # percent
            "max_disk_usage": 90.0        # percent
        }
        self.last_alerts = {}
        self.alert_cooldown = 300  # 5 minutes
        
    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run complete monitoring cycle."""
        alerts = []
        
        try:
            # Check API health
            api_health = await self._check_api_health()
            if not api_health["healthy"]:
                alerts.append(Alert(
                    severity=AlertSeverity.CRITICAL,
                    component="API",
                    message="API health check failed",
                    details=api_health,
                    timestamp=datetime.utcnow()
                ))
            
            # Check processing metrics
            processing_metrics = await self._check_processing_metrics()
            alerts.extend(processing_metrics["alerts"])
            
            # Check external dependencies
            dependency_health = await self._check_dependencies()
            alerts.extend(dependency_health["alerts"])
            
            # Check resource usage
            resource_alerts = await self._check_resource_usage()
            alerts.extend(resource_alerts)
            
            # Check database performance
            db_alerts = await self._check_database_performance()
            alerts.extend(db_alerts)
            
            # Send alerts
            for alert in alerts:
                await self._send_alert(alert)
            
            return {
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "alerts_generated": len(alerts),
                "alerts": [self._serialize_alert(alert) for alert in alerts]
            }
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_api_health(self) -> Dict[str, Any]:
        """Check API health and response times."""
        try:
            start_time = datetime.utcnow()
            
            # Test health endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://localhost:{settings.port}/health",
                    timeout=10.0
                )
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "healthy": response.status_code == 200,
                "response_time": response_time,
                "status_code": response.status_code,
                "details": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "response_time": None
            }
    
    async def _check_processing_metrics(self) -> Dict[str, Any]:
        """Check email processing performance metrics."""
        try:
            # Get processing statistics from database
            stats = await database_service.get_processing_statistics(hours=1)
            
            alerts = []
            
            # Check queue size
            queue_size = stats.get("current_queue_size", 0)
            if queue_size > self.thresholds["max_queue_size"]:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    component="Processing Queue",
                    message=f"Queue size is high: {queue_size}",
                    details={"queue_size": queue_size, "threshold": self.thresholds["max_queue_size"]},
                    timestamp=datetime.utcnow()
                ))
            
            # Check success rate
            success_rate = stats.get("success_rate", 1.0)
            if success_rate < self.thresholds["min_success_rate"]:
                alerts.append(Alert(
                    severity=AlertSeverity.CRITICAL,
                    component="Processing",
                    message=f"Low success rate: {success_rate:.2%}",
                    details={"success_rate": success_rate, "threshold": self.thresholds["min_success_rate"]},
                    timestamp=datetime.utcnow()
                ))
            
            # Check average processing time
            avg_time = stats.get("average_processing_time", 0)
            if avg_time > self.thresholds["max_processing_time"]:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    component="Performance",
                    message=f"Slow processing: {avg_time:.2f}s",
                    details={"avg_processing_time": avg_time, "threshold": self.thresholds["max_processing_time"]},
                    timestamp=datetime.utcnow()
                ))
            
            return {"healthy": len(alerts) == 0, "alerts": alerts}
            
        except Exception as e:
            return {
                "healthy": False,
                "alerts": [Alert(
                    severity=AlertSeverity.CRITICAL,
                    component="Monitoring",
                    message=f"Failed to check processing metrics: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.utcnow()
                )]
            }
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check external dependency health."""
        alerts = []
        
        try:
            # Check M365 Graph API
            from app.utils.graph_auth import auth_manager
            m365_health = await auth_manager.test_connection()
            if not m365_health:
                alerts.append(Alert(
                    severity=AlertSeverity.CRITICAL,
                    component="M365 Graph API",
                    message="M365 Graph API connectivity failed",
                    details={"service": "Microsoft Graph"},
                    timestamp=datetime.utcnow()
                ))
            
            # Check OpenAI API
            from app.core.llm_service import llm_service
            try:
                # Simple test to check API availability
                if not llm_service.client:
                    alerts.append(Alert(
                        severity=AlertSeverity.CRITICAL,
                        component="OpenAI API",
                        message="OpenAI client not initialized",
                        details={"service": "OpenAI"},
                        timestamp=datetime.utcnow()
                    ))
            except Exception as e:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    component="OpenAI API",
                    message=f"OpenAI API check failed: {str(e)}",
                    details={"service": "OpenAI", "error": str(e)},
                    timestamp=datetime.utcnow()
                ))
            
            # Check database connectivity
            try:
                db_health = await database_service.health_check()
                if db_health["status"] != "healthy":
                    alerts.append(Alert(
                        severity=AlertSeverity.CRITICAL,
                        component="Database",
                        message="Database health check failed",
                        details=db_health,
                        timestamp=datetime.utcnow()
                    ))
            except Exception as e:
                alerts.append(Alert(
                    severity=AlertSeverity.CRITICAL,
                    component="Database",
                    message=f"Database connectivity failed: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.utcnow()
                ))
            
            return {"healthy": len(alerts) == 0, "alerts": alerts}
            
        except Exception as e:
            return {
                "healthy": False,
                "alerts": [Alert(
                    severity=AlertSeverity.CRITICAL,
                    component="Dependency Check",
                    message=f"Dependency check failed: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.utcnow()
                )]
            }
    
    async def _check_resource_usage(self) -> List[Alert]:
        """Check system resource usage."""
        alerts = []
        
        try:
            import psutil
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.thresholds["max_cpu_usage"]:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    component="System Resources",
                    message=f"High CPU usage: {cpu_percent:.1f}%",
                    details={"cpu_usage": cpu_percent, "threshold": self.thresholds["max_cpu_usage"]},
                    timestamp=datetime.utcnow()
                ))
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.thresholds["max_memory_usage"]:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    component="System Resources",
                    message=f"High memory usage: {memory.percent:.1f}%",
                    details={"memory_usage": memory.percent, "threshold": self.thresholds["max_memory_usage"]},
                    timestamp=datetime.utcnow()
                ))
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self.thresholds["max_disk_usage"]:
                alerts.append(Alert(
                    severity=AlertSeverity.CRITICAL,
                    component="System Resources",
                    message=f"High disk usage: {disk_percent:.1f}%",
                    details={"disk_usage": disk_percent, "threshold": self.thresholds["max_disk_usage"]},
                    timestamp=datetime.utcnow()
                ))
            
        except ImportError:
            logger.warning("psutil not available for resource monitoring")
        except Exception as e:
            alerts.append(Alert(
                severity=AlertSeverity.WARNING,
                component="Resource Monitor",
                message=f"Resource monitoring failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            ))
        
        return alerts
    
    async def _check_database_performance(self) -> List[Alert]:
        """Check database performance metrics."""
        alerts = []
        
        try:
            # Check connection pool status
            pool_info = await database_service.get_connection_pool_info()
            
            if pool_info["active_connections"] >= pool_info["pool_size"] * 0.9:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    component="Database Pool",
                    message=f"High connection pool usage: {pool_info['active_connections']}/{pool_info['pool_size']}",
                    details=pool_info,
                    timestamp=datetime.utcnow()
                ))
            
            # Check slow queries
            slow_queries = await database_service.get_slow_queries()
            if slow_queries:
                alerts.append(Alert(
                    severity=AlertSeverity.WARNING,
                    component="Database Performance",
                    message=f"Detected {len(slow_queries)} slow queries",
                    details={"slow_queries": slow_queries},
                    timestamp=datetime.utcnow()
                ))
            
        except Exception as e:
            alerts.append(Alert(
                severity=AlertSeverity.WARNING,
                component="Database Monitor",
                message=f"Database performance check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            ))
        
        return alerts
    
    async def _send_alert(self, alert: Alert):
        """Send alert to configured endpoints."""
        try:
            # Check if alert should be sent (cooldown)
            alert_key = f"{alert.component}:{alert.message}"
            now = datetime.utcnow()
            
            if alert_key in self.last_alerts:
                time_since_last = (now - self.last_alerts[alert_key]).total_seconds()
                if time_since_last < self.alert_cooldown:
                    return  # Skip due to cooldown
            
            self.last_alerts[alert_key] = now
            
            # Send to webhook if configured
            if self.alert_webhook:
                await self._send_webhook_alert(alert)
            
            # Log alert
            log_level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.INFO)
            
            logger.log(log_level, f"ALERT [{alert.severity.value}] {alert.component}: {alert.message}")
            
            # Store alert in database
            await self._store_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    @AsyncRetry(max_attempts=3, backoff_factor=2.0)
    async def _send_webhook_alert(self, alert: Alert):
        """Send alert to webhook endpoint."""
        try:
            payload = {
                "severity": alert.severity.value,
                "component": alert.component,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat(),
                "service": "EmailBot"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.alert_webhook,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {str(e)}")
            raise
    
    async def _store_alert(self, alert: Alert):
        """Store alert in database for historical tracking."""
        try:
            await database_service.store_alert({
                "severity": alert.severity.value,
                "component": alert.component,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp
            })
        except Exception as e:
            logger.error(f"Failed to store alert in database: {str(e)}")
    
    def _serialize_alert(self, alert: Alert) -> Dict[str, Any]:
        """Serialize alert for JSON response."""
        return {
            "severity": alert.severity.value,
            "component": alert.component,
            "message": alert.message,
            "details": alert.details,
            "timestamp": alert.timestamp.isoformat()
        }


class PerformanceMetrics:
    """Performance metrics collection and analysis."""
    
    async def get_kpi_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get key performance indicators for the last N hours."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = {
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            }
        }
        
        try:
            # Email processing metrics
            processing_data = await database_service.get_processing_metrics(start_time, end_time)
            metrics["email_processing"] = {
                "total_processed": processing_data["count"],
                "success_rate": processing_data["success_rate"],
                "avg_processing_time": processing_data["avg_time"],
                "automation_rate": processing_data["automation_rate"]
            }
            
            # Classification accuracy
            classification_data = await database_service.get_classification_metrics(start_time, end_time)
            metrics["classification"] = {
                "accuracy": classification_data["accuracy"],
                "confidence_distribution": classification_data["confidence_dist"],
                "category_distribution": classification_data["category_dist"]
            }
            
            # System performance
            system_data = await self._get_system_metrics()
            metrics["system"] = {
                "cpu_usage": system_data["cpu_percent"],
                "memory_usage": system_data["memory_percent"],
                "disk_usage": system_data["disk_percent"],
                "uptime": system_data["uptime_hours"]
            }
            
            # Service availability
            availability_data = await database_service.get_availability_metrics(start_time, end_time)
            metrics["availability"] = {
                "uptime_percentage": availability_data["uptime"],
                "downtime_incidents": availability_data["incidents"],
                "mttr": availability_data["mttr"]  # Mean Time To Recovery
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get KPI summary: {str(e)}")
            return {
                "error": str(e),
                "time_range": metrics["time_range"]
            }
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            import psutil
            import time
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                "uptime_hours": (time.time() - psutil.boot_time()) / 3600
            }
        except ImportError:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "uptime_hours": 0
            }


# Global monitoring service instance
monitoring_service = SystemMonitor()
performance_metrics = PerformanceMetrics() 