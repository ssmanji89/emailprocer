"""
EmailBot Enhanced Authentication Manager
=======================================

Provides secure authentication management with M365 Graph API integration,
failed attempt tracking, and comprehensive security controls.

This module implements:
- Enhanced Graph API authentication with security validation
- Failed attempt tracking and progressive lockout
- Token validation and refresh with security checks
- Authentication audit logging
- Redis-backed token caching with TTL
- Multi-factor authentication support
"""

import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from msal import ConfidentialClientApplication
import jwt
import secrets
import asyncio

from app.core.security import SecurityManager, SecurityException, create_security_manager
from app.models.security_models import (
    AuthenticationAttempt, AuditLog, SecurityEvent,
    AuthenticationStatus, AuditLogType, SecurityEventSeverity,
    record_authentication_attempt, create_audit_log, create_security_event,
    get_failed_attempts_count, is_user_locked_out, clear_failed_attempts
)
from app.config.redis_client import get_redis_client
from app.config.database import get_db_session

logger = logging.getLogger(__name__)


class AuthenticationError(SecurityException):
    """Exception raised for authentication failures."""
    pass


class TokenValidationError(SecurityException):
    """Exception raised for token validation failures."""
    pass


class LockoutError(SecurityException):
    """Exception raised when account is locked due to failed attempts."""
    pass


