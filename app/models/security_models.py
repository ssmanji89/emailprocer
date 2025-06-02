"""
EmailBot Security Models
=======================

Security-focused database models for audit logging, authentication tracking,
and security event management.

This module provides:
- AuditLog model for comprehensive security event tracking
- AuthenticationAttempt model for login monitoring and lockout
- SecurityEvent model for security incident management
- EncryptionKeyMetadata model for key lifecycle tracking
- SecurityConfiguration model for security settings
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.config.database import Base


class AuditLogType(str, Enum):
    """Enumeration of audit log event types."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    ENCRYPTION = "encryption"
    DECRYPTION = "decryption"
    SECURITY_EVENT = "security_event"
    CONFIGURATION_CHANGE = "configuration_change"
    API_REQUEST = "api_request"
    ERROR = "error"


class SecurityEventSeverity(str, Enum):
    """Enumeration of security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuthenticationStatus(str, Enum):
    """Enumeration of authentication attempt statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    LOCKED_OUT = "locked_out"
    EXPIRED = "expired"
    INVALID_TOKEN = "invalid_token"


# =====  PYDANTIC MODELS =====

class AuditLogCreate(BaseModel):
    """Pydantic model for creating audit log entries."""
    event_type: AuditLogType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class SecurityEventCreate(BaseModel):
    """Pydantic model for creating security events."""
    event_type: str
    severity: SecurityEventSeverity
    description: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    affected_resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    mitigation_action: Optional[str] = None


class AuthenticationAttemptCreate(BaseModel):
    """Pydantic model for authentication attempts."""
    user_identifier: str
    auth_method: str
    ip_address: str
    user_agent: Optional[str] = None
    status: AuthenticationStatus
    failure_reason: Optional[str] = None
    token_used: Optional[str] = None


# ===== DATABASE MODELS =====

class AuditLog(Base):
    """
    Comprehensive audit log for security events and data access.
    
    Tracks all security-relevant events in the system for compliance
    and security monitoring purposes.
    """
    __tablename__ = "audit_logs"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Event classification
    event_type = Column(String(50), nullable=False)  # AuditLogType
    action = Column(String(100), nullable=False)
    
    # User context
    user_id = Column(String(100))
    session_id = Column(String(100))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    
    # Resource information
    resource_type = Column(String(50))  # e.g., 'email', 'user', 'configuration'
    resource_id = Column(String(100))
    
    # Event details
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text)
    details = Column(JSON)  # Additional event-specific data
    
    # Performance tracking
    execution_time_ms = Column(Integer)  # Time taken for the operation
    
    # Security context
    risk_score = Column(Integer, default=0)  # 0-100 risk assessment
    requires_review = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, type={self.event_type}, action={self.action})>"
    
    @classmethod
    def create_log(cls, event_data: AuditLogCreate, **kwargs) -> 'AuditLog':
        """Create audit log entry from pydantic model."""
        return cls(
            event_type=event_data.event_type.value,
            user_id=event_data.user_id,
            session_id=event_data.session_id,
            ip_address=event_data.ip_address,
            user_agent=event_data.user_agent,
            resource_type=event_data.resource_type,
            resource_id=event_data.resource_id,
            action=event_data.action,
            details=event_data.details,
            success=event_data.success,
            error_message=event_data.error_message,
            **kwargs
        )


class AuthenticationAttempt(Base):
    """
    Track authentication attempts for security monitoring and lockout management.
    
    Used to implement failed attempt tracking, progressive lockouts,
    and authentication analytics.
    """
    __tablename__ = "authentication_attempts"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Authentication details
    user_identifier = Column(String(255), nullable=False)  # email, username, etc.
    auth_method = Column(String(50), nullable=False)  # 'password', 'token', 'oauth'
    status = Column(String(20), nullable=False)  # AuthenticationStatus
    
    # Network context
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    
    # Failure details
    failure_reason = Column(String(200))
    failure_count = Column(Integer, default=1)
    
    # Token information (if applicable)
    token_used = Column(String(100))  # Partial token for tracking
    token_type = Column(String(50))
    
    # Security assessment
    risk_score = Column(Integer, default=0)
    suspicious_activity = Column(Boolean, default=False)
    
    # Geographic information (optional)
    country = Column(String(2))  # ISO country code
    city = Column(String(100))
    
    def __repr__(self):
        return f"<AuthenticationAttempt(id={self.id}, user={self.user_identifier}, status={self.status})>"
    
    @classmethod
    def create_attempt(cls, attempt_data: AuthenticationAttemptCreate, **kwargs) -> 'AuthenticationAttempt':
        """Create authentication attempt from pydantic model."""
        return cls(
            user_identifier=attempt_data.user_identifier,
            auth_method=attempt_data.auth_method,
            ip_address=attempt_data.ip_address,
            user_agent=attempt_data.user_agent,
            status=attempt_data.status.value,
            failure_reason=attempt_data.failure_reason,
            token_used=attempt_data.token_used,
            **kwargs
        )


class SecurityEvent(Base):
    """
    Track security incidents and threats for monitoring and response.
    
    Used for security incident management, threat detection,
    and security operations center (SOC) activities.
    """
    __tablename__ = "security_events"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Event classification
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # SecurityEventSeverity
    status = Column(String(20), default="open")  # open, investigating, resolved, false_positive
    
    # Event description
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Source information
    source_ip = Column(String(45))
    source_system = Column(String(100))
    user_id = Column(String(100))
    
    # Affected resources
    affected_resource = Column(String(200))
    resource_count = Column(Integer, default=1)
    
    # Event details
    details = Column(JSON)
    indicators = Column(JSON)  # IOCs, signatures, etc.
    
    # Response tracking
    assigned_to = Column(String(100))
    mitigation_action = Column(Text)
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    
    # Risk assessment
    risk_score = Column(Integer, default=0)
    impact_score = Column(Integer, default=0)
    likelihood_score = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"
    
    @classmethod
    def create_event(cls, event_data: SecurityEventCreate, **kwargs) -> 'SecurityEvent':
        """Create security event from pydantic model."""
        return cls(
            event_type=event_data.event_type,
            severity=event_data.severity.value,
            title=event_data.description[:200],  # Use description as title (truncated)
            description=event_data.description,
            source_ip=event_data.source_ip,
            user_id=event_data.user_id,
            affected_resource=event_data.affected_resource,
            details=event_data.details,
            mitigation_action=event_data.mitigation_action,
            **kwargs
        )


class EncryptionKeyMetadata(Base):
    """
    Track encryption key lifecycle and usage for key management.
    
    Maintains metadata about encryption keys including creation,
    rotation, usage statistics, and deactivation.
    """
    __tablename__ = "encryption_key_metadata"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_id = Column(String(100), nullable=False, unique=True)
    
    # Key lifecycle
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime)
    deactivated_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Key properties
    key_type = Column(String(50), nullable=False)  # 'fernet', 'rsa', 'aes'
    key_purpose = Column(String(100))  # 'email_content', 'user_data', 'general'
    key_algorithm = Column(String(50))
    key_length = Column(Integer)
    
    # Status and usage
    status = Column(String(20), default="active")  # active, inactive, rotated, compromised
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # Security metadata
    derivation_method = Column(String(100))  # How the key was derived
    salt = Column(String(200))  # Salt used in derivation
    iteration_count = Column(Integer)  # For PBKDF2
    
    # Rotation tracking
    previous_key_id = Column(String(100))  # Key this replaced
    next_key_id = Column(String(100))  # Key that replaced this
    rotation_reason = Column(String(200))
    
    # Compliance and audit
    compliance_tags = Column(JSON)  # Compliance requirements
    access_log = Column(JSON)  # Key access history
    
    def __repr__(self):
        return f"<EncryptionKeyMetadata(id={self.key_id}, type={self.key_type}, status={self.status})>"
    
    def is_active(self) -> bool:
        """Check if key is currently active."""
        return (
            self.status == "active" and
            (self.expires_at is None or self.expires_at > datetime.utcnow())
        )
    
    def record_usage(self):
        """Record key usage for tracking."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()


class SecurityConfiguration(Base):
    """
    Store security configuration settings and policies.
    
    Centralizes security configuration management with versioning
    and audit trail for configuration changes.
    """
    __tablename__ = "security_configurations"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration identification
    config_key = Column(String(100), nullable=False)
    config_category = Column(String(50), nullable=False)  # 'auth', 'encryption', 'audit'
    
    # Configuration data
    config_value = Column(JSON, nullable=False)
    config_type = Column(String(50))  # 'boolean', 'integer', 'string', 'object'
    
    # Versioning
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Security properties
    is_sensitive = Column(Boolean, default=False)  # Should value be encrypted?
    requires_restart = Column(Boolean, default=False)  # Requires app restart to apply?
    
    # Change tracking
    changed_by = Column(String(100))
    change_reason = Column(Text)
    previous_value = Column(JSON)
    
    # Validation
    validation_schema = Column(JSON)  # JSON schema for value validation
    
    def __repr__(self):
        return f"<SecurityConfiguration(key={self.config_key}, category={self.config_category})>"
    
    @classmethod
    def get_config(cls, session, key: str, category: str = None) -> Optional['SecurityConfiguration']:
        """Get active configuration by key."""
        query = session.query(cls).filter(
            cls.config_key == key,
            cls.is_active == True
        )
        
        if category:
            query = query.filter(cls.config_category == category)
        
        return query.first()
    
    def create_new_version(self, new_value: Any, changed_by: str, reason: str = None) -> 'SecurityConfiguration':
        """Create new version of configuration."""
        # Deactivate current version
        self.is_active = False
        
        # Create new version
        new_config = SecurityConfiguration(
            config_key=self.config_key,
            config_category=self.config_category,
            config_value=new_value,
            config_type=self.config_type,
            version=self.version + 1,
            is_active=True,
            is_sensitive=self.is_sensitive,
            requires_restart=self.requires_restart,
            changed_by=changed_by,
            change_reason=reason,
            previous_value=self.config_value,
            validation_schema=self.validation_schema
        )
        
        return new_config


# ===== DATABASE INDEXES =====

# Performance indexes for audit logs
Index('idx_audit_logs_created_at', AuditLog.created_at)
Index('idx_audit_logs_event_type', AuditLog.event_type)
Index('idx_audit_logs_user_id', AuditLog.user_id)
Index('idx_audit_logs_resource', AuditLog.resource_type, AuditLog.resource_id)
Index('idx_audit_logs_ip_address', AuditLog.ip_address)

# Performance indexes for authentication attempts
Index('idx_auth_attempts_user_identifier', AuthenticationAttempt.user_identifier)
Index('idx_auth_attempts_created_at', AuthenticationAttempt.created_at)
Index('idx_auth_attempts_ip_address', AuthenticationAttempt.ip_address)
Index('idx_auth_attempts_status', AuthenticationAttempt.status)

# Performance indexes for security events
Index('idx_security_events_created_at', SecurityEvent.created_at)
Index('idx_security_events_severity', SecurityEvent.severity)
Index('idx_security_events_status', SecurityEvent.status)
Index('idx_security_events_event_type', SecurityEvent.event_type)

# Performance indexes for encryption key metadata
Index('idx_encryption_keys_key_id', EncryptionKeyMetadata.key_id)
Index('idx_encryption_keys_status', EncryptionKeyMetadata.status)
Index('idx_encryption_keys_purpose', EncryptionKeyMetadata.key_purpose)

# Performance indexes for security configuration
Index('idx_security_config_key_category', SecurityConfiguration.config_key, SecurityConfiguration.config_category)
Index('idx_security_config_active', SecurityConfiguration.is_active)


# ===== UTILITY FUNCTIONS =====

def create_audit_log(session, event_type: AuditLogType, action: str, **kwargs) -> AuditLog:
    """Create and save audit log entry."""
    audit_data = AuditLogCreate(
        event_type=event_type,
        action=action,
        **kwargs
    )
    
    audit_log = AuditLog.create_log(audit_data)
    session.add(audit_log)
    session.commit()
    
    return audit_log


def record_authentication_attempt(session, user_identifier: str, auth_method: str, 
                                ip_address: str, status: AuthenticationStatus, **kwargs) -> AuthenticationAttempt:
    """Record authentication attempt."""
    attempt_data = AuthenticationAttemptCreate(
        user_identifier=user_identifier,
        auth_method=auth_method,
        ip_address=ip_address,
        status=status,
        **kwargs
    )
    
    attempt = AuthenticationAttempt.create_attempt(attempt_data)
    session.add(attempt)
    session.commit()
    
    return attempt


def create_security_event(session, event_type: str, severity: SecurityEventSeverity,
                         description: str, **kwargs) -> SecurityEvent:
    """Create security event."""
    event_data = SecurityEventCreate(
        event_type=event_type,
        severity=severity,
        description=description,
        **kwargs
    )
    
    event = SecurityEvent.create_event(event_data)
    session.add(event)
    session.commit()
    
    return event


def get_failed_attempts_count(session, user_identifier: str, 
                            time_window_minutes: int = 15) -> int:
    """Get count of failed authentication attempts in time window."""
    from datetime import timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    return session.query(AuthenticationAttempt).filter(
        AuthenticationAttempt.user_identifier == user_identifier,
        AuthenticationAttempt.status == AuthenticationStatus.FAILED.value,
        AuthenticationAttempt.created_at >= cutoff_time
    ).count()


def is_user_locked_out(session, user_identifier: str, 
                      max_attempts: int = 5, lockout_minutes: int = 15) -> bool:
    """Check if user is currently locked out due to failed attempts."""
    failed_count = get_failed_attempts_count(session, user_identifier, lockout_minutes)
    return failed_count >= max_attempts


def clear_failed_attempts(session, user_identifier: str):
    """Clear failed authentication attempts for user (on successful login)."""
    session.query(AuthenticationAttempt).filter(
        AuthenticationAttempt.user_identifier == user_identifier,
        AuthenticationAttempt.status == AuthenticationStatus.FAILED.value
    ).delete()
    session.commit() 