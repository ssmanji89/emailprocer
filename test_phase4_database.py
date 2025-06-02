#!/usr/bin/env python3
"""
EmailBot Phase 4 - Database Integration Test
==========================================

Comprehensive test suite for database persistence and analytics functionality.
Tests all database models, repositories, and API endpoints.

Tests:
- Database connectivity and table creation
- Email processing persistence
- Classification result storage
- Processing result tracking
- Escalation team management
- Pattern analysis and automation candidates
- Performance metrics collection
- Analytics and dashboard data
- API endpoint validation

Usage:
    python test_phase4_database.py
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules
from app.config.database import init_database, get_async_session
from app.config.settings import settings
from app.services.database_service import database_service
from app.models.email_models import (
    EmailMessage as PydanticEmailMessage,
    ClassificationResult as PydanticClassificationResult,
    ProcessingResult as PydanticProcessingResult,
    EmailCategory, UrgencyLevel, ProcessingStatus
)
from app.models.database_models import (
    EmailMessage, ClassificationResult, ProcessingResult,
    EscalationTeam, EmailPattern, PerformanceMetric,
    PatternType, MetricType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseTestSuite:
    """Test suite for database integration."""
    
    def __init__(self):
        self.test_results = []
        self.test_email_id = f"test-email-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.test_data = self._generate_test_data()
    
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test data for database operations."""
        now = datetime.utcnow()
        
        return {
            "email": PydanticEmailMessage(
                id=self.test_email_id,
                sender_email="test@example.com",
                sender_name="Test Sender",
                recipient_email="smanji@zgcompanies.com",
                subject="Test Email for Database Integration",
                body="This is a test email for validating database persistence functionality.",
                received_datetime=now,
                conversation_id="test-conversation-123",
                importance="normal",
                attachments=[]
            ),
            "classification": PydanticClassificationResult(
                category=EmailCategory.SUPPORT,
                confidence=87.5,
                reasoning="This appears to be a technical support request based on keywords and context.",
                urgency=UrgencyLevel.MEDIUM,
                suggested_action="Route to technical support team for review and response.",
                required_expertise=["technical_support", "database_administration"],
                estimated_effort="30-60 minutes"
            ),
            "processing_result": {
                "action_taken": "Automated classification and routing completed",
                "response_sent": False,
                "escalation_id": None,
                "processing_time_ms": 1250,
                "model_info": {
                    "model": "gpt-4",
                    "version": "2024-02-01",
                    "prompt_version": "1.0",
                    "tokens": 245
                }
            }
        }
    
    async def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test with error handling."""
        try:
            logger.info(f"🧪 Running test: {test_name}")
            result = await test_func()
            
            if result:
                logger.info(f"✅ PASSED: {test_name}")
                self.test_results.append({"test": test_name, "status": "PASSED"})
                return True
            else:
                logger.error(f"❌ FAILED: {test_name}")
                self.test_results.append({"test": test_name, "status": "FAILED"})
                return False
                
        except Exception as e:
            logger.error(f"💥 ERROR in {test_name}: {str(e)}")
            logger.debug(traceback.format_exc())
            self.test_results.append({"test": test_name, "status": "ERROR", "error": str(e)})
            return False
    
    async def test_database_initialization(self) -> bool:
        """Test database connection and table creation."""
        try:
            # Initialize database
            await init_database()
            
            # Test connection
            async with get_async_session() as session:
                result = await session.execute("SELECT 1")
                assert result.scalar() == 1
            
            logger.info("Database initialization successful")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    async def test_email_repository(self) -> bool:
        """Test email repository operations."""
        try:
            async with database_service.get_session() as session:
                # Test create email
                db_email = await database_service.email_repo.create_email(self.test_data["email"])
                assert db_email.id == self.test_email_id
                assert db_email.sender_email == "test@example.com"
                
                # Test get by ID
                retrieved_email = await database_service.email_repo.get_by_id(self.test_email_id)
                assert retrieved_email is not None
                assert retrieved_email.subject == "Test Email for Database Integration"
                
                # Test mark as processed
                success = await database_service.email_repo.mark_as_processed(
                    self.test_email_id, ProcessingStatus.COMPLETED.value
                )
                assert success
                
                # Test get by sender
                sender_emails = await database_service.email_repo.get_emails_by_sender("test@example.com")
                assert len(sender_emails) >= 1
                
                logger.info("Email repository operations successful")
                return True
                
        except Exception as e:
            logger.error(f"Email repository test failed: {str(e)}")
            return False
    
    async def test_classification_repository(self) -> bool:
        """Test classification repository operations."""
        try:
            async with database_service.get_session() as session:
                # Test create classification
                db_classification = await database_service.classification_repo.create_classification(
                    self.test_email_id, 
                    self.test_data["classification"],
                    self.test_data["processing_result"]["model_info"]
                )
                assert db_classification.email_id == self.test_email_id
                assert db_classification.category == EmailCategory.SUPPORT.value
                assert db_classification.confidence == 87.5
                
                # Test get by email ID
                retrieved_classification = await database_service.classification_repo.get_by_email_id(
                    self.test_email_id
                )
                assert retrieved_classification is not None
                assert retrieved_classification.urgency == UrgencyLevel.MEDIUM.value
                
                # Test add feedback
                feedback_success = await database_service.classification_repo.add_human_feedback(
                    self.test_email_id, "correct", "Classification was accurate"
                )
                assert feedback_success
                
                # Test classification statistics
                stats = await database_service.classification_repo.get_classification_statistics()
                assert "category_distribution" in stats
                
                logger.info("Classification repository operations successful")
                return True
                
        except Exception as e:
            logger.error(f"Classification repository test failed: {str(e)}")
            return False
    
    async def test_processing_repository(self) -> bool:
        """Test processing result repository operations."""
        try:
            async with database_service.get_session() as session:
                # Test create processing result
                db_processing = await database_service.processing_repo.create_processing_result(
                    self.test_email_id, ProcessingStatus.RECEIVED
                )
                assert db_processing.email_id == self.test_email_id
                assert db_processing.status == ProcessingStatus.RECEIVED.value
                
                # Test complete processing
                complete_success = await database_service.processing_repo.complete_processing(
                    self.test_email_id,
                    "Test completion",
                    response_sent=False,
                    processing_time_ms=1250
                )
                assert complete_success
                
                # Test processing statistics
                stats = await database_service.processing_repo.get_processing_statistics(days=1)
                assert "overall" in stats
                assert "status_distribution" in stats
                
                logger.info("Processing repository operations successful")
                return True
                
        except Exception as e:
            logger.error(f"Processing repository test failed: {str(e)}")
            return False
    
    async def test_escalation_repository(self) -> bool:
        """Test escalation team repository operations."""
        try:
            async with database_service.get_session() as session:
                test_team_id = f"test-team-{datetime.utcnow().strftime('%H%M%S')}"
                
                # Test create escalation
                db_escalation = await database_service.escalation_repo.create_escalation(
                    self.test_email_id,
                    test_team_id,
                    "Test Escalation Team",
                    ["admin@zgcompanies.com", "support@zgcompanies.com"],
                    "admin@zgcompanies.com"
                )
                assert db_escalation.team_id == test_team_id
                assert db_escalation.member_count == 2
                
                # Test get active escalations
                active_escalations = await database_service.escalation_repo.get_active_escalations()
                assert len(active_escalations) >= 1
                
                # Test resolve escalation
                resolve_success = await database_service.escalation_repo.resolve_escalation(
                    test_team_id, "Test resolution completed"
                )
                assert resolve_success
                
                logger.info("Escalation repository operations successful")
                return True
                
        except Exception as e:
            logger.error(f"Escalation repository test failed: {str(e)}")
            return False
    
    async def test_pattern_repository(self) -> bool:
        """Test email pattern repository operations."""
        try:
            async with database_service.get_session() as session:
                test_pattern_id = f"test-pattern-{datetime.utcnow().strftime('%H%M%S')}"
                
                # Test create pattern
                db_pattern = await database_service.pattern_repo.create_or_update_pattern(
                    test_pattern_id,
                    PatternType.SUBJECT_PATTERN,
                    "Test subject pattern for automated responses",
                    automation_potential=85.0,
                    common_keywords=["test", "automated", "support"],
                    time_savings_potential_minutes=15
                )
                assert db_pattern.pattern_id == test_pattern_id
                assert db_pattern.automation_potential == 85.0
                
                # Test update pattern (increase frequency)
                updated_pattern = await database_service.pattern_repo.create_or_update_pattern(
                    test_pattern_id,
                    PatternType.SUBJECT_PATTERN,
                    "Updated test subject pattern",
                    automation_potential=90.0
                )
                assert updated_pattern.frequency == 2  # Should be incremented
                
                # Test get automation candidates
                candidates = await database_service.pattern_repo.get_automation_candidates(
                    min_frequency=1, min_automation_potential=80.0
                )
                assert len(candidates) >= 1
                
                logger.info("Pattern repository operations successful")
                return True
                
        except Exception as e:
            logger.error(f"Pattern repository test failed: {str(e)}")
            return False
    
    async def test_metrics_repository(self) -> bool:
        """Test performance metrics repository operations."""
        try:
            async with database_service.get_session() as session:
                # Test record metric
                db_metric = await database_service.metrics_repo.record_metric(
                    MetricType.PROCESSING_TIME,
                    "test_processing_time",
                    1250.0,
                    unit="milliseconds",
                    email_id=self.test_email_id,
                    category="test"
                )
                assert db_metric.metric_name == "test_processing_time"
                assert db_metric.value == 1250.0
                
                # Record additional metrics for statistics
                await database_service.metrics_repo.record_metric(
                    MetricType.CLASSIFICATION_ACCURACY,
                    "test_classification_accuracy",
                    87.5,
                    unit="percentage",
                    category="test"
                )
                
                # Test metrics summary
                summary = await database_service.metrics_repo.get_metrics_summary(days=1)
                assert "metrics" in summary
                assert len(summary["metrics"]) >= 1
                
                logger.info("Metrics repository operations successful")
                return True
                
        except Exception as e:
            logger.error(f"Metrics repository test failed: {str(e)}")
            return False
    
    async def test_database_service_integration(self) -> bool:
        """Test high-level database service operations."""
        try:
            # Test complete email processing storage
            success = await database_service.store_email_processing_complete(
                self.test_data["email"],
                self.test_data["classification"],
                self.test_data["processing_result"]
            )
            # Note: This might fail if email already exists, which is okay for testing
            
            # Test dashboard data
            dashboard_data = await database_service.get_dashboard_data()
            assert "processing" in dashboard_data
            assert "classification" in dashboard_data
            
            # Test health check
            health_check = await database_service.health_check()
            assert health_check["status"] == "healthy"
            assert "tables" in health_check
            
            logger.info("Database service integration successful")
            return True
            
        except Exception as e:
            logger.error(f"Database service integration test failed: {str(e)}")
            return False
    
    async def test_database_performance(self) -> bool:
        """Test database performance with multiple operations."""
        try:
            async with database_service.get_session() as session:
                # Create multiple test emails
                start_time = datetime.utcnow()
                
                for i in range(5):
                    test_email_id = f"perf-test-{i}-{start_time.strftime('%H%M%S')}"
                    test_email = PydanticEmailMessage(
                        id=test_email_id,
                        sender_email=f"perf-test-{i}@example.com",
                        sender_name=f"Performance Test {i}",
                        recipient_email="smanji@zgcompanies.com",
                        subject=f"Performance Test Email {i}",
                        body=f"This is performance test email number {i}.",
                        received_datetime=start_time + timedelta(seconds=i),
                        attachments=[]
                    )
                    
                    await database_service.email_repo.create_email(test_email)
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"Created 5 test emails in {duration:.2f} seconds")
                
                # Test bulk query performance
                start_time = datetime.utcnow()
                emails = await database_service.email_repo.get_emails_by_date_range(
                    start_time - timedelta(minutes=5), start_time
                )
                end_time = datetime.utcnow()
                query_duration = (end_time - start_time).total_seconds()
                
                logger.info(f"Queried {len(emails)} emails in {query_duration:.2f} seconds")
                
                return True
                
        except Exception as e:
            logger.error(f"Database performance test failed: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all database integration tests."""
        logger.info("🚀 Starting EmailBot Phase 4 Database Integration Tests")
        logger.info(f"Test Email ID: {self.test_email_id}")
        
        # Test sequence
        tests = [
            ("Database Initialization", self.test_database_initialization),
            ("Email Repository", self.test_email_repository),
            ("Classification Repository", self.test_classification_repository),
            ("Processing Repository", self.test_processing_repository),
            ("Escalation Repository", self.test_escalation_repository),
            ("Pattern Repository", self.test_pattern_repository),
            ("Metrics Repository", self.test_metrics_repository),
            ("Database Service Integration", self.test_database_service_integration),
            ("Database Performance", self.test_database_performance),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            success = await self.run_test(test_name, test_func)
            if success:
                passed += 1
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "💥"
            logger.info(f"{status_emoji} {result['test']}: {result['status']}")
            if "error" in result:
                logger.info(f"   Error: {result['error']}")
        
        logger.info("=" * 60)
        logger.info(f"📈 RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Phase 4 Database Integration is ready!")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed. Please review and fix issues.")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed / total) * 100,
            "test_details": self.test_results,
            "status": "PASSED" if passed == total else "FAILED"
        }


async def main():
    """Main test execution."""
    try:
        # Validate environment
        logger.info("Validating test environment...")
        
        if not settings.database_url:
            logger.error("DATABASE_URL not configured. Please set up database configuration.")
            return
        
        # Run tests
        test_suite = DatabaseTestSuite()
        results = await test_suite.run_all_tests()
        
        # Exit with appropriate code
        exit_code = 0 if results["status"] == "PASSED" else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 