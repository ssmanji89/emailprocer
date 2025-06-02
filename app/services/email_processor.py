import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.models.email_models import (
    EmailMessage, ClassificationResult, ProcessingResult, 
    ProcessingStatus, EmailCategory, UrgencyLevel
)
from app.integrations.m365_client import M365EmailClient
from app.services.teams_manager import TeamsEscalationManager
from app.core.llm_service import LLMService
from app.core.security import SecurityService
from app.utils.rate_limiter import RateLimiter
from app.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceThresholds:
    """Configuration for confidence-based routing."""
    auto_handle: float = 85.0      # Auto-process with high confidence
    suggest_response: float = 60.0  # Generate suggested response for review
    escalate_review: float = 40.0   # Flag for manual review
    immediate_escalation: float = 0.0  # Immediate escalation required


class EmailProcessingPipeline:
    """Main email processing pipeline with confidence-based routing."""
    
    def __init__(self):
        self.m365_client = M365EmailClient()
        self.llm_service = LLMService()
        self.teams_manager = TeamsEscalationManager()
        self.security_service = SecurityService()
        self.rate_limiter = RateLimiter(
            max_requests=settings.rate_limit_requests,
            time_window=settings.rate_limit_window
        )
        
        # Confidence thresholds for routing decisions
        self.thresholds = ConfidenceThresholds(
            auto_handle=settings.confidence_threshold_auto,
            suggest_response=settings.confidence_threshold_suggest,
            escalate_review=settings.confidence_threshold_review
        )
        
        # Processing metrics
        self.processing_stats = {
            "total_processed": 0,
            "auto_handled": 0,
            "suggested_responses": 0,
            "escalated": 0,
            "failed": 0,
            "last_processing_time": None
        }
    
    async def process_new_emails(self, since_datetime: Optional[datetime] = None) -> Dict[str, Any]:
        """Main entry point for processing new emails."""
        start_time = datetime.utcnow()
        processing_summary = {
            "status": "success",
            "emails_processed": 0,
            "results": [],
            "errors": [],
            "processing_time_ms": 0,
            "timestamp": start_time.isoformat()
        }
        
        try:
            logger.info("Starting email processing pipeline")
            
            # Rate limiting check
            if not await self.rate_limiter.allow_request("email_processing"):
                raise Exception("Rate limit exceeded for email processing")
            
            # Fetch new emails from M365
            emails = await self.m365_client.fetch_new_emails(since_datetime)
            logger.info(f"Retrieved {len(emails)} new emails for processing")
            
            if not emails:
                processing_summary["message"] = "No new emails to process"
                return processing_summary
            
            # Process each email through the pipeline
            for email in emails:
                try:
                    result = await self._process_single_email(email)
                    processing_summary["results"].append(result.dict())
                    processing_summary["emails_processed"] += 1
                    
                    # Update processing statistics
                    self._update_processing_stats(result)
                    
                except Exception as e:
                    error_msg = f"Failed to process email {email.id}: {str(e)}"
                    logger.error(error_msg)
                    processing_summary["errors"].append(error_msg)
                    self.processing_stats["failed"] += 1
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            processing_summary["processing_time_ms"] = int(processing_time)
            
            # Update last processing time
            self.processing_stats["last_processing_time"] = end_time.isoformat()
            
            logger.info(f"Email processing completed: {processing_summary['emails_processed']} processed, "
                       f"{len(processing_summary['errors'])} errors")
            
            return processing_summary
            
        except Exception as e:
            logger.error(f"Email processing pipeline failed: {str(e)}")
            processing_summary["status"] = "error"
            processing_summary["error"] = str(e)
            return processing_summary
    
    async def _process_single_email(self, email: EmailMessage) -> ProcessingResult:
        """Process a single email through the complete pipeline."""
        result = ProcessingResult(
            email_id=email.id,
            status=ProcessingStatus.RECEIVED,
            created_at=datetime.utcnow()
        )
        
        processing_start = datetime.utcnow()
        
        try:
            # Step 1: Security screening
            result.status = ProcessingStatus.ANALYZING
            await self._perform_security_screening(email)
            
            # Step 2: LLM classification
            result.status = ProcessingStatus.CLASSIFYING
            classification = await self.llm_service.classify_email(email)
            result.classification = classification
            
            logger.info(f"Email {email.id} classified as {classification.category} "
                       f"with {classification.confidence}% confidence")
            
            # Step 3: Confidence-based routing
            result.status = ProcessingStatus.ROUTING
            routing_decision = self._make_routing_decision(classification)
            
            # Step 4: Execute action based on routing decision
            if routing_decision["action"] == "auto_handle":
                await self._handle_auto_processing(email, classification, result)
            elif routing_decision["action"] == "suggest_response":
                await self._handle_suggested_response(email, classification, result)
            elif routing_decision["action"] == "escalate":
                await self._handle_escalation(email, classification, result)
            else:
                await self._handle_manual_review(email, classification, result)
            
            # Step 5: Mark email as processed
            await self.m365_client.mark_as_read(email.id)
            
            result.status = ProcessingStatus.COMPLETED
            
        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            logger.error(f"Failed to process email {email.id}: {str(e)}")
        
        finally:
            # Calculate processing time
            processing_end = datetime.utcnow()
            processing_time = (processing_end - processing_start).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)
            result.updated_at = processing_end
        
        return result
    
    async def _perform_security_screening(self, email: EmailMessage) -> None:
        """Perform security screening on the email content."""
        try:
            # Security validation using existing security service
            security_result = await self.security_service.validate_email_content(
                content=email.body,
                subject=email.subject,
                sender=email.sender_email
            )
            
            if not security_result["is_safe"]:
                logger.warning(f"Security screening flagged email {email.id}: {security_result['issues']}")
                # Could implement additional security actions here
                
        except Exception as e:
            logger.error(f"Security screening failed for email {email.id}: {str(e)}")
            # Security screening failure shouldn't stop processing but should be logged
    
    def _make_routing_decision(self, classification: ClassificationResult) -> Dict[str, Any]:
        """Make routing decision based on confidence and category."""
        confidence = classification.confidence
        category = classification.category
        urgency = classification.urgency
        
        # High urgency always gets special handling
        if urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            if confidence >= self.thresholds.suggest_response:
                return {
                    "action": "escalate",
                    "reason": f"High urgency ({urgency}) with sufficient confidence",
                    "confidence_met": True
                }
        
        # Standard confidence-based routing
        if confidence >= self.thresholds.auto_handle:
            # Auto-handle high-confidence classifications
            return {
                "action": "auto_handle",
                "reason": f"High confidence ({confidence}%) meets auto-handle threshold",
                "confidence_met": True
            }
        elif confidence >= self.thresholds.suggest_response:
            # Generate suggested response for medium confidence
            return {
                "action": "suggest_response", 
                "reason": f"Medium confidence ({confidence}%) - suggesting response for review",
                "confidence_met": True
            }
        elif confidence >= self.thresholds.escalate_review:
            # Flag for manual review
            return {
                "action": "manual_review",
                "reason": f"Low confidence ({confidence}%) - requires manual review",
                "confidence_met": False
            }
        else:
            # Immediate escalation for very low confidence
            return {
                "action": "escalate",
                "reason": f"Very low confidence ({confidence}%) - immediate escalation",
                "confidence_met": False
            }
    
    async def _handle_auto_processing(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult, 
        result: ProcessingResult
    ) -> None:
        """Handle high-confidence emails with automated responses."""
        result.status = ProcessingStatus.RESPONDING
        
        try:
            # Generate and send automated response
            response_content = await self.llm_service.generate_response_suggestion(email, classification)
            
            # Send the response
            success = await self.m365_client.send_reply(
                original_email=email,
                reply_content=response_content,
                is_html=False
            )
            
            if success:
                result.response_sent = True
                result.action_taken = f"Automated response sent for {classification.category}"
                logger.info(f"Automated response sent for email {email.id}")
            else:
                raise Exception("Failed to send automated response")
                
        except Exception as e:
            logger.error(f"Auto-processing failed for email {email.id}: {str(e)}")
            # Fall back to manual review
            await self._handle_manual_review(email, classification, result)
    
    async def _handle_suggested_response(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult, 
        result: ProcessingResult
    ) -> None:
        """Handle medium-confidence emails with suggested responses."""
        try:
            # Generate suggested response for human review
            suggested_response = await self.llm_service.generate_response_suggestion(email, classification)
            
            # Store suggestion for human review (would integrate with UI/dashboard)
            result.action_taken = f"Generated suggested response for {classification.category} (requires review)"
            
            # Could implement notification to staff here
            logger.info(f"Suggested response generated for email {email.id} - awaiting review")
            
        except Exception as e:
            logger.error(f"Response suggestion failed for email {email.id}: {str(e)}")
            await self._handle_manual_review(email, classification, result)
    
    async def _handle_escalation(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult, 
        result: ProcessingResult
    ) -> None:
        """Handle escalation by creating Teams groups and notifications."""
        result.status = ProcessingStatus.ESCALATING
        
        try:
            # Assess escalation needs
            escalation_info = await self.llm_service.assess_escalation_needs(email, classification)
            
            # Create Teams escalation group
            escalation_team = await self.teams_manager.create_escalation_team(
                email=email,
                classification=classification,
                escalation_info=escalation_info
            )
            
            result.escalation_id = escalation_team.team_id
            result.action_taken = f"Escalated to Teams group: {escalation_team.team_name}"
            
            logger.info(f"Email {email.id} escalated to Teams group {escalation_team.team_id}")
            
        except Exception as e:
            logger.error(f"Escalation failed for email {email.id}: {str(e)}")
            # Fall back to manual review
            await self._handle_manual_review(email, classification, result)
    
    async def _handle_manual_review(
        self, 
        email: EmailMessage, 
        classification: ClassificationResult, 
        result: ProcessingResult
    ) -> None:
        """Handle emails that require manual review."""
        try:
            result.action_taken = f"Flagged for manual review - {classification.category} with {classification.confidence}% confidence"
            
            # Could implement notification system here
            logger.info(f"Email {email.id} flagged for manual review")
            
        except Exception as e:
            logger.error(f"Manual review handling failed for email {email.id}: {str(e)}")
            result.error_message = f"Manual review setup failed: {str(e)}"
    
    def _update_processing_stats(self, result: ProcessingResult) -> None:
        """Update processing statistics."""
        self.processing_stats["total_processed"] += 1
        
        if result.status == ProcessingStatus.COMPLETED:
            if result.response_sent:
                self.processing_stats["auto_handled"] += 1
            elif result.escalation_id:
                self.processing_stats["escalated"] += 1
            else:
                self.processing_stats["suggested_responses"] += 1
        else:
            self.processing_stats["failed"] += 1
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            **self.processing_stats,
            "thresholds": {
                "auto_handle": self.thresholds.auto_handle,
                "suggest_response": self.thresholds.suggest_response,
                "escalate_review": self.thresholds.escalate_review
            }
        }
    
    async def validate_processing_pipeline(self) -> Dict[str, Any]:
        """Validate all components of the processing pipeline."""
        validation_results = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test M365 client
        try:
            m365_test = await self.m365_client.test_connectivity()
            validation_results["components"]["m365_client"] = {
                "status": "healthy" if m365_test["status"] == "success" else "unhealthy",
                "details": m365_test
            }
        except Exception as e:
            validation_results["components"]["m365_client"] = {
                "status": "error",
                "error": str(e)
            }
            validation_results["status"] = "degraded"
        
        # Test LLM service
        try:
            if self.llm_service.client:
                validation_results["components"]["llm_service"] = {"status": "healthy"}
            else:
                validation_results["components"]["llm_service"] = {"status": "unhealthy"}
                validation_results["status"] = "degraded"
        except Exception as e:
            validation_results["components"]["llm_service"] = {
                "status": "error",
                "error": str(e)
            }
            validation_results["status"] = "degraded"
        
        # Test Teams manager
        try:
            teams_test = await self.teams_manager.test_connectivity()
            validation_results["components"]["teams_manager"] = {
                "status": "healthy" if teams_test["status"] == "success" else "unhealthy",
                "details": teams_test
            }
        except Exception as e:
            validation_results["components"]["teams_manager"] = {
                "status": "error",
                "error": str(e)
            }
            validation_results["status"] = "degraded"
        
        return validation_results


# Singleton instance for use across the application
email_processor = EmailProcessingPipeline() 