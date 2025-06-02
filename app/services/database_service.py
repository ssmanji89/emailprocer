"""
EmailBot Database Service
========================

Database service layer with repository pattern for email processing persistence.
Provides high-level database operations for all email processing components.

This module provides:
- DatabaseService: Main service class for database operations
- Repository classes for each entity type
- Transaction management and error handling
- Performance metrics and analytics queries
- Data export and reporting capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

from sqlalchemy import func, select, update, delete, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.config.database import get_async_session
from app.models.database_models import (
    EmailMessage, ClassificationResult, ProcessingResult, 
    EscalationTeam, EmailPattern, PerformanceMetric,
    EmailCategory, ProcessingStatus, UrgencyLevel, PatternType, MetricType
)
from app.models.email_models import EmailMessage as PydanticEmailMessage
from app.models.email_models import ClassificationResult as PydanticClassificationResult

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def commit(self):
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        await self.session.rollback()
    
    async def refresh(self, instance):
        """Refresh instance from database."""
        await self.session.refresh(instance)


class EmailRepository(BaseRepository):
    """Repository for email message operations."""
    
    async def create_email(self, email_data: PydanticEmailMessage) -> EmailMessage:
        """Create new email record from Pydantic model."""
        try:
            db_email = EmailMessage(
                id=email_data.id,
                sender_email=email_data.sender_email,
                sender_name=email_data.sender_name,
                recipient_email=email_data.recipient_email,
                subject=email_data.subject,
                body=email_data.body,
                html_body=email_data.html_body,
                received_datetime=email_data.received_datetime,
                conversation_id=email_data.conversation_id,
                importance=email_data.importance,
                attachments_count=len(email_data.attachments) if email_data.attachments else 0,
                attachments_metadata=email_data.attachments or []
            )
            
            self.session.add(db_email)
            await self.commit()
            await self.refresh(db_email)
            
            logger.info(f"Created email record: {db_email.id}")
            return db_email
            
        except IntegrityError as e:
            await self.rollback()
            logger.warning(f"Email {email_data.id} already exists in database")
            return await self.get_by_id(email_data.id)
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to create email record: {str(e)}")
            raise
    
    async def get_by_id(self, email_id: str) -> Optional[EmailMessage]:
        """Get email by ID with related data."""
        try:
            stmt = select(EmailMessage).options(
                selectinload(EmailMessage.classification_result),
                selectinload(EmailMessage.processing_results),
                selectinload(EmailMessage.escalation_teams)
            ).where(EmailMessage.id == email_id)
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {str(e)}")
            return None
    
    async def get_unprocessed_emails(self, limit: int = 50) -> List[EmailMessage]:
        """Get emails that haven't been processed yet."""
        try:
            stmt = select(EmailMessage).where(
                EmailMessage.processed_datetime.is_(None)
            ).order_by(EmailMessage.received_datetime.asc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get unprocessed emails: {str(e)}")
            return []
    
    async def mark_as_processed(self, email_id: str, processing_status: str) -> bool:
        """Mark email as processed."""
        try:
            stmt = update(EmailMessage).where(
                EmailMessage.id == email_id
            ).values(
                processed_datetime=datetime.utcnow(),
                processing_status=processing_status
            )
            
            await self.session.execute(stmt)
            await self.commit()
            
            logger.debug(f"Marked email {email_id} as processed with status {processing_status}")
            return True
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to mark email {email_id} as processed: {str(e)}")
            return False
    
    async def get_emails_by_sender(self, sender_email: str, 
                                 limit: int = 20) -> List[EmailMessage]:
        """Get emails from specific sender."""
        try:
            stmt = select(EmailMessage).where(
                EmailMessage.sender_email == sender_email
            ).order_by(EmailMessage.received_datetime.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get emails from sender {sender_email}: {str(e)}")
            return []
    
    async def get_emails_by_date_range(self, start_date: datetime, 
                                     end_date: datetime) -> List[EmailMessage]:
        """Get emails within date range."""
        try:
            stmt = select(EmailMessage).where(
                and_(
                    EmailMessage.received_datetime >= start_date,
                    EmailMessage.received_datetime <= end_date
                )
            ).order_by(EmailMessage.received_datetime.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get emails by date range: {str(e)}")
            return []


class ClassificationRepository(BaseRepository):
    """Repository for classification result operations."""
    
    async def create_classification(self, email_id: str, 
                                  classification: PydanticClassificationResult,
                                  model_info: Dict[str, Any] = None) -> ClassificationResult:
        """Create classification result."""
        try:
            db_classification = ClassificationResult(
                email_id=email_id,
                category=classification.category.value,
                confidence=classification.confidence,
                reasoning=classification.reasoning,
                urgency=classification.urgency.value,
                suggested_action=classification.suggested_action,
                required_expertise=classification.required_expertise,
                estimated_effort=classification.estimated_effort,
                model_used=model_info.get("model") if model_info else "gpt-4",
                model_version=model_info.get("version") if model_info else "unknown",
                prompt_version=model_info.get("prompt_version") if model_info else "1.0",
                tokens_used=model_info.get("tokens") if model_info else 0
            )
            
            self.session.add(db_classification)
            await self.commit()
            await self.refresh(db_classification)
            
            logger.info(f"Created classification for email {email_id}: {classification.category} ({classification.confidence}%)")
            return db_classification
            
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to create classification for email {email_id}: {str(e)}")
            raise
    
    async def get_by_email_id(self, email_id: str) -> Optional[ClassificationResult]:
        """Get classification result by email ID."""
        try:
            stmt = select(ClassificationResult).where(
                ClassificationResult.email_id == email_id
            )
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get classification for email {email_id}: {str(e)}")
            return None
    
    async def add_human_feedback(self, email_id: str, feedback: str, 
                               notes: str = None) -> bool:
        """Add human feedback to classification."""
        try:
            stmt = update(ClassificationResult).where(
                ClassificationResult.email_id == email_id
            ).values(
                human_feedback=feedback,
                feedback_notes=notes,
                feedback_timestamp=datetime.utcnow()
            )
            
            await self.session.execute(stmt)
            await self.commit()
            
            logger.info(f"Added feedback '{feedback}' to classification for email {email_id}")
            return True
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to add feedback for email {email_id}: {str(e)}")
            return False
    
    async def get_classification_statistics(self) -> Dict[str, Any]:
        """Get classification statistics."""
        try:
            # Category distribution
            category_stats = await self.session.execute(
                select(
                    ClassificationResult.category,
                    func.count().label('count'),
                    func.avg(ClassificationResult.confidence).label('avg_confidence')
                ).group_by(ClassificationResult.category)
            )
            
            # Confidence distribution
            confidence_stats = await self.session.execute(
                select(
                    func.count().label('total'),
                    func.avg(ClassificationResult.confidence).label('avg_confidence'),
                    func.min(ClassificationResult.confidence).label('min_confidence'),
                    func.max(ClassificationResult.confidence).label('max_confidence')
                )
            )
            
            # Feedback statistics
            feedback_stats = await self.session.execute(
                select(
                    ClassificationResult.human_feedback,
                    func.count().label('count')
                ).where(
                    ClassificationResult.human_feedback.is_not(None)
                ).group_by(ClassificationResult.human_feedback)
            )
            
            return {
                "category_distribution": [
                    {"category": row.category, "count": row.count, "avg_confidence": float(row.avg_confidence)}
                    for row in category_stats
                ],
                "confidence_stats": confidence_stats.first()._asdict(),
                "feedback_distribution": [
                    {"feedback": row.human_feedback, "count": row.count}
                    for row in feedback_stats
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get classification statistics: {str(e)}")
            return {}


class ProcessingRepository(BaseRepository):
    """Repository for processing result operations."""
    
    async def create_processing_result(self, email_id: str, 
                                     status: ProcessingStatus = ProcessingStatus.RECEIVED) -> ProcessingResult:
        """Create initial processing result."""
        try:
            db_result = ProcessingResult(
                email_id=email_id,
                status=status.value,
                started_at=datetime.utcnow()
            )
            
            self.session.add(db_result)
            await self.commit()
            await self.refresh(db_result)
            
            logger.debug(f"Created processing result for email {email_id}")
            return db_result
            
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to create processing result for email {email_id}: {str(e)}")
            raise
    
    async def update_processing_result(self, email_id: str, 
                                     update_data: Dict[str, Any]) -> bool:
        """Update processing result."""
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            stmt = update(ProcessingResult).where(
                ProcessingResult.email_id == email_id
            ).values(**update_data)
            
            await self.session.execute(stmt)
            await self.commit()
            
            logger.debug(f"Updated processing result for email {email_id}")
            return True
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to update processing result for email {email_id}: {str(e)}")
            return False
    
    async def complete_processing(self, email_id: str, action_taken: str,
                                response_sent: bool = False, escalation_id: str = None,
                                processing_time_ms: int = None) -> bool:
        """Mark processing as completed."""
        try:
            update_data = {
                "status": ProcessingStatus.COMPLETED.value,
                "completed_at": datetime.utcnow(),
                "action_taken": action_taken,
                "response_sent": response_sent
            }
            
            if escalation_id:
                update_data["escalation_id"] = escalation_id
                update_data["escalation_created"] = True
            
            if processing_time_ms:
                update_data["processing_time_ms"] = processing_time_ms
            
            return await self.update_processing_result(email_id, update_data)
        except Exception as e:
            logger.error(f"Failed to complete processing for email {email_id}: {str(e)}")
            return False
    
    async def fail_processing(self, email_id: str, error_message: str,
                            error_stage: str = None) -> bool:
        """Mark processing as failed."""
        try:
            update_data = {
                "status": ProcessingStatus.FAILED.value,
                "completed_at": datetime.utcnow(),
                "error_message": error_message
            }
            
            if error_stage:
                update_data["error_stage"] = error_stage
            
            return await self.update_processing_result(email_id, update_data)
        except Exception as e:
            logger.error(f"Failed to mark processing as failed for email {email_id}: {str(e)}")
            return False
    
    async def get_processing_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get processing performance statistics."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Overall statistics
            overall_stats = await self.session.execute(
                select(
                    func.count().label('total_processed'),
                    func.sum(func.case((ProcessingResult.status == ProcessingStatus.COMPLETED.value, 1), else_=0)).label('successful'),
                    func.sum(func.case((ProcessingResult.status == ProcessingStatus.FAILED.value, 1), else_=0)).label('failed'),
                    func.sum(func.case((ProcessingResult.response_sent == True, 1), else_=0)).label('responses_sent'),
                    func.sum(func.case((ProcessingResult.escalation_created == True, 1), else_=0)).label('escalations_created'),
                    func.avg(ProcessingResult.processing_time_ms).label('avg_processing_time_ms'),
                    func.max(ProcessingResult.processing_time_ms).label('max_processing_time_ms')
                ).where(ProcessingResult.created_at >= since_date)
            )
            
            # Status distribution
            status_stats = await self.session.execute(
                select(
                    ProcessingResult.status,
                    func.count().label('count')
                ).where(
                    ProcessingResult.created_at >= since_date
                ).group_by(ProcessingResult.status)
            )
            
            # Performance trends (daily)
            daily_stats = await self.session.execute(
                select(
                    func.date(ProcessingResult.created_at).label('date'),
                    func.count().label('count'),
                    func.avg(ProcessingResult.processing_time_ms).label('avg_time_ms')
                ).where(
                    ProcessingResult.created_at >= since_date
                ).group_by(func.date(ProcessingResult.created_at))
                .order_by(func.date(ProcessingResult.created_at))
            )
            
            overall = overall_stats.first()
            
            return {
                "period_days": days,
                "overall": overall._asdict() if overall else {},
                "status_distribution": [
                    {"status": row.status, "count": row.count}
                    for row in status_stats
                ],
                "daily_trends": [
                    {"date": row.date.isoformat(), "count": row.count, "avg_time_ms": float(row.avg_time_ms or 0)}
                    for row in daily_stats
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get processing statistics: {str(e)}")
            return {}


class EscalationRepository(BaseRepository):
    """Repository for escalation team operations."""
    
    async def create_escalation(self, email_id: str, team_id: str, team_name: str,
                              members: List[str], owner_email: str = None) -> EscalationTeam:
        """Create escalation team record."""
        try:
            db_escalation = EscalationTeam(
                team_id=team_id,
                email_id=email_id,
                team_name=team_name,
                members=members,
                member_count=len(members),
                owner_email=owner_email or members[0] if members else None
            )
            
            self.session.add(db_escalation)
            await self.commit()
            await self.refresh(db_escalation)
            
            logger.info(f"Created escalation team {team_id} for email {email_id}")
            return db_escalation
            
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to create escalation for email {email_id}: {str(e)}")
            raise
    
    async def resolve_escalation(self, team_id: str, resolution_notes: str) -> bool:
        """Mark escalation as resolved."""
        try:
            resolved_at = datetime.utcnow()
            
            # Get escalation to calculate resolution time
            escalation = await self.session.execute(
                select(EscalationTeam).where(EscalationTeam.team_id == team_id)
            )
            escalation = escalation.scalar_one_or_none()
            
            if not escalation:
                logger.warning(f"Escalation team {team_id} not found")
                return False
            
            resolution_time_hours = (resolved_at - escalation.created_at).total_seconds() / 3600
            
            stmt = update(EscalationTeam).where(
                EscalationTeam.team_id == team_id
            ).values(
                status="resolved",
                resolved_at=resolved_at,
                resolution_notes=resolution_notes,
                resolution_time_hours=resolution_time_hours
            )
            
            await self.session.execute(stmt)
            await self.commit()
            
            logger.info(f"Resolved escalation team {team_id} after {resolution_time_hours:.1f} hours")
            return True
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to resolve escalation {team_id}: {str(e)}")
            return False
    
    async def get_active_escalations(self) -> List[EscalationTeam]:
        """Get all active escalation teams."""
        try:
            stmt = select(EscalationTeam).where(
                EscalationTeam.status == "active"
            ).order_by(EscalationTeam.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get active escalations: {str(e)}")
            return []


class PatternRepository(BaseRepository):
    """Repository for email pattern operations."""
    
    async def create_or_update_pattern(self, pattern_id: str, pattern_type: PatternType,
                                     description: str, **kwargs) -> EmailPattern:
        """Create new pattern or update existing one."""
        try:
            # Check if pattern exists
            existing = await self.session.execute(
                select(EmailPattern).where(EmailPattern.pattern_id == pattern_id)
            )
            existing = existing.scalar_one_or_none()
            
            if existing:
                # Update existing pattern
                existing.frequency += 1
                existing.last_seen = datetime.utcnow()
                existing.description = description
                
                # Update optional fields
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                
                await self.commit()
                await self.refresh(existing)
                
                logger.debug(f"Updated pattern {pattern_id} (frequency: {existing.frequency})")
                return existing
            else:
                # Create new pattern
                now = datetime.utcnow()
                db_pattern = EmailPattern(
                    pattern_id=pattern_id,
                    pattern_type=pattern_type.value,
                    description=description,
                    frequency=1,
                    first_seen=now,
                    last_seen=now,
                    automation_potential=kwargs.get("automation_potential", 0.0),
                    **{k: v for k, v in kwargs.items() if k != "automation_potential"}
                )
                
                self.session.add(db_pattern)
                await self.commit()
                await self.refresh(db_pattern)
                
                logger.info(f"Created new pattern {pattern_id}")
                return db_pattern
                
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to create/update pattern {pattern_id}: {str(e)}")
            raise
    
    async def get_automation_candidates(self, min_frequency: int = 5,
                                      min_automation_potential: float = 70.0) -> List[EmailPattern]:
        """Get patterns that are good automation candidates."""
        try:
            stmt = select(EmailPattern).where(
                and_(
                    EmailPattern.frequency >= min_frequency,
                    EmailPattern.automation_potential >= min_automation_potential
                )
            ).order_by(EmailPattern.automation_potential.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get automation candidates: {str(e)}")
            return []


class MetricsRepository(BaseRepository):
    """Repository for performance metrics operations."""
    
    async def record_metric(self, metric_type: MetricType, metric_name: str,
                          value: float, **kwargs) -> PerformanceMetric:
        """Record a performance metric."""
        try:
            db_metric = PerformanceMetric(
                metric_type=metric_type.value,
                metric_name=metric_name,
                metric_category=kwargs.get("category", "general"),
                value=value,
                value_unit=kwargs.get("unit", ""),
                email_id=kwargs.get("email_id"),
                sample_size=kwargs.get("sample_size", 1),
                aggregation_method=kwargs.get("aggregation", "single"),
                metadata=kwargs.get("metadata", {}),
                tags=kwargs.get("tags", [])
            )
            
            self.session.add(db_metric)
            await self.commit()
            await self.refresh(db_metric)
            
            logger.debug(f"Recorded metric {metric_name}: {value}")
            return db_metric
            
        except Exception as e:
            await self.rollback()
            logger.error(f"Failed to record metric {metric_name}: {str(e)}")
            raise
    
    async def get_metrics_summary(self, metric_type: MetricType = None,
                                days: int = 7) -> Dict[str, Any]:
        """Get metrics summary for the specified period."""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = select(
                PerformanceMetric.metric_name,
                func.count().label('count'),
                func.avg(PerformanceMetric.value).label('avg_value'),
                func.min(PerformanceMetric.value).label('min_value'),
                func.max(PerformanceMetric.value).label('max_value')
            ).where(PerformanceMetric.created_at >= since_date)
            
            if metric_type:
                stmt = stmt.where(PerformanceMetric.metric_type == metric_type.value)
            
            stmt = stmt.group_by(PerformanceMetric.metric_name)
            
            result = await self.session.execute(stmt)
            
            return {
                "period_days": days,
                "metrics": [
                    {
                        "name": row.metric_name,
                        "count": row.count,
                        "average": float(row.avg_value),
                        "minimum": float(row.min_value),
                        "maximum": float(row.max_value)
                    }
                    for row in result
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {str(e)}")
            return {}


class DatabaseService:
    """Main database service providing high-level operations."""
    
    def __init__(self):
        self.email_repo: Optional[EmailRepository] = None
        self.classification_repo: Optional[ClassificationRepository] = None
        self.processing_repo: Optional[ProcessingRepository] = None
        self.escalation_repo: Optional[EscalationRepository] = None
        self.pattern_repo: Optional[PatternRepository] = None
        self.metrics_repo: Optional[MetricsRepository] = None
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with repository initialization."""
        async with get_async_session() as session:
            # Initialize repositories
            self.email_repo = EmailRepository(session)
            self.classification_repo = ClassificationRepository(session)
            self.processing_repo = ProcessingRepository(session)
            self.escalation_repo = EscalationRepository(session)
            self.pattern_repo = PatternRepository(session)
            self.metrics_repo = MetricsRepository(session)
            
            try:
                yield session
            finally:
                # Clean up repositories
                self.email_repo = None
                self.classification_repo = None
                self.processing_repo = None
                self.escalation_repo = None
                self.pattern_repo = None
                self.metrics_repo = None
    
    async def store_email_processing_complete(self, email_data: PydanticEmailMessage,
                                           classification: PydanticClassificationResult,
                                           processing_result: Dict[str, Any]) -> bool:
        """Store complete email processing results in a single transaction."""
        try:
            async with self.get_session() as session:
                # 1. Store email
                db_email = await self.email_repo.create_email(email_data)
                
                # 2. Store classification
                await self.classification_repo.create_classification(
                    db_email.id, classification, processing_result.get("model_info")
                )
                
                # 3. Create processing result
                db_processing = await self.processing_repo.create_processing_result(
                    db_email.id, ProcessingStatus.COMPLETED
                )
                
                # 4. Update processing result with completion data
                await self.processing_repo.complete_processing(
                    db_email.id,
                    processing_result.get("action_taken", "Processed automatically"),
                    processing_result.get("response_sent", False),
                    processing_result.get("escalation_id"),
                    processing_result.get("processing_time_ms")
                )
                
                # 5. Mark email as processed
                await self.email_repo.mark_as_processed(
                    db_email.id, ProcessingStatus.COMPLETED.value
                )
                
                # 6. Record performance metrics
                if processing_result.get("processing_time_ms"):
                    await self.metrics_repo.record_metric(
                        MetricType.PROCESSING_TIME,
                        "email_processing_time",
                        processing_result["processing_time_ms"],
                        unit="milliseconds",
                        email_id=db_email.id,
                        category="performance"
                    )
                
                logger.info(f"Successfully stored complete processing results for email {db_email.id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to store email processing results: {str(e)}")
            return False
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        try:
            async with self.get_session() as session:
                # Get processing statistics
                processing_stats = await self.processing_repo.get_processing_statistics()
                
                # Get classification statistics
                classification_stats = await self.classification_repo.get_classification_statistics()
                
                # Get active escalations
                active_escalations = await self.escalation_repo.get_active_escalations()
                
                # Get automation candidates
                automation_candidates = await self.pattern_repo.get_automation_candidates()
                
                # Get recent metrics
                metrics_summary = await self.metrics_repo.get_metrics_summary()
                
                return {
                    "processing": processing_stats,
                    "classification": classification_stats,
                    "active_escalations": len(active_escalations),
                    "escalation_details": [
                        {
                            "team_id": esc.team_id,
                            "email_id": esc.email_id,
                            "team_name": esc.team_name,
                            "created_at": esc.created_at.isoformat(),
                            "member_count": esc.member_count,
                            "days_active": esc.days_since_creation
                        }
                        for esc in active_escalations[:10]  # Limit to 10 most recent
                    ],
                    "automation_opportunities": len(automation_candidates),
                    "automation_details": [
                        {
                            "pattern_id": pattern.pattern_id,
                            "description": pattern.description,
                            "frequency": pattern.frequency,
                            "automation_potential": pattern.automation_potential
                        }
                        for pattern in automation_candidates[:5]  # Top 5 candidates
                    ],
                    "metrics": metrics_summary
                }
                
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            async with self.get_session() as session:
                # Test basic connectivity
                await session.execute(select(1))
                
                # Get table counts
                email_count = await session.execute(
                    select(func.count(EmailMessage.id))
                )
                
                classification_count = await session.execute(
                    select(func.count(ClassificationResult.id))
                )
                
                processing_count = await session.execute(
                    select(func.count(ProcessingResult.id))
                )
                
                return {
                    "status": "healthy",
                    "tables": {
                        "emails": email_count.scalar(),
                        "classifications": classification_count.scalar(),
                        "processing_results": processing_count.scalar()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Singleton instance for use across the application
database_service = DatabaseService() 