from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class EmailCategory(str, Enum):
    PURCHASING = "PURCHASING"
    SUPPORT = "SUPPORT"
    INFORMATION = "INFORMATION"
    ESCALATION = "ESCALATION"
    CONSULTATION = "CONSULTATION"


class UrgencyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProcessingStatus(str, Enum):
    RECEIVED = "received"
    CLASSIFYING = "classifying"
    ANALYZING = "analyzing"
    ROUTING = "routing"
    RESPONDING = "responding"
    ESCALATING = "escalating"
    COMPLETED = "completed"
    FAILED = "failed"


class EmailMessage(BaseModel):
    id: str = Field(..., description="Unique email identifier")
    sender_email: EmailStr = Field(..., description="Sender email address")
    sender_name: Optional[str] = Field(None, description="Sender display name")
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    html_body: Optional[str] = Field(None, description="HTML email body")
    received_datetime: datetime = Field(..., description="When email was received")
    processed_datetime: Optional[datetime] = Field(None, description="When processing started")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Email attachments")
    conversation_id: Optional[str] = Field(None, description="Email thread identifier")
    importance: Optional[str] = Field(None, description="Email importance level")
    
    class Config:
        from_attributes = True


class ClassificationResult(BaseModel):
    category: EmailCategory = Field(..., description="Classified email category")
    confidence: float = Field(..., ge=0, le=100, description="Classification confidence score")
    reasoning: str = Field(..., description="Explanation of classification decision")
    urgency: UrgencyLevel = Field(..., description="Urgency assessment")
    suggested_action: str = Field(..., description="Recommended action to take")
    required_expertise: List[str] = Field(default_factory=list, description="Required skills/knowledge")
    estimated_effort: str = Field(..., description="Time estimate for resolution")
    
    class Config:
        from_attributes = True


class ProcessingResult(BaseModel):
    email_id: str = Field(..., description="Reference to processed email")
    status: ProcessingStatus = Field(..., description="Current processing status")
    classification: Optional[ClassificationResult] = Field(None, description="LLM classification result")
    action_taken: Optional[str] = Field(None, description="Action that was executed")
    escalation_id: Optional[str] = Field(None, description="Teams escalation group ID")
    response_sent: bool = Field(default=False, description="Whether automated response was sent")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error details if processing failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When result was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class EmailPattern(BaseModel):
    pattern_id: str = Field(..., description="Unique pattern identifier")
    pattern_type: str = Field(..., description="Type of pattern detected")
    description: str = Field(..., description="Human-readable pattern description")
    frequency: int = Field(..., ge=1, description="Number of occurrences")
    first_seen: datetime = Field(..., description="When pattern was first detected")
    last_seen: datetime = Field(..., description="Most recent occurrence")
    automation_potential: float = Field(..., ge=0, le=100, description="Automation feasibility score")
    sample_emails: List[str] = Field(default_factory=list, description="Sample email IDs")
    
    class Config:
        from_attributes = True


class EscalationTeam(BaseModel):
    team_id: str = Field(..., description="Teams group identifier")
    email_id: str = Field(..., description="Associated email")
    team_name: str = Field(..., description="Descriptive team name")
    members: List[str] = Field(default_factory=list, description="Team member email addresses")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When team was created")
    resolved_at: Optional[datetime] = Field(None, description="When issue was resolved")
    resolution_notes: Optional[str] = Field(None, description="Resolution summary")
    
    class Config:
        from_attributes = True 