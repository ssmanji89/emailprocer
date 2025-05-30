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


@app.get("/process/status")
async def get_processing_status():
    """Get current processing status and statistics."""
    try:
        # This would typically fetch from database/cache
        # For now, return basic status
        return {
            "status": "ready",
            "last_processing": None,
            "emails_processed_today": 0,
            "current_queue_size": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {str(e)}")
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


async def process_emails_background():
    """Background task for processing emails."""
    try:
        logger.info("Starting background email processing")
        
        # Fetch new emails
        emails = await email_client.fetch_new_emails()
        
        if not emails:
            logger.info("No new emails to process")
            return
        
        logger.info(f"Processing {len(emails)} new emails")
        
        for email in emails:
            try:
                # Classify email using LLM
                classification = await llm_service.classify_email(email)
                
                logger.info(f"Email {email.id} classified as {classification.category} "
                           f"with {classification.confidence}% confidence")
                
                # TODO: Implement routing logic based on confidence
                # TODO: Implement escalation for low confidence emails
                # TODO: Implement automated responses for high confidence emails
                # TODO: Update database with processing results
                
                # Mark email as read for now
                await email_client.mark_as_read(email.id)
                
            except Exception as e:
                logger.error(f"Error processing email {email.id}: {str(e)}")
                continue
        
        logger.info("Background email processing completed")
        
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