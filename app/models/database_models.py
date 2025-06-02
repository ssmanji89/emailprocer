"""
EmailBot Database Models
=======================

SQLAlchemy ORM models for email processing persistence.
This module provides database models for storing email processing history,
classification results, and performance metrics.

This module provides:
- EmailMessage model for storing processed emails
- ClassificationResult model for LLM classification results
- ProcessingResult model for processing workflow tracking
- EscalationTeam model for Teams escalation tracking
- EmailPattern model for pattern analysis and learning
- PerformanceMetric model for system performance tracking
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Text, JSON, 
    Index, ForeignKey, Float, BigInteger, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum

from app.config.database import Base


# ===== ENUMS =====

class EmailCategory(str, Enum):
    """Email classification categories."""
    PURCHASING = "PURCHASING"
    SUPPORT = "SUPPORT"
    INFORMATION = "INFORMATION"
    ESCALATION = "ESCALATION"
    CONSULTATION = "CONSULTATION"


class ProcessingStatus(str, Enum):
    """Email processing workflow states."""
    RECEIVED = "received"
    VALIDATING = "validating"
    CLASSIFYING = "classifying"
    ANALYZING = "analyzing"
    ROUTING = "routing"
    RESPONDING = "responding"
    ESCALATING = "escalating"
    COMPLETED = "completed"
    FAILED = "failed"


class UrgencyLevel(str, Enum):
    """Email urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatternType(str, Enum):
    """Types of email patterns detected."""
    SUBJECT_PATTERN = "subject_pattern"
    SENDER_PATTERN = "sender_pattern"
    CONTENT_PATTERN = "content_pattern"
    TIMING_PATTERN = "timing_pattern"
    WORKFLOW_PATTERN = "workflow_pattern"


class MetricType(str, Enum):
    """Performance metric types."""
    PROCESSING_TIME = "processing_time"
    CLASSIFICATION_ACCURACY = "classification_accuracy"
    RESPONSE_TIME = "response_time"
    ESCALATION_RATE = "escalation_rate"
    SUCCESS_RATE = "success_rate"


# ===== DATABASE MODELS =====

class EmailMessage(Base):
    """
    Core email message storage with processing metadata.
    
    Stores all processed emails with full content and metadata
    for historical tracking and analysis.
    """
    __tablename__ = "email_messages"
    
    # Primary identification
    id = Column(String(255), primary_key=True)  # M365 email ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Email metadata
    sender_email = Column(String(255), nullable=False, index=True)
    sender_name = Column(String(255))
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(Text, nullable=False)
    
    # Email content
    body = Column(Text, nullable=False)
    html_body = Column(Text)
    
    # Temporal information
    received_datetime = Column(DateTime, nullable=False, index=True)
    processed_datetime = Column(DateTime, index=True)
    
    # Email context
    conversation_id = Column(String(255), index=True)
    importance = Column(String(50))
    attachments_count = Column(Integer, default=0)
    attachments_metadata = Column(JSON)  # Attachment details
    
    # Processing status
    processing_status = Column(String(50), default=ProcessingStatus.RECEIVED.value, index=True)
    retry_count = Column(Integer, default=0)
    last_error = Column(Text)
    
    # Relationships
    classification_result = relationship("ClassificationResult", back_populates="email", uselist=False)
    processing_results = relationship("ProcessingResult", back_populates="email")
    escalation_teams = relationship("EscalationTeam", back_populates="email")
    
    def __repr__(self):
        return f"<EmailMessage(id={self.id}, sender={self.sender_email}, subject='{self.subject[:50]}...')>"
    
    @hybrid_property
    def is_processed(self):
        """Check if email has been processed."""
        return self.processed_datetime is not None
    
    @hybrid_property
    def processing_duration_seconds(self):
        """Calculate processing duration if completed."""
        if self.processed_datetime and self.received_datetime:
            return (self.processed_datetime - self.received_datetime).total_seconds()
        return None


