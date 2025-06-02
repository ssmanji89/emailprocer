import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import signal

from app.services.email_processor import email_processor
from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmailProcessingScheduler:
    """Background scheduler for automated email processing."""
    
    def __init__(self):
        self.interval_minutes = settings.polling_interval_minutes
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        
        # Statistics
        self.stats = {
            "started_at": None,
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run_timestamp": None,
            "last_error_timestamp": None,
            "uptime_seconds": 0
        }
    
    async def start(self) -> None:
        """Start the email processing scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        self.stats["started_at"] = datetime.utcnow()
        self.task = asyncio.create_task(self._scheduler_loop())
        
        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        logger.info(f"Email processing scheduler started with {self.interval_minutes} minute interval")
    
    async def stop(self) -> None:
        """Stop the email processing scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Email processing scheduler stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # Signals can only be registered in main thread
            logger.debug("Signal handlers not registered (not in main thread)")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.stop())
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        try:
            while self.is_running:
                try:
                    await self._run_email_processing()
                    self.stats["successful_runs"] += 1
                    
                except Exception as e:
                    self.error_count += 1
                    self.stats["failed_runs"] += 1
                    self.stats["last_error_timestamp"] = datetime.utcnow().isoformat()
                    logger.error(f"Scheduled email processing failed: {str(e)}")
                
                # Update statistics
                self.stats["total_runs"] += 1
                self.stats["last_run_timestamp"] = datetime.utcnow().isoformat()
                
                # Calculate next run time
                self.next_run = datetime.utcnow() + timedelta(minutes=self.interval_minutes)
                
                # Wait for next interval
                await asyncio.sleep(self.interval_minutes * 60)
                
        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Scheduler loop error: {str(e)}")
            raise
    
    async def _run_email_processing(self) -> None:
        """Run a single email processing cycle."""
        try:
            self.last_run = datetime.utcnow()
            self.run_count += 1
            
            logger.info(f"Starting scheduled email processing (run #{self.run_count})")
            
            # Process new emails
            result = await email_processor.process_new_emails()
            
            # Log results
            if result["status"] == "success":
                logger.info(f"Scheduled processing completed: {result['emails_processed']} emails processed")
                
                if result.get("errors"):
                    logger.warning(f"Processing completed with {len(result['errors'])} errors")
                    
            else:
                logger.error(f"Scheduled processing failed: {result.get('error', 'Unknown error')}")
                raise Exception(result.get('error', 'Processing failed'))
            
        except Exception as e:
            logger.error(f"Error in scheduled email processing: {str(e)}")
            raise
    
    async def trigger_immediate_run(self) -> Dict[str, Any]:
        """Trigger an immediate email processing run outside the schedule."""
        try:
            logger.info("Triggering immediate email processing run")
            
            start_time = datetime.utcnow()
            result = await email_processor.process_new_emails()
            end_time = datetime.utcnow()
            
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "completed",
                "trigger_type": "immediate",
                "processing_time_seconds": processing_time,
                "result": result,
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Immediate processing trigger failed: {str(e)}")
            return {
                "status": "failed",
                "trigger_type": "immediate",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        current_time = datetime.utcnow()
        
        status = {
            "is_running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "current_time": current_time.isoformat()
        }
        
        # Calculate uptime
        if self.stats["started_at"]:
            started_at = datetime.fromisoformat(self.stats["started_at"]) if isinstance(self.stats["started_at"], str) else self.stats["started_at"]
            uptime = (current_time - started_at).total_seconds()
            self.stats["uptime_seconds"] = int(uptime)
        
        status.update(self.stats)
        
        return status
    
    async def update_interval(self, new_interval_minutes: int) -> bool:
        """Update the polling interval."""
        try:
            if new_interval_minutes < 1:
                raise ValueError("Interval must be at least 1 minute")
            
            old_interval = self.interval_minutes
            self.interval_minutes = new_interval_minutes
            
            logger.info(f"Scheduler interval updated from {old_interval} to {new_interval_minutes} minutes")
            
            # Update next run time if scheduler is running
            if self.is_running and self.last_run:
                self.next_run = self.last_run + timedelta(minutes=new_interval_minutes)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update scheduler interval: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the scheduler."""
        current_time = datetime.utcnow()
        
        health_status = {
            "status": "healthy",
            "checks": {},
            "timestamp": current_time.isoformat()
        }
        
        # Check if scheduler is running
        health_status["checks"]["scheduler_running"] = {
            "status": "healthy" if self.is_running else "unhealthy",
            "details": f"Scheduler {'is' if self.is_running else 'is not'} running"
        }
        
        # Check last run time
        if self.last_run:
            time_since_last_run = (current_time - self.last_run).total_seconds() / 60
            expected_max_interval = self.interval_minutes * 2  # Allow 2x interval before considering unhealthy
            
            if time_since_last_run > expected_max_interval:
                health_status["checks"]["last_run"] = {
                    "status": "unhealthy",
                    "details": f"Last run was {time_since_last_run:.1f} minutes ago"
                }
                health_status["status"] = "unhealthy"
            else:
                health_status["checks"]["last_run"] = {
                    "status": "healthy",
                    "details": f"Last run was {time_since_last_run:.1f} minutes ago"
                }
        else:
            health_status["checks"]["last_run"] = {
                "status": "warning",
                "details": "No runs completed yet"
            }
        
        # Check error rate
        if self.run_count > 0:
            error_rate = (self.error_count / self.run_count) * 100
            
            if error_rate > 50:
                health_status["checks"]["error_rate"] = {
                    "status": "unhealthy",
                    "details": f"High error rate: {error_rate:.1f}%"
                }
                health_status["status"] = "unhealthy"
            elif error_rate > 20:
                health_status["checks"]["error_rate"] = {
                    "status": "warning",
                    "details": f"Elevated error rate: {error_rate:.1f}%"
                }
                if health_status["status"] == "healthy":
                    health_status["status"] = "warning"
            else:
                health_status["checks"]["error_rate"] = {
                    "status": "healthy",
                    "details": f"Error rate: {error_rate:.1f}%"
                }
        
        return health_status


# Global scheduler instance
email_scheduler = EmailProcessingScheduler() 