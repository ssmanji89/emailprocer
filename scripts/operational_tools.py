#!/usr/bin/env python3
"""
EmailBot Operational Tools
=========================

Operational scripts for EmailBot maintenance, troubleshooting, and system management.
Implements procedures from OPERATIONS.md.

Usage:
    python scripts/operational_tools.py [command] [options]

Commands:
    health-check       - Run comprehensive health check
    backup-database    - Create database backup
    restore-database   - Restore database from backup
    rotate-logs        - Rotate and archive log files
    clean-cache        - Clean Redis cache and temporary files
    generate-api-key   - Generate new API key for user
    system-diagnostics - Run system diagnostics
    performance-report - Generate performance report
    security-audit     - Run security audit
    maintenance-mode   - Enable/disable maintenance mode
"""

import asyncio
import argparse
import logging
import sys
import json
import subprocess
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import settings
from app.services.database_service import database_service
from app.services.monitoring_service import monitoring_service, performance_metrics
from app.core.enhanced_security import (
    api_key_manager, audit_logger, access_control, encryption_manager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OperationalTools:
    """Operational tools for EmailBot maintenance."""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.logs_dir = Path("logs")
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    async def health_check(self, detailed: bool = False) -> Dict[str, Any]:
        """Run comprehensive health check."""
        try:
            logger.info("🔍 Starting comprehensive health check...")
            
            health_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "healthy",
                "components": {},
                "issues": [],
                "recommendations": []
            }
            
            # Database health
            try:
                db_health = await database_service.health_check()
                health_result["components"]["database"] = db_health
                if db_health["status"] != "healthy":
                    health_result["overall_status"] = "degraded"
                    health_result["issues"].append("Database health check failed")
            except Exception as e:
                health_result["components"]["database"] = {"status": "error", "error": str(e)}
                health_result["overall_status"] = "unhealthy"
                health_result["issues"].append(f"Database error: {str(e)}")
            
            # System monitoring
            try:
                monitoring_result = await monitoring_service.run_monitoring_cycle()
                health_result["components"]["monitoring"] = monitoring_result
                if monitoring_result["alerts_generated"] > 0:
                    health_result["overall_status"] = "degraded"
                    health_result["issues"].append(f"{monitoring_result['alerts_generated']} active alerts")
            except Exception as e:
                health_result["components"]["monitoring"] = {"status": "error", "error": str(e)}
                health_result["issues"].append(f"Monitoring error: {str(e)}")
            
            # Performance metrics
            if detailed:
                try:
                    metrics = await performance_metrics.get_kpi_summary(24)
                    health_result["components"]["performance"] = metrics
                    
                    # Check performance thresholds
                    if metrics.get("email_processing", {}).get("success_rate", 1.0) < 0.95:
                        health_result["recommendations"].append("Email processing success rate is below 95%")
                    
                    if metrics.get("system", {}).get("cpu_usage", 0) > 80:
                        health_result["recommendations"].append("High CPU usage detected")
                        
                except Exception as e:
                    health_result["components"]["performance"] = {"status": "error", "error": str(e)}
            
            # Disk space check
            try:
                disk_usage = shutil.disk_usage("/")
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                health_result["components"]["disk_space"] = {
                    "status": "healthy" if disk_percent < 90 else "warning",
                    "usage_percent": disk_percent,
                    "free_gb": disk_usage.free / (1024**3)
                }
                
                if disk_percent > 90:
                    health_result["overall_status"] = "degraded"
                    health_result["issues"].append(f"High disk usage: {disk_percent:.1f}%")
                    
            except Exception as e:
                health_result["components"]["disk_space"] = {"status": "error", "error": str(e)}
            
            logger.info(f"✅ Health check completed - Status: {health_result['overall_status']}")
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    async def backup_database(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create database backup."""
        try:
            if not backup_name:
                backup_name = f"emailbot_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"📦 Creating database backup: {backup_name}")
            
            backup_file = self.backup_dir / f"{backup_name}.sql"
            
            # PostgreSQL backup using pg_dump
            cmd = [
                "pg_dump",
                "-h", settings.database_host,
                "-p", str(settings.database_port),
                "-U", settings.database_user,
                "-d", settings.database_name,
                "-f", str(backup_file),
                "--no-password",
                "--verbose"
            ]
            
            # Set PGPASSWORD environment variable
            env = {"PGPASSWORD": settings.database_password}
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Compress backup
                compressed_file = f"{backup_file}.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                backup_file.unlink()
                
                backup_info = {
                    "status": "success",
                    "backup_file": compressed_file,
                    "size_mb": Path(compressed_file).stat().st_size / (1024 * 1024),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"✅ Database backup created: {compressed_file}")
                return backup_info
            else:
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def restore_database(self, backup_file: str) -> Dict[str, Any]:
        """Restore database from backup."""
        try:
            logger.info(f"🔄 Restoring database from: {backup_file}")
            
            backup_path = Path(backup_file)
            if not backup_path.exists():
                backup_path = self.backup_dir / backup_file
            
            if not backup_path.exists():
                raise Exception(f"Backup file not found: {backup_file}")
            
            # Extract if compressed
            if backup_path.suffix == '.gz':
                extracted_file = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(extracted_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sql_file = extracted_file
            else:
                sql_file = backup_path
            
            # PostgreSQL restore using psql
            cmd = [
                "psql",
                "-h", settings.database_host,
                "-p", str(settings.database_port),
                "-U", settings.database_user,
                "-d", settings.database_name,
                "-f", str(sql_file),
                "--no-password"
            ]
            
            env = {"PGPASSWORD": settings.database_password}
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            # Clean up extracted file if it was compressed
            if backup_path.suffix == '.gz' and extracted_file.exists():
                extracted_file.unlink()
            
            if result.returncode == 0:
                logger.info("✅ Database restore completed successfully")
                return {
                    "status": "success",
                    "restored_from": str(backup_path),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise Exception(f"Database restore failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def rotate_logs(self, max_age_days: int = 30, max_size_mb: int = 100) -> Dict[str, Any]:
        """Rotate and archive log files."""
        try:
            logger.info("📄 Starting log rotation...")
            
            rotated_files = []
            total_size_saved = 0
            
            for log_file in self.logs_dir.glob("*.log"):
                try:
                    # Check file age and size
                    file_stat = log_file.stat()
                    file_age = (datetime.now().timestamp() - file_stat.st_mtime) / 86400  # days
                    file_size = file_stat.st_size / (1024 * 1024)  # MB
                    
                    if file_age > max_age_days or file_size > max_size_mb:
                        # Archive the file
                        archive_name = f"{log_file.stem}_{datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y%m%d')}.log.gz"
                        archive_path = self.logs_dir / "archive" / archive_name
                        archive_path.parent.mkdir(exist_ok=True)
                        
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(archive_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        total_size_saved += file_size
                        rotated_files.append({
                            "original": str(log_file),
                            "archived": str(archive_path),
                            "size_mb": file_size
                        })
                        
                        # Remove original file
                        log_file.unlink()
                        
                except Exception as e:
                    logger.warning(f"Failed to rotate {log_file}: {str(e)}")
            
            logger.info(f"✅ Log rotation completed - {len(rotated_files)} files rotated")
            return {
                "status": "success",
                "files_rotated": len(rotated_files),
                "total_size_saved_mb": total_size_saved,
                "rotated_files": rotated_files,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Log rotation failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def clean_cache(self) -> Dict[str, Any]:
        """Clean Redis cache and temporary files."""
        try:
            logger.info("🧹 Starting cache cleanup...")
            
            cleanup_result = {
                "status": "success",
                "redis_keys_cleared": 0,
                "temp_files_removed": 0,
                "space_freed_mb": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Clean Redis cache
            try:
                import redis
                redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password,
                    decode_responses=True
                )
                
                # Get all EmailBot keys
                emailbot_keys = redis_client.keys("emailbot:*")
                if emailbot_keys:
                    redis_client.delete(*emailbot_keys)
                    cleanup_result["redis_keys_cleared"] = len(emailbot_keys)
                    
            except Exception as e:
                logger.warning(f"Redis cleanup failed: {str(e)}")
            
            # Clean temporary files
            temp_dirs = ["/tmp", "/var/tmp", "temp"]
            for temp_dir in temp_dirs:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    for temp_file in temp_path.glob("emailbot_*"):
                        try:
                            if temp_file.is_file():
                                size_mb = temp_file.stat().st_size / (1024 * 1024)
                                temp_file.unlink()
                                cleanup_result["temp_files_removed"] += 1
                                cleanup_result["space_freed_mb"] += size_mb
                        except Exception as e:
                            logger.warning(f"Failed to remove {temp_file}: {str(e)}")
            
            logger.info(f"✅ Cache cleanup completed - {cleanup_result['redis_keys_cleared']} Redis keys, {cleanup_result['temp_files_removed']} temp files")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def generate_api_key(
        self, 
        user_id: str, 
        role: str = "viewer",
        expires_days: int = 90
    ) -> Dict[str, Any]:
        """Generate new API key for user."""
        try:
            logger.info(f"🔑 Generating API key for user: {user_id}")
            
            # Get permissions for role
            permissions = access_control.get_role_permissions(role)
            if not permissions:
                raise Exception(f"Invalid role: {role}")
            
            # Generate API key
            api_key_data = api_key_manager.generate_api_key(user_id, permissions, expires_days)
            
            # Log API key creation
            await audit_logger.log_security_event(
                event_type="API_KEY_GENERATED",
                user_id="system",
                details={
                    "target_user": user_id,
                    "role": role,
                    "permissions": permissions,
                    "key_id": api_key_data["key_id"]
                },
                severity="INFO"
            )
            
            logger.info(f"✅ API key generated for {user_id}: {api_key_data['key_id']}")
            return {
                "status": "success",
                "user_id": user_id,
                "role": role,
                "api_key": api_key_data["api_key"],
                "key_id": api_key_data["key_id"],
                "expires_at": api_key_data["expires_at"],
                "permissions": permissions
            }
            
        except Exception as e:
            logger.error(f"API key generation failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def system_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        try:
            logger.info("🔧 Running system diagnostics...")
            
            diagnostics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system_info": {},
                "dependencies": {},
                "configuration": {},
                "recommendations": []
            }
            
            # System information
            try:
                import psutil
                import platform
                
                diagnostics["system_info"] = {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_gb": psutil.virtual_memory().total / (1024**3),
                    "disk_space_gb": psutil.disk_usage('/').total / (1024**3),
                    "uptime_hours": (datetime.now().timestamp() - psutil.boot_time()) / 3600
                }
            except ImportError:
                diagnostics["system_info"]["error"] = "psutil not available"
            
            # Check dependencies
            dependencies = [
                "fastapi", "httpx", "psycopg2-binary", "redis", 
                "openai", "cryptography", "msal", "jwt"
            ]
            
            for dep in dependencies:
                try:
                    __import__(dep.replace("-", "_"))
                    diagnostics["dependencies"][dep] = "installed"
                except ImportError:
                    diagnostics["dependencies"][dep] = "missing"
                    diagnostics["recommendations"].append(f"Install missing dependency: {dep}")
            
            # Configuration validation
            config_checks = {
                "database_url": bool(settings.database_url),
                "redis_host": bool(settings.redis_host),
                "openai_api_key": bool(settings.openai_api_key),
                "m365_tenant_id": bool(settings.m365_tenant_id),
                "master_encryption_key": bool(getattr(settings, 'master_encryption_key', None))
            }
            
            diagnostics["configuration"] = config_checks
            
            for config, status in config_checks.items():
                if not status:
                    diagnostics["recommendations"].append(f"Configure missing setting: {config}")
            
            logger.info("✅ System diagnostics completed")
            return diagnostics
            
        except Exception as e:
            logger.error(f"System diagnostics failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        try:
            logger.info(f"📊 Generating performance report for last {hours} hours...")
            
            # Get KPI summary
            kpi_data = await performance_metrics.get_kpi_summary(hours)
            
            # Get processing statistics
            processing_stats = await database_service.get_processing_statistics(hours)
            
            # Get classification metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            classification_metrics = await database_service.get_classification_metrics(start_time, end_time)
            
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "time_range": {
                    "hours": hours,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "kpi_summary": kpi_data,
                "processing_statistics": processing_stats,
                "classification_metrics": classification_metrics,
                "recommendations": []
            }
            
            # Generate recommendations
            if processing_stats.get("success_rate", 1.0) < 0.95:
                report["recommendations"].append("Email processing success rate is below target (95%)")
            
            if processing_stats.get("average_processing_time", 0) > 30:
                report["recommendations"].append("Average processing time is above target (30s)")
            
            if classification_metrics.get("accuracy", 1.0) < 0.90:
                report["recommendations"].append("Classification accuracy is below target (90%)")
            
            logger.info("✅ Performance report generated")
            return report
            
        except Exception as e:
            logger.error(f"Performance report generation failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit."""
        try:
            logger.info("🔒 Running security audit...")
            
            audit_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "security_checks": {},
                "vulnerabilities": [],
                "recommendations": [],
                "compliance_status": "compliant"
            }
            
            # Check encryption status
            try:
                test_data = "test_encryption_data"
                encrypted = encryption_manager.encrypt_sensitive_data(test_data)
                decrypted = encryption_manager.decrypt_sensitive_data(encrypted)
                audit_result["security_checks"]["encryption"] = "working" if decrypted == test_data else "failed"
            except Exception as e:
                audit_result["security_checks"]["encryption"] = "failed"
                audit_result["vulnerabilities"].append("Data encryption is not working properly")
            
            # Check API key security
            try:
                # Generate test API key
                test_key = api_key_manager.generate_api_key("test_user", ["read:emails"], 1)
                # Validate it
                validation = await api_key_manager.validate_api_key(test_key["api_key"])
                audit_result["security_checks"]["api_key_validation"] = "working" if validation["valid"] else "failed"
                # Revoke test key
                await api_key_manager.revoke_api_key(test_key["key_id"], "Security audit test")
            except Exception as e:
                audit_result["security_checks"]["api_key_validation"] = "failed"
                audit_result["vulnerabilities"].append("API key validation is not working properly")
            
            # Check audit logging
            try:
                await audit_logger.log_security_event(
                    "SECURITY_AUDIT_TEST",
                    "system",
                    {"test": True},
                    "INFO"
                )
                audit_result["security_checks"]["audit_logging"] = "working"
            except Exception as e:
                audit_result["security_checks"]["audit_logging"] = "failed"
                audit_result["vulnerabilities"].append("Audit logging is not working properly")
            
            # Check for security recommendations
            if len(audit_result["vulnerabilities"]) == 0:
                audit_result["recommendations"].append("All security checks passed")
            else:
                audit_result["compliance_status"] = "non_compliant"
                audit_result["recommendations"].append("Address identified vulnerabilities immediately")
            
            logger.info(f"✅ Security audit completed - Status: {audit_result['compliance_status']}")
            return audit_result
            
        except Exception as e:
            logger.error(f"Security audit failed: {str(e)}")
            return {"status": "error", "error": str(e)}


async def main():
    """Main CLI interface for operational tools."""
    parser = argparse.ArgumentParser(description="EmailBot Operational Tools")
    parser.add_argument("command", choices=[
        "health-check", "backup-database", "restore-database", "rotate-logs",
        "clean-cache", "generate-api-key", "system-diagnostics", 
        "performance-report", "security-audit"
    ])
    
    # Command-specific arguments
    parser.add_argument("--detailed", action="store_true", help="Detailed health check")
    parser.add_argument("--backup-name", help="Custom backup name")
    parser.add_argument("--backup-file", help="Backup file to restore")
    parser.add_argument("--user-id", help="User ID for API key generation")
    parser.add_argument("--role", default="viewer", help="Role for API key (admin, operator, viewer, api_user)")
    parser.add_argument("--expires-days", type=int, default=90, help="API key expiration in days")
    parser.add_argument("--hours", type=int, default=24, help="Time range in hours for reports")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    tools = OperationalTools()
    result = None
    
    try:
        if args.command == "health-check":
            result = await tools.health_check(args.detailed)
        elif args.command == "backup-database":
            result = await tools.backup_database(args.backup_name)
        elif args.command == "restore-database":
            if not args.backup_file:
                print("Error: --backup-file is required for restore-database")
                sys.exit(1)
            result = await tools.restore_database(args.backup_file)
        elif args.command == "rotate-logs":
            result = tools.rotate_logs()
        elif args.command == "clean-cache":
            result = await tools.clean_cache()
        elif args.command == "generate-api-key":
            if not args.user_id:
                print("Error: --user-id is required for generate-api-key")
                sys.exit(1)
            result = await tools.generate_api_key(args.user_id, args.role, args.expires_days)
        elif args.command == "system-diagnostics":
            result = await tools.system_diagnostics()
        elif args.command == "performance-report":
            result = await tools.performance_report(args.hours)
        elif args.command == "security-audit":
            result = await tools.security_audit()
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 