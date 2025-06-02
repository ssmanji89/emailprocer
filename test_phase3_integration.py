#!/usr/bin/env python3
"""
EmailBot Phase 3 Integration Test Suite
Tests M365 Integration & Email Processing functionality
"""

import asyncio
import logging
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Setup path for imports
sys.path.append('.')

from app.services.email_processor import email_processor
from app.services.teams_manager import teams_manager
from app.services.scheduler import email_scheduler
from app.integrations.m365_client import M365EmailClient
from app.core.llm_service import LLMService
from app.models.email_models import EmailMessage, EmailCategory, UrgencyLevel
from app.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
settings = get_settings()


class Phase3TestSuite:
    """Comprehensive test suite for Phase 3 M365 Integration."""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.utcnow()
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", duration_ms: int = 0):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")

    async def test_m365_authentication(self) -> bool:
        """Test M365 authentication and permissions."""
        test_start = datetime.utcnow()
        
        try:
            # Test Graph API connectivity
            client = M365EmailClient()
            connectivity_test = await client.test_connectivity()
            
            if connectivity_test["status"] != "success":
                self.log_test_result(
                    "M365 Authentication",
                    False,
                    f"Authentication failed: {connectivity_test}",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            # Test Teams manager connectivity
            teams_test = await teams_manager.test_connectivity()
            
            if teams_test["status"] != "success":
                self.log_test_result(
                    "M365 Authentication",
                    False,
                    f"Teams connectivity failed: {teams_test}",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            self.log_test_result(
                "M365 Authentication",
                True,
                f"M365 Graph API and Teams connectivity successful. Mailbox: {connectivity_test.get('mailbox_email')}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "M365 Authentication",
                False,
                f"Exception: {str(e)}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return False

    async def test_llm_classification(self) -> bool:
        """Test LLM email classification."""
        test_start = datetime.utcnow()
        
        try:
            # Create test email
            test_email = EmailMessage(
                id="test-classification-001",
                sender_email="user@zgcompanies.com",
                sender_name="Test User",
                recipient_email=settings.target_mailbox,
                subject="Need help with password reset",
                body="Hi IT team, I forgot my password and can't log into my computer. Can you help me reset it? This is urgent as I have a meeting in 30 minutes. Thanks!",
                received_datetime=datetime.utcnow()
            )
            
            # Test classification
            llm_service = LLMService()
            classification = await llm_service.classify_email(test_email)
            
            # Validate classification result
            if not classification.category:
                self.log_test_result(
                    "LLM Classification",
                    False,
                    "No category returned from classification",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            if not (0 <= classification.confidence <= 100):
                self.log_test_result(
                    "LLM Classification",
                    False,
                    f"Invalid confidence score: {classification.confidence}",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            self.log_test_result(
                "LLM Classification",
                True,
                f"Email classified as {classification.category} with {classification.confidence}% confidence. Urgency: {classification.urgency}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "LLM Classification",
                False,
                f"Exception: {str(e)}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return False

    async def test_confidence_routing(self) -> bool:
        """Test confidence-based routing logic."""
        test_start = datetime.utcnow()
        
        try:
            # Test different confidence scenarios
            test_cases = [
                {
                    "name": "High Confidence (Auto-handle)",
                    "confidence": 90.0,
                    "expected_action": "auto_handle"
                },
                {
                    "name": "Medium Confidence (Suggest)",
                    "confidence": 75.0,
                    "expected_action": "suggest_response"
                },
                {
                    "name": "Low Confidence (Manual Review)",
                    "confidence": 50.0,
                    "expected_action": "manual_review"
                },
                {
                    "name": "Very Low Confidence (Escalate)",
                    "confidence": 20.0,
                    "expected_action": "escalate"
                }
            ]
            
            all_passed = True
            
            for test_case in test_cases:
                # Create mock classification result
                from app.models.email_models import ClassificationResult
                
                classification = ClassificationResult(
                    category=EmailCategory.SUPPORT,
                    confidence=test_case["confidence"],
                    reasoning="Test classification",
                    urgency=UrgencyLevel.MEDIUM,
                    suggested_action="Test action",
                    required_expertise=["it_admin"],
                    estimated_effort="15 minutes"
                )
                
                # Test routing decision
                routing_decision = email_processor._make_routing_decision(classification)
                
                if routing_decision["action"] != test_case["expected_action"]:
                    self.log_test_result(
                        f"Confidence Routing - {test_case['name']}",
                        False,
                        f"Expected {test_case['expected_action']}, got {routing_decision['action']}",
                        0
                    )
                    all_passed = False
                else:
                    self.log_test_result(
                        f"Confidence Routing - {test_case['name']}",
                        True,
                        f"Correctly routed to {routing_decision['action']}",
                        0
                    )
            
            duration = int((datetime.utcnow() - test_start).total_seconds() * 1000)
            
            if all_passed:
                self.log_test_result(
                    "Confidence Routing",
                    True,
                    "All routing scenarios passed",
                    duration
                )
            else:
                self.log_test_result(
                    "Confidence Routing",
                    False,
                    "Some routing scenarios failed",
                    duration
                )
            
            return all_passed
            
        except Exception as e:
            self.log_test_result(
                "Confidence Routing",
                False,
                f"Exception: {str(e)}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return False

    async def test_email_fetching(self) -> bool:
        """Test email fetching from M365."""
        test_start = datetime.utcnow()
        
        try:
            client = M365EmailClient()
            
            # Fetch recent emails (last 24 hours)
            since_datetime = datetime.utcnow() - timedelta(hours=24)
            emails = await client.fetch_new_emails(since_datetime)
            
            self.log_test_result(
                "Email Fetching",
                True,
                f"Successfully fetched {len(emails)} emails from the past 24 hours",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            
            # Log email details for debugging
            for i, email in enumerate(emails[:3]):  # Show first 3 emails
                logger.info(f"Email {i+1}: From {email.sender_email}, Subject: {email.subject[:50]}...")
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "Email Fetching",
                False,
                f"Exception: {str(e)}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return False

    async def test_processing_pipeline_validation(self) -> bool:
        """Test email processing pipeline validation."""
        test_start = datetime.utcnow()
        
        try:
            # Validate processing pipeline components
            validation_result = await email_processor.validate_processing_pipeline()
            
            if validation_result["status"] != "healthy":
                self.log_test_result(
                    "Processing Pipeline Validation",
                    False,
                    f"Pipeline validation failed: {validation_result}",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            # Check individual components
            components = validation_result.get("components", {})
            failed_components = [
                name for name, details in components.items()
                if details.get("status") != "healthy"
            ]
            
            if failed_components:
                self.log_test_result(
                    "Processing Pipeline Validation",
                    False,
                    f"Failed components: {', '.join(failed_components)}",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            self.log_test_result(
                "Processing Pipeline Validation",
                True,
                f"All pipeline components healthy: {', '.join(components.keys())}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Processing Pipeline Validation",
                False,
                f"Exception: {str(e)}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return False

    async def test_scheduler_functionality(self) -> bool:
        """Test email processing scheduler."""
        test_start = datetime.utcnow()
        
        try:
            # Get scheduler status
            status = email_scheduler.get_status()
            
            # Test scheduler health check
            health_check = await email_scheduler.health_check()
            
            # Test immediate trigger (without starting scheduler)
            trigger_result = await email_scheduler.trigger_immediate_run()
            
            if trigger_result["status"] != "completed":
                self.log_test_result(
                    "Scheduler Functionality",
                    False,
                    f"Immediate trigger failed: {trigger_result}",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            self.log_test_result(
                "Scheduler Functionality",
                True,
                f"Scheduler operational. Immediate trigger processed {trigger_result['result']['emails_processed']} emails",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Scheduler Functionality",
                False,
                f"Exception: {str(e)}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return False

    async def test_processing_statistics(self) -> bool:
        """Test processing statistics collection."""
        test_start = datetime.utcnow()
        
        try:
            # Get processing statistics
            processing_stats = email_processor.get_processing_statistics()
            
            # Get escalation statistics
            escalation_stats = teams_manager.get_escalation_statistics()
            
            # Validate statistics structure
            required_processing_fields = ["total_processed", "auto_handled", "suggested_responses", "escalated"]
            required_escalation_fields = ["total_escalations", "teams_created", "resolved_escalations"]
            
            missing_processing = [field for field in required_processing_fields if field not in processing_stats]
            missing_escalation = [field for field in required_escalation_fields if field not in escalation_stats]
            
            if missing_processing or missing_escalation:
                self.log_test_result(
                    "Processing Statistics",
                    False,
                    f"Missing stats fields - Processing: {missing_processing}, Escalation: {missing_escalation}",
                    int((datetime.utcnow() - test_start).total_seconds() * 1000)
                )
                return False
            
            self.log_test_result(
                "Processing Statistics",
                True,
                f"Statistics collected - Processed: {processing_stats['total_processed']}, Escalations: {escalation_stats['total_escalations']}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Processing Statistics",
                False,
                f"Exception: {str(e)}",
                int((datetime.utcnow() - test_start).total_seconds() * 1000)
            )
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 3 tests."""
        logger.info("🚀 Starting Phase 3 M365 Integration & Email Processing Tests")
        logger.info("=" * 80)
        
        test_functions = [
            self.test_m365_authentication,
            self.test_llm_classification,
            self.test_confidence_routing,
            self.test_email_fetching,
            self.test_processing_pipeline_validation,
            self.test_scheduler_functionality,
            self.test_processing_statistics,
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_func in test_functions:
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed with exception: {str(e)}")
        
        # Calculate results
        end_time = datetime.utcnow()
        total_duration = (end_time - self.start_time).total_seconds()
        success_rate = (passed_tests / total_tests) * 100
        
        # Generate summary
        summary = {
            "phase": "Phase 3 - M365 Integration & Email Processing",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "total_duration_seconds": total_duration,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "test_results": self.test_results
        }
        
        # Print summary
        logger.info("=" * 80)
        logger.info("📊 PHASE 3 TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Total Duration: {total_duration:.2f} seconds")
        
        if success_rate == 100:
            logger.info("🎉 ALL TESTS PASSED! Phase 3 implementation is ready for production.")
        elif success_rate >= 80:
            logger.info("⚠️  Most tests passed. Review failed tests before production deployment.")
        else:
            logger.info("❌ Multiple test failures. Phase 3 needs significant fixes before deployment.")
        
        return summary


async def main():
    """Main test execution function."""
    try:
        # Initialize test suite
        test_suite = Phase3TestSuite()
        
        # Run all tests
        results = await test_suite.run_all_tests()
        
        # Save results to file
        with open("phase3_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Test results saved to phase3_test_results.json")
        
        # Exit with appropriate code
        exit_code = 0 if results["success_rate"] == 100 else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Test suite execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 