class ClassificationResult(Base):
    """
    LLM classification results for email categorization.
    
    Stores the AI classification output including confidence scores,
    reasoning, and suggested actions for each processed email.
    """
    __tablename__ = "classification_results"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(String(255), ForeignKey("email_messages.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Classification output
    category = Column(String(50), nullable=False, index=True)  # EmailCategory
    confidence = Column(Float, nullable=False, index=True)  # 0.0 to 100.0
    reasoning = Column(Text, nullable=False)
    
    # Urgency and action
    urgency = Column(String(20), nullable=False, index=True)  # UrgencyLevel
    suggested_action = Column(Text, nullable=False)
    
    # Expertise and effort
    required_expertise = Column(JSON)  # List of required skills
    estimated_effort = Column(String(100))  # Time estimate
    
    # LLM metadata
    model_used = Column(String(100))
    model_version = Column(String(50))
    prompt_version = Column(String(50))
    tokens_used = Column(Integer)
    
    # Feedback tracking
    human_feedback = Column(String(20))  # correct, incorrect, partial
    feedback_notes = Column(Text)
    feedback_timestamp = Column(DateTime)
    
    # Relationships
    email = relationship("EmailMessage", back_populates="classification_result")
    
    def __repr__(self):
        return f"<ClassificationResult(email_id={self.email_id}, category={self.category}, confidence={self.confidence})>"
    
    @hybrid_property
    def is_high_confidence(self):
        """Check if classification has high confidence."""
        return self.confidence >= 85.0
    
    @hybrid_property
    def is_low_confidence(self):
        """Check if classification has low confidence."""
        return self.confidence < 60.0


class ProcessingResult(Base):
    """
    Complete processing workflow tracking and results.
    
    Tracks the entire email processing pipeline including actions taken,
    escalations created, and performance metrics.
    """
    __tablename__ = "processing_results"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(String(255), ForeignKey("email_messages.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing status
    status = Column(String(50), nullable=False, index=True)  # ProcessingStatus
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    
    # Actions taken
    action_taken = Column(String(200))
    response_sent = Column(Boolean, default=False, index=True)
    escalation_created = Column(Boolean, default=False, index=True)
    escalation_id = Column(String(255))
    
    # Performance metrics
    processing_time_ms = Column(Integer)
    classification_time_ms = Column(Integer)
    response_generation_time_ms = Column(Integer)
    
    # Error handling
    error_message = Column(Text)
    error_stage = Column(String(50))  # Which stage failed
    retry_count = Column(Integer, default=0)
    
    # Context and metadata
    processing_context = Column(JSON)  # Additional context data
    confidence_routing = Column(String(50))  # How confidence was handled
    
    # Relationships
    email = relationship("EmailMessage", back_populates="processing_results")
    
    def __repr__(self):
        return f"<ProcessingResult(email_id={self.email_id}, status={self.status}, action={self.action_taken})>"
    
    @hybrid_property
    def is_successful(self):
        """Check if processing completed successfully."""
        return self.status == ProcessingStatus.COMPLETED.value
    
    @hybrid_property
    def processing_duration_seconds(self):
        """Calculate total processing duration."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class EscalationTeam(Base):
    """
    Teams escalation group tracking and management.
    
    Tracks Microsoft Teams groups created for email escalations
    including team composition and resolution status.
    """
    __tablename__ = "escalation_teams"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(String(255), nullable=False, unique=True, index=True)  # Teams group ID
    email_id = Column(String(255), ForeignKey("email_messages.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Team information
    team_name = Column(String(200), nullable=False)
    team_description = Column(Text)
    
    # Team composition
    members = Column(JSON, nullable=False)  # List of member email addresses
    member_count = Column(Integer, nullable=False)
    owner_email = Column(String(255))
    
    # Status tracking
    status = Column(String(50), default="active", index=True)  # active, resolved, abandoned
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    resolution_time_hours = Column(Float)
    
    # Teams integration
    teams_group_url = Column(String(500))
    channel_id = Column(String(255))
    message_count = Column(Integer, default=0)
    
    # Performance tracking
    first_response_time_minutes = Column(Integer)
    average_response_time_minutes = Column(Integer)
    participant_engagement_score = Column(Float)  # 0.0 to 10.0
    
    # Relationships
    email = relationship("EmailMessage", back_populates="escalation_teams")
    
    def __repr__(self):
        return f"<EscalationTeam(team_id={self.team_id}, email_id={self.email_id}, status={self.status})>"
    
    @hybrid_property
    def is_resolved(self):
        """Check if escalation has been resolved."""
        return self.status == "resolved" and self.resolved_at is not None
    
    @hybrid_property
    def days_since_creation(self):
        """Calculate days since team was created."""
        return (datetime.utcnow() - self.created_at).days


class EmailPattern(Base):
    """
    Discovered email patterns for automation and insights.
    
    Tracks recurring patterns in emails for automation opportunities
    and process improvement insights.
    """
    __tablename__ = "email_patterns"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(String(100), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pattern classification
    pattern_type = Column(String(50), nullable=False, index=True)  # PatternType
    description = Column(Text, nullable=False)
    pattern_signature = Column(String(500))  # Unique pattern identifier
    
    # Frequency tracking
    frequency = Column(Integer, nullable=False, default=1, index=True)
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    
    # Pattern analysis
    automation_potential = Column(Float, nullable=False, index=True)  # 0.0 to 100.0
    complexity_score = Column(Float, default=0.0)  # Pattern complexity
    confidence_level = Column(Float, default=0.0)  # Pattern reliability
    
    # Sample data
    sample_emails = Column(JSON)  # List of sample email IDs
    sample_count = Column(Integer, default=0)
    
    # Pattern characteristics
    common_keywords = Column(JSON)  # Frequently occurring words
    sender_patterns = Column(JSON)  # Common sender characteristics
    timing_patterns = Column(JSON)  # Time-based patterns
    
    # Impact analysis
    time_savings_potential_minutes = Column(Integer)
    affected_categories = Column(JSON)  # Email categories this pattern affects
    required_improvements = Column(JSON)  # What needs to be improved for automation
    
    def __repr__(self):
        return f"<EmailPattern(pattern_id={self.pattern_id}, type={self.pattern_type}, frequency={self.frequency})>"
    
    @hybrid_property
    def is_high_frequency(self):
        """Check if pattern occurs frequently."""
        return self.frequency >= 10
    
    @hybrid_property
    def is_automation_candidate(self):
        """Check if pattern is suitable for automation."""
        return self.automation_potential >= 70.0 and self.frequency >= 5


class PerformanceMetric(Base):
    """
    System performance metrics and analytics.
    
    Tracks various performance metrics for monitoring and optimization
    of the email processing system.
    """
    __tablename__ = "performance_metrics"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metric identification
    metric_type = Column(String(100), nullable=False, index=True)  # MetricType
    metric_name = Column(String(200), nullable=False, index=True)
    metric_category = Column(String(50), nullable=False, index=True)
    
    # Metric values
    value = Column(Float, nullable=False)
    value_unit = Column(String(50))  # seconds, percentage, count, etc.
    
    # Context information
    email_id = Column(String(255))  # Associated email if applicable
    time_period_start = Column(DateTime)
    time_period_end = Column(DateTime)
    
    # Aggregation metadata
    sample_size = Column(Integer)  # How many data points
    aggregation_method = Column(String(50))  # mean, median, sum, max, etc.
    
    # Additional metadata
    metadata = Column(JSON)  # Additional context data
    tags = Column(JSON)  # Classification tags
    
    def __repr__(self):
        return f"<PerformanceMetric(type={self.metric_type}, name={self.metric_name}, value={self.value})>"
    
    @hybrid_property
    def is_recent(self):
        """Check if metric is from the last 24 hours."""
        return (datetime.utcnow() - self.created_at).days == 0


# ===== DATABASE INDEXES =====

# Performance indexes for email messages
Index('idx_email_messages_sender_received', EmailMessage.sender_email, EmailMessage.received_datetime)
Index('idx_email_messages_status_received', EmailMessage.processing_status, EmailMessage.received_datetime)
Index('idx_email_messages_conversation', EmailMessage.conversation_id)

# Performance indexes for classification results
Index('idx_classification_category_confidence', ClassificationResult.category, ClassificationResult.confidence)
Index('idx_classification_urgency', ClassificationResult.urgency)
Index('idx_classification_created', ClassificationResult.created_at)

# Performance indexes for processing results
Index('idx_processing_status_created', ProcessingResult.status, ProcessingResult.created_at)
Index('idx_processing_timing', ProcessingResult.started_at, ProcessingResult.completed_at)
Index('idx_processing_performance', ProcessingResult.processing_time_ms)

# Performance indexes for escalation teams
Index('idx_escalation_status_created', EscalationTeam.status, EscalationTeam.created_at)
Index('idx_escalation_resolution', EscalationTeam.resolved_at)

# Performance indexes for email patterns
Index('idx_pattern_type_frequency', EmailPattern.pattern_type, EmailPattern.frequency)
Index('idx_pattern_automation', EmailPattern.automation_potential)
Index('idx_pattern_timing', EmailPattern.first_seen, EmailPattern.last_seen)

# Performance indexes for metrics
Index('idx_metrics_type_created', PerformanceMetric.metric_type, PerformanceMetric.created_at)
Index('idx_metrics_category_name', PerformanceMetric.metric_category, PerformanceMetric.metric_name)


# ===== UTILITY FUNCTIONS =====

def create_email_record(session, email_data: dict) -> EmailMessage:
    """Create email record from M365 email data."""
    email = EmailMessage(
        id=email_data["id"],
        sender_email=email_data["sender_email"],
        sender_name=email_data.get("sender_name"),
        recipient_email=email_data["recipient_email"],
        subject=email_data["subject"],
        body=email_data["body"],
        html_body=email_data.get("html_body"),
        received_datetime=email_data["received_datetime"],
        conversation_id=email_data.get("conversation_id"),
        importance=email_data.get("importance"),
        attachments_count=len(email_data.get("attachments", [])),
        attachments_metadata=email_data.get("attachments", [])
    )
    
    session.add(email)
    session.commit()
    session.refresh(email)
    
    return email


def record_performance_metric(session, metric_type: str, metric_name: str, 
                            value: float, **kwargs) -> PerformanceMetric:
    """Record a performance metric."""
    metric = PerformanceMetric(
        metric_type=metric_type,
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
    
    session.add(metric)
    session.commit()
    session.refresh(metric)
    
    return metric


# ===== CONSTRAINTS =====

# Ensure unique email processing results per email
UniqueConstraint('email_id', name='uq_classification_email')

# Ensure unique escalation team per email (if needed)
# UniqueConstraint('email_id', name='uq_escalation_email') 