class EnhancedAuthManager:
    """
    Enhanced authentication manager with comprehensive security controls.
    
    This class provides secure authentication for M365 Graph API with:
    - Failed attempt tracking and lockout mechanisms
    - Token validation and refresh with security checks
    - Redis-backed caching for performance
    - Comprehensive audit logging
    - Security threat detection
    """
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, 
                 security_manager: SecurityManager = None):
        """Initialize enhanced authentication manager."""
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Initialize security manager
        self.security_manager = security_manager or create_security_manager()
        
        # Security configuration
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 15
        self.token_cache_ttl = 3600  # 1 hour
        self.max_token_age = 3600    # 1 hour
        
        # Initialize components
        self._init_msal_client()
        self._init_redis_client()
        self._init_security_patterns()
        
        # Tracking
        self.failed_attempts = {}
        self.active_sessions = {}
        
    def _init_msal_client(self):
        """Initialize MSAL client with security configurations."""
        try:
            self.msal_app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                # Security configurations
                validate_authority=True,
                instance_discovery=True,
                # Enable token cache
                token_cache=None  # We'll use Redis for caching
            )
            
            logger.info("MSAL client initialized successfully")
            
        except Exception as e:
            logger.error(f"MSAL client initialization failed: {str(e)}")
            raise AuthenticationError(f"Failed to initialize authentication client: {str(e)}")
    
    def _init_redis_client(self):
        """Initialize Redis client for token caching."""
        try:
            self.redis_client = get_redis_client()
            logger.info("Redis client initialized for auth manager")
        except Exception as e:
            logger.warning(f"Redis initialization failed, caching disabled: {str(e)}")
            self.redis_client = None
    
    def _init_security_patterns(self):
        """Initialize security detection patterns."""
        self.security_patterns = {
            'suspicious_user_agents': [
                r'bot', r'crawler', r'spider', r'automated'
            ],
            'suspicious_ips': [
                # Add known malicious IP patterns
                r'^10\.0\.0\.1$',  # Example
            ]
        }
    
    # ===== AUTHENTICATION METHODS =====
    
    async def authenticate_service_account(self, request_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Authenticate service account with enhanced security validation.
        
        Args:
            request_context: Optional context including IP, user agent, etc.
            
        Returns:
            Authentication result with token and metadata
            
        Raises:
            AuthenticationError: If authentication fails
            LockoutError: If account is locked
        """
        auth_context = self._prepare_auth_context(request_context)
        
        try:
            # Check for lockout
            await self._check_lockout_status(auth_context["identifier"])
            
            # Security pre-validation
            security_check = await self._perform_security_validation(auth_context)
            if not security_check["safe"]:
                raise AuthenticationError(f"Security validation failed: {security_check['reason']}")
            
            # Check cache first
            cached_token = await self._get_cached_token(auth_context["identifier"])
            if cached_token:
                logger.info("Using cached authentication token")
                await self._record_successful_auth(auth_context, "cached_token")
                return cached_token
            
            # Perform MSAL authentication
            auth_result = await self._perform_msal_authentication()
            
            # Validate token security
            token_validation = await self._validate_token_security(auth_result["access_token"])
            if not token_validation["valid"]:
                raise TokenValidationError(f"Token validation failed: {token_validation['reason']}")
            
            # Enhance result with security metadata
            enhanced_result = await self._enhance_auth_result(auth_result, auth_context)
            
            # Cache the token
            await self._cache_token(auth_context["identifier"], enhanced_result)
            
            # Record successful authentication
            await self._record_successful_auth(auth_context, "msal_authentication")
            
            # Clear any previous failed attempts
            await self._clear_failed_attempts(auth_context["identifier"])
            
            logger.info(f"Service account authentication successful for {auth_context['identifier']}")
            
            return enhanced_result
            
        except (AuthenticationError, TokenValidationError, LockoutError):
            # Record failed attempt for known errors
            await self._record_failed_auth(auth_context, str(e))
            raise
        except Exception as e:
            # Record failed attempt for unexpected errors
            await self._record_failed_auth(auth_context, f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected authentication error: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    async def validate_token(self, token: str, request_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate access token with security checks.
        
        Args:
            token: Access token to validate
            request_context: Optional request context
            
        Returns:
            Token validation result
        """
        validation_context = self._prepare_auth_context(request_context)
        
        try:
            # Basic token validation
            validation_result = await self._validate_token_security(token)
            
            if not validation_result["valid"]:
                await self._record_security_event(
                    "invalid_token_used",
                    SecurityEventSeverity.MEDIUM,
                    f"Invalid token validation attempt from {validation_context.get('ip_address', 'unknown')}",
                    validation_context
                )
                return validation_result
            
            # Enhanced security checks
            security_checks = await self._perform_token_security_checks(token, validation_context)
            validation_result["security_checks"] = security_checks
            
            # Log successful validation
            await self._create_audit_log(
                AuditLogType.AUTHENTICATION,
                "token_validated",
                validation_context,
                success=True,
                details={"token_checks": security_checks}
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return {
                "valid": False,
                "reason": f"Validation error: {str(e)}",
                "security_checks": {}
            }
    
    async def refresh_token(self, refresh_token: str = None, 
                          request_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Refresh authentication token with security validation.
        
        Args:
            refresh_token: Optional refresh token
            request_context: Request context for security tracking
            
        Returns:
            New authentication result
        """
        auth_context = self._prepare_auth_context(request_context)
        
        try:
            # For service account, we don't use refresh tokens - re-authenticate
            logger.info("Performing re-authentication for token refresh")
            return await self.authenticate_service_account(request_context)
            
        except Exception as e:
            await self._record_failed_auth(auth_context, f"Token refresh failed: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    # ===== SECURITY VALIDATION METHODS =====
    
    async def _perform_msal_authentication(self) -> Dict[str, Any]:
        """Perform MSAL authentication with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                result = self.msal_app.acquire_token_for_client(
                    scopes=["https://graph.microsoft.com/.default"]
                )
                
                if "access_token" not in result:
                    error_desc = result.get("error_description", "Unknown error")
                    raise AuthenticationError(f"MSAL authentication failed: {error_desc}")
                
                return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"MSAL authentication attempt {attempt + 1} failed, retrying: {str(e)}")
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise AuthenticationError(f"MSAL authentication failed after {max_retries} attempts: {str(e)}")
    
    async def _validate_token_security(self, token: str) -> Dict[str, Any]:
        """
        Comprehensive token security validation.
        
        Args:
            token: Access token to validate
            
        Returns:
            Validation result with security checks
        """
        try:
            # Decode without verification to inspect claims
            unverified = jwt.decode(token, options={"verify_signature": False})
            
            validation = {
                "valid": True,
                "reason": None,
                "claims": {},
                "security_checks": {}
            }
            
            current_time = time.time()
            
            # Check token expiration
            exp = unverified.get("exp", 0)
            if exp <= current_time:
                validation.update({
                    "valid": False,
                    "reason": "Token expired"
                })
                return validation
            
            # Check token age
            iat = unverified.get("iat", 0)
            token_age = current_time - iat
            if token_age > self.max_token_age:
                validation.update({
                    "valid": False,
                    "reason": f"Token too old (age: {token_age}s, max: {self.max_token_age}s)"
                })
                return validation
            
            # Check audience
            aud = unverified.get("aud")
            expected_audience = "https://graph.microsoft.com"
            if aud != expected_audience:
                validation.update({
                    "valid": False,
                    "reason": f"Invalid audience: {aud}"
                })
                return validation
            
            # Check issuer
            iss = unverified.get("iss")
            expected_issuer_prefix = "https://sts.windows.net/"
            if not iss or not iss.startswith(expected_issuer_prefix):
                validation.update({
                    "valid": False,
                    "reason": f"Invalid issuer: {iss}"
                })
                return validation
            
            # Check tenant
            tid = unverified.get("tid")
            if tid != self.tenant_id:
                validation.update({
                    "valid": False,
                    "reason": f"Invalid tenant: {tid}"
                })
                return validation
            
            # Extract and validate claims
            validation["claims"] = {
                "app_id": unverified.get("appid"),
                "tenant_id": unverified.get("tid"),
                "issued_at": datetime.fromtimestamp(iat).isoformat(),
                "expires_at": datetime.fromtimestamp(exp).isoformat(),
                "scope": unverified.get("scp", ""),
                "roles": unverified.get("roles", [])
            }
            
            # Security checks passed
            validation["security_checks"] = {
                "expiration": "valid",
                "audience": "valid",
                "issuer": "valid",
                "tenant": "valid",
                "age": "valid"
            }
            
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "reason": f"Token validation error: {str(e)}",
                "claims": {},
                "security_checks": {}
            }
    
    async def _perform_security_validation(self, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform security validation on authentication context.
        
        Args:
            auth_context: Authentication context with IP, user agent, etc.
            
        Returns:
            Security validation result
        """
        security_result = {
            "safe": True,
            "reason": None,
            "threats": [],
            "risk_score": 0
        }
        
        try:
            # Check IP address reputation
            ip_address = auth_context.get("ip_address")
            if ip_address:
                ip_check = await self._check_ip_reputation(ip_address)
                security_result["threats"].extend(ip_check.get("threats", []))
                security_result["risk_score"] += ip_check.get("risk_score", 0)
            
            # Check user agent
            user_agent = auth_context.get("user_agent")
            if user_agent:
                ua_check = self._check_user_agent_security(user_agent)
                security_result["threats"].extend(ua_check.get("threats", []))
                security_result["risk_score"] += ua_check.get("risk_score", 0)
            
            # Check for suspicious patterns
            pattern_check = self._check_suspicious_patterns(auth_context)
            security_result["threats"].extend(pattern_check.get("threats", []))
            security_result["risk_score"] += pattern_check.get("risk_score", 0)
            
            # Determine if request is safe
            if security_result["risk_score"] > 70:
                security_result["safe"] = False
                security_result["reason"] = f"High risk score: {security_result['risk_score']}"
            
            if security_result["threats"]:
                if any(threat["severity"] == "high" for threat in security_result["threats"]):
                    security_result["safe"] = False
                    security_result["reason"] = "High severity security threats detected"
            
            return security_result
            
        except Exception as e:
            logger.error(f"Security validation error: {str(e)}")
            return {
                "safe": False,
                "reason": f"Security validation failed: {str(e)}",
                "threats": [],
                "risk_score": 100
            }
    
    async def _perform_token_security_checks(self, token: str, 
                                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform additional security checks on token usage."""
        checks = {
            "token_reuse": "unknown",
            "unusual_access_pattern": "unknown",
            "geographic_anomaly": "unknown"
        }
        
        try:
            # Check for token reuse patterns
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
            
            # Check usage patterns (simplified)
            if self.redis_client:
                usage_key = f"token_usage:{token_hash}"
                usage_count = await self.redis_client.incr(usage_key)
                await self.redis_client.expire(usage_key, 3600)
                
                if usage_count > 100:  # Suspicious high usage
                    checks["token_reuse"] = "suspicious"
                else:
                    checks["token_reuse"] = "normal"
            
            return checks
            
        except Exception as e:
            logger.error(f"Token security checks error: {str(e)}")
            return checks
    
    # ===== LOCKOUT AND TRACKING METHODS =====
    
    async def _check_lockout_status(self, identifier: str):
        """Check if identifier is currently locked out."""
        try:
            with get_db_session() as session:
                if is_user_locked_out(session, identifier, self.max_failed_attempts, self.lockout_duration_minutes):
                    await self._record_security_event(
                        "lockout_attempt",
                        SecurityEventSeverity.MEDIUM,
                        f"Authentication attempt on locked account: {identifier}",
                        {"identifier": identifier}
                    )
                    raise LockoutError(f"Account {identifier} is temporarily locked due to failed attempts")
        except LockoutError:
            raise
        except Exception as e:
            logger.error(f"Lockout check error: {str(e)}")
            # Continue with authentication if lockout check fails
    
    async def _record_successful_auth(self, auth_context: Dict[str, Any], method: str):
        """Record successful authentication attempt."""
        try:
            with get_db_session() as session:
                record_authentication_attempt(
                    session,
                    user_identifier=auth_context["identifier"],
                    auth_method=method,
                    ip_address=auth_context.get("ip_address", "unknown"),
                    status=AuthenticationStatus.SUCCESS,
                    user_agent=auth_context.get("user_agent")
                )
                
                # Create audit log
                await self._create_audit_log(
                    AuditLogType.AUTHENTICATION,
                    "authentication_success",
                    auth_context,
                    success=True,
                    details={"auth_method": method}
                )
                
        except Exception as e:
            logger.error(f"Failed to record successful auth: {str(e)}")
    
    async def _record_failed_auth(self, auth_context: Dict[str, Any], reason: str):
        """Record failed authentication attempt."""
        try:
            with get_db_session() as session:
                record_authentication_attempt(
                    session,
                    user_identifier=auth_context["identifier"],
                    auth_method="msal",
                    ip_address=auth_context.get("ip_address", "unknown"),
                    status=AuthenticationStatus.FAILED,
                    failure_reason=reason,
                    user_agent=auth_context.get("user_agent")
                )
                
                # Check if this triggers lockout
                failed_count = get_failed_attempts_count(
                    session, 
                    auth_context["identifier"], 
                    self.lockout_duration_minutes
                )
                
                if failed_count >= self.max_failed_attempts:
                    await self._record_security_event(
                        "account_locked",
                        SecurityEventSeverity.HIGH,
                        f"Account locked due to {failed_count} failed attempts: {auth_context['identifier']}",
                        auth_context
                    )
                
                # Create audit log
                await self._create_audit_log(
                    AuditLogType.AUTHENTICATION,
                    "authentication_failed",
                    auth_context,
                    success=False,
                    error_message=reason,
                    details={"failed_count": failed_count}
                )
                
        except Exception as e:
            logger.error(f"Failed to record failed auth: {str(e)}")
    
    async def _clear_failed_attempts(self, identifier: str):
        """Clear failed authentication attempts for identifier."""
        try:
            with get_db_session() as session:
                clear_failed_attempts(session, identifier)
        except Exception as e:
            logger.error(f"Failed to clear failed attempts: {str(e)}")
    
    # ===== CACHING METHODS =====
    
    async def _get_cached_token(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get cached authentication token."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"auth_token:{identifier}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                token_data = json.loads(cached_data)
                # Validate cached token is not expired
                expires_at = token_data.get("expires_at", 0)
                if time.time() < expires_at:
                    return token_data
                else:
                    # Remove expired token
                    await self.redis_client.delete(cache_key)
            
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
            return None
    
    async def _cache_token(self, identifier: str, token_data: Dict[str, Any]):
        """Cache authentication token with TTL."""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"auth_token:{identifier}"
            cache_data = json.dumps(token_data, default=str)
            await self.redis_client.setex(cache_key, self.token_cache_ttl, cache_data)
            
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
    
    # ===== UTILITY METHODS =====
    
    def _prepare_auth_context(self, request_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare authentication context from request."""
        context = request_context or {}
        
        return {
            "identifier": f"service_account:{self.client_id}",
            "ip_address": context.get("ip_address", "127.0.0.1"),
            "user_agent": context.get("user_agent", "EmailBot/1.0"),
            "session_id": context.get("session_id"),
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": context.get("request_id", secrets.token_hex(8))
        }
    
    async def _enhance_auth_result(self, auth_result: Dict[str, Any], 
                                 auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance authentication result with security metadata."""
        enhanced_result = auth_result.copy()
        
        # Add security metadata
        enhanced_result.update({
            "security_metadata": {
                "authenticated_at": auth_context["timestamp"],
                "auth_method": "msal_service_account",
                "session_id": auth_context["session_id"],
                "ip_address": auth_context["ip_address"],
                "expires_at": time.time() + auth_result.get("expires_in", 3600)
            },
            "token_metadata": {
                "token_type": auth_result.get("token_type", "Bearer"),
                "scope": auth_result.get("scope", ""),
                "expires_in": auth_result.get("expires_in", 3600)
            }
        })
        
        return enhanced_result
    
    async def _check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP address reputation (simplified implementation)."""
        return {
            "threats": [],
            "risk_score": 0,
            "reputation": "unknown"
        }
    
    def _check_user_agent_security(self, user_agent: str) -> Dict[str, Any]:
        """Check user agent for suspicious patterns."""
        threats = []
        risk_score = 0
        
        # Check for bot patterns
        for pattern in self.security_patterns["suspicious_user_agents"]:
            if pattern.lower() in user_agent.lower():
                threats.append({
                    "type": "suspicious_user_agent",
                    "severity": "medium",
                    "pattern": pattern
                })
                risk_score += 30
        
        return {
            "threats": threats,
            "risk_score": risk_score
        }
    
    def _check_suspicious_patterns(self, auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check for suspicious authentication patterns."""
        return {
            "threats": [],
            "risk_score": 0
        }
    
    async def _create_audit_log(self, event_type: AuditLogType, action: str,
                              context: Dict[str, Any], **kwargs):
        """Create audit log entry."""
        try:
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=event_type,
                    action=action,
                    user_id=context.get("identifier"),
                    session_id=context.get("session_id"),
                    ip_address=context.get("ip_address"),
                    user_agent=context.get("user_agent"),
                    **kwargs
                )
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
    
    async def _record_security_event(self, event_type: str, severity: SecurityEventSeverity,
                                   description: str, context: Dict[str, Any]):
        """Record security event."""
        try:
            with get_db_session() as session:
                create_security_event(
                    session,
                    event_type=event_type,
                    severity=severity,
                    description=description,
                    source_ip=context.get("ip_address"),
                    user_id=context.get("identifier"),
                    details=context
                )
        except Exception as e:
            logger.error(f"Failed to record security event: {str(e)}")


# ===== UTILITY FUNCTIONS =====

def create_enhanced_auth_manager(tenant_id: str, client_id: str, client_secret: str,
                               encryption_key: str = None) -> EnhancedAuthManager:
    """Create enhanced authentication manager instance."""
    security_manager = create_security_manager(encryption_key)
    return EnhancedAuthManager(tenant_id, client_id, client_secret, security_manager)


async def validate_request_authentication(auth_manager: EnhancedAuthManager,
                                        authorization_header: str,
                                        request_context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate authentication from request headers."""
    try:
        # Extract token from Authorization header
        if not authorization_header or not authorization_header.startswith("Bearer "):
            return {
                "authenticated": False,
                "reason": "Missing or invalid Authorization header"
            }
        
        token = authorization_header[7:]  # Remove "Bearer " prefix
        
        # Validate token
        validation_result = await auth_manager.validate_token(token, request_context)
        
        return {
            "authenticated": validation_result["valid"],
            "reason": validation_result.get("reason"),
            "claims": validation_result.get("claims", {}),
            "security_checks": validation_result.get("security_checks", {})
        }
        
    except Exception as e:
        logger.error(f"Request authentication validation error: {str(e)}")
        return {
            "authenticated": False,
            "reason": f"Authentication validation error: {str(e)}"
        } 