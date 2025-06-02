import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.utils.graph_auth import auth_manager
from app.integrations.m365_client import email_client
from app.core.llm_service import llm_service
from app.services.email_processor import email_processor
from app.services.teams_manager import teams_manager
from app.services.database_service import database_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Test M365 connectivity on startup
    try:
        connection_test = await email_client.test_connectivity()
        if connection_test["status"] == "success":
            logger.info("M365 connectivity test passed")
        else:
            logger.warning(f"M365 connectivity test failed: {connection_test.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Failed to test M365 connectivity: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down EmailBot application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="M365 EmailBot for automated email processing and escalation",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic application information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Test M365 Graph API connectivity
        try:
            if await auth_manager.test_connection():
                health_status["components"]["m365_graph"] = "healthy"
            else:
                health_status["components"]["m365_graph"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["m365_graph"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Test email client connectivity
        try:
            email_test = await email_client.test_connectivity()
            if email_test["status"] == "success":
                health_status["components"]["email_client"] = "healthy"
            else:
                health_status["components"]["email_client"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["email_client"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Test LLM service (basic check)
        try:
            if llm_service.client:
                health_status["components"]["llm_service"] = "healthy"
            else:
                health_status["components"]["llm_service"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["llm_service"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Test email processor pipeline
        try:
            pipeline_status = await email_processor.validate_processing_pipeline()
            if pipeline_status["status"] == "healthy":
                health_status["components"]["email_processor"] = "healthy"
            else:
                health_status["components"]["email_processor"] = "degraded"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["email_processor"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Test Teams manager
        try:
            teams_test = await teams_manager.test_connectivity()
            if teams_test["status"] == "success":
                health_status["components"]["teams_manager"] = "healthy"
            else:
                health_status["components"]["teams_manager"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["teams_manager"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Test database service
        try:
            db_health = await database_service.health_check()
            if db_health["status"] == "healthy":
                health_status["components"]["database"] = "healthy"
                health_status["components"]["database_details"] = db_health["tables"]
            else:
                health_status["components"]["database"] = "unhealthy"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["database"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component-specific information."""
    try:
        detailed_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # M365 authentication details
        try:
            token_info = auth_manager.get_token_info()
            permissions = await auth_manager.validate_permissions()
            
            detailed_status["components"]["m365_auth"] = {
                "status": "healthy" if token_info["is_valid"] else "unhealthy",
                "token_valid": token_info["is_valid"],
                "expires_at": token_info["expires_at"],
                "permissions": permissions
            }
        except Exception as e:
            detailed_status["components"]["m365_auth"] = {
                "status": "error",
                "error": str(e)
            }
            detailed_status["status"] = "degraded"
        
        # Email client details
        try:
            email_test = await email_client.test_connectivity()
            detailed_status["components"]["email_client"] = {
                "status": "healthy" if email_test["status"] == "success" else "unhealthy",
                "mailbox": email_test.get("mailbox_email"),
                "display_name": email_test.get("mailbox_display_name"),
                "can_read_messages": email_test.get("can_read_messages"),
                "test_timestamp": email_test.get("test_timestamp")
            }
        except Exception as e:
            detailed_status["components"]["email_client"] = {
                "status": "error",
                "error": str(e)
            }
            detailed_status["status"] = "degraded"
        
        # Configuration status
        detailed_status["components"]["configuration"] = {
            "status": "healthy",
            "target_mailbox": settings.target_mailbox,
            "polling_interval": settings.polling_interval_minutes,
            "batch_size": settings.batch_size,
            "llm_model": settings.openai_model,
            "confidence_thresholds": {
                "auto": settings.confidence_threshold_auto,
                "suggest": settings.confidence_threshold_suggest,
                "review": settings.confidence_threshold_review
            }
        }
        
        return detailed_status
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.post("/process/trigger")
async def trigger_email_processing(background_tasks: BackgroundTasks):
    """Manually trigger email processing."""
    try:
        background_tasks.add_task(process_emails_background)
        
        return {
            "status": "triggered",
            "message": "Email processing started in background",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger email processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/immediate")
async def process_emails_immediate():
    """Process emails immediately and return results."""
    try:
        logger.info("Starting immediate email processing")
        result = await email_processor.process_new_emails()
        
        return {
            "status": "completed",
            "processing_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Immediate email processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/process/status")
async def get_processing_status():
    """Get current processing status and statistics."""
    try:
        # Get processing statistics from email processor
        stats = email_processor.get_processing_statistics()
        
        return {
            "status": "ready",
            "processing_statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/process/statistics")
async def get_detailed_statistics():
    """Get detailed processing and escalation statistics."""
    try:
        processing_stats = email_processor.get_processing_statistics()
        escalation_stats = teams_manager.get_escalation_statistics()
        
        return {
            "processing": processing_stats,
            "escalations": escalation_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get detailed statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/escalations/active")
async def get_active_escalations():
    """Get list of currently active escalation teams."""
    try:
        escalations = await teams_manager.list_active_escalations()
        
        return {
            "status": "success",
            "active_escalations": escalations,
            "count": len(escalations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get active escalations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/escalations/{team_id}/resolve")
async def resolve_escalation(team_id: str, resolution_notes: str):
    """Mark an escalation as resolved."""
    try:
        success = await teams_manager.resolve_escalation(team_id, resolution_notes)
        
        if success:
            return {
                "status": "resolved",
                "team_id": team_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to resolve escalation")
            
    except Exception as e:
        logger.error(f"Failed to resolve escalation {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config/validation")
async def validate_configuration():
    """Validate current configuration and integrations."""
    try:
        validation_results = {
            "status": "valid",
            "timestamp": datetime.utcnow().isoformat(),
            "validations": {}
        }
        
        # Validate M365 configuration
        try:
            token_valid = await auth_manager.test_connection()
            permissions = await auth_manager.validate_permissions()
            
            validation_results["validations"]["m365"] = {
                "status": "valid" if token_valid else "invalid",
                "token_valid": token_valid,
                "permissions": permissions
            }
        except Exception as e:
            validation_results["validations"]["m365"] = {
                "status": "error",
                "error": str(e)
            }
            validation_results["status"] = "invalid"
        
        # Validate email access
        try:
            email_test = await email_client.test_connectivity()
            validation_results["validations"]["email_access"] = {
                "status": "valid" if email_test["status"] == "success" else "invalid",
                "details": email_test
            }
        except Exception as e:
            validation_results["validations"]["email_access"] = {
                "status": "error",
                "error": str(e)
            }
            validation_results["status"] = "invalid"
        
        # Validate required environment variables
        required_vars = [
            "m365_tenant_id", "m365_client_id", "m365_client_secret",
            "target_mailbox", "openai_api_key"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(settings, var, None):
                missing_vars.append(var)
        
        validation_results["validations"]["environment"] = {
            "status": "valid" if not missing_vars else "invalid",
            "missing_variables": missing_vars
        }
        
        if missing_vars:
            validation_results["status"] = "invalid"
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/dashboard")
async def get_dashboard_analytics():
    """Get comprehensive dashboard analytics."""
    try:
        dashboard_data = await database_service.get_dashboard_data()
        
        return {
            "status": "success",
            "data": dashboard_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/analytics/processing")
async def get_processing_analytics(days: int = 7):
    """Get processing performance analytics."""
    try:
        async with database_service.get_session() as session:
            processing_stats = await database_service.processing_repo.get_processing_statistics(days)
            
        return {
            "status": "success",
            "data": processing_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing analytics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/analytics/classification")
async def get_classification_analytics():
    """Get email classification analytics."""
    try:
        async with database_service.get_session() as session:
            classification_stats = await database_service.classification_repo.get_classification_statistics()
            
        return {
            "status": "success",
            "data": classification_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get classification analytics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/analytics/patterns")
async def get_pattern_analytics(min_frequency: int = 5, min_automation_potential: float = 70.0):
    """Get email pattern analytics and automation opportunities."""
    try:
        async with database_service.get_session() as session:
            automation_candidates = await database_service.pattern_repo.get_automation_candidates(
                min_frequency, min_automation_potential
            )
            
        patterns_data = [
            {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type,
                "description": pattern.description,
                "frequency": pattern.frequency,
                "automation_potential": pattern.automation_potential,
                "first_seen": pattern.first_seen.isoformat(),
                "last_seen": pattern.last_seen.isoformat(),
                "time_savings_potential_minutes": pattern.time_savings_potential_minutes
            }
            for pattern in automation_candidates
        ]
        
        return {
            "status": "success",
            "data": {
                "automation_candidates": patterns_data,
                "total_candidates": len(patterns_data),
                "criteria": {
                    "min_frequency": min_frequency,
                    "min_automation_potential": min_automation_potential
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get pattern analytics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/emails/history")
async def get_email_history(sender: str = None, days: int = 30, limit: int = 50):
    """Get email processing history."""
    try:
        async with database_service.get_session() as session:
            if sender:
                emails = await database_service.email_repo.get_emails_by_sender(sender, limit)
            else:
                start_date = datetime.utcnow() - timedelta(days=days)
                end_date = datetime.utcnow()
                emails = await database_service.email_repo.get_emails_by_date_range(start_date, end_date)
                emails = emails[:limit]  # Limit results
        
        emails_data = [
            {
                "id": email.id,
                "sender_email": email.sender_email,
                "sender_name": email.sender_name,
                "subject": email.subject,
                "received_datetime": email.received_datetime.isoformat(),
                "processed_datetime": email.processed_datetime.isoformat() if email.processed_datetime else None,
                "processing_status": email.processing_status,
                "is_processed": email.is_processed,
                "processing_duration_seconds": email.processing_duration_seconds
            }
            for email in emails
        ]
        
        return {
            "status": "success",
            "data": {
                "emails": emails_data,
                "total_count": len(emails_data),
                "filters": {
                    "sender": sender,
                    "days": days,
                    "limit": limit
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get email history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.post("/analytics/feedback")
async def add_classification_feedback(email_id: str, feedback: str, notes: str = None):
    """Add human feedback to email classification."""
    try:
        async with database_service.get_session() as session:
            success = await database_service.classification_repo.add_human_feedback(
                email_id, feedback, notes
            )
            
        if success:
            return {
                "status": "success",
                "message": f"Feedback '{feedback}' added to email {email_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "error": f"Email {email_id} not found or feedback could not be added",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Failed to add feedback for email {email_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def process_emails_background():
    """Background task for processing emails using the complete pipeline."""
    try:
        logger.info("Starting background email processing")
        
        # Use the email processor pipeline for complete processing
        result = await email_processor.process_new_emails()
        
        logger.info(f"Background email processing completed: {result['emails_processed']} processed")
        
        if result.get('errors'):
            logger.warning(f"Processing completed with {len(result['errors'])} errors")
            for error in result['errors']:
                logger.error(f"Processing error: {error}")
        
    except Exception as e:
        logger.error(f"Background email processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    ) 