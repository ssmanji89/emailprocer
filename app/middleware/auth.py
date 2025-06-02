"""
EmailBot Authentication Middleware
=================================

Provides authentication middleware for token validation and
authentication flow management.

This module implements:
- Token validation for API endpoints
- Authentication bypass for health checks
- Security context management
- Session management with caching
- Authentication event logging
- Multi-layer authentication support
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio

from app.core.auth_manager import (
    EnhancedAuthManager, create_enhanced_auth_manager,
    validate_request_authentication, AuthenticationError, LockoutError
)
from app.core.security import SecurityManager, create_security_manager
from app.models.security_models import (
    AuditLog, SecurityEvent, AuditLogType, SecurityEventSeverity,
    create_audit_log, create_security_event
)
from app.config.redis_client import get_redis_client
from app.config.database import get_db_session

logger = logging.getLogger(__name__)


class AuthenticationMiddlewareError(Exception):
    """Exception raised for authentication middleware errors."""
    pass


class UnauthorizedError(Exception):
    """Exception raised for unauthorized access attempts."""
    pass


class AuthenticationMiddleware:
    """
    Comprehensive authentication middleware for API endpoints.
    
    This middleware provides:
    - Token validation for protected endpoints
    - Authentication bypass for public endpoints
    - Security context management
    - Session tracking and management
    - Authentication audit logging
    - Rate limiting for authentication attempts
    """
    
    def __init__(self, auth_manager: EnhancedAuthManager = None,
                 security_manager: SecurityManager = None):
        """Initialize authentication middleware."""
        self.auth_manager = auth_manager
        self.security_manager = security_manager or create_security_manager()
        
        # Initialize Redis for session management
        self._init_redis_client()
        
        # Authentication configuration
        self.session_timeout = 3600  # 1 hour
        self.max_concurrent_sessions = 10
        self.auth_required_paths = set()
        self.public_paths = {
            "/health",
            "/health/",
            "/metrics",
            "/metrics/",
            "/docs",
            "/docs/",
            "/redoc",
            "/redoc/",
            "/openapi.json"
        }
        
        # Authentication schemes
        self.bearer_security = HTTPBearer(auto_error=False)
        
        # Session tracking
        self.active_sessions = {}
        
    def _init_redis_client(self):
        """Initialize Redis client for session management."""
        try:
            self.redis_client = get_redis_client()
            logger.info("Redis client initialized for auth middleware")
        except Exception as e:
            logger.warning(f"Redis initialization failed, session management limited: {str(e)}")
            self.redis_client = None
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Main authentication middleware entry point."""
        start_time = time.time()
        auth_context = await self._prepare_auth_context(request)
        
        try:
            # Check if authentication is required for this path
            if not self._is_authentication_required(request.url.path):
                # Process request without authentication
                response = await call_next(request)
                await self._log_public_access(auth_context, response, start_time)
                return response
            
            # Perform authentication
            auth_result = await self._authenticate_request(request, auth_context)
            
            # Add authentication context to request
            request.state.auth_context = auth_result
            request.state.session_info = auth_result.get("session_info", {})
            
            # Process authenticated request
            response = await call_next(request)
            
            # Update session activity
            await self._update_session_activity(auth_result, auth_context)
            
            # Log successful authenticated request
            await self._log_authenticated_access(auth_context, auth_result, response, start_time)
            
            return response
            
        except HTTPException as e:
            # Handle authentication errors
            await self._log_authentication_failure(auth_context, str(e.detail), start_time)
            raise
        except Exception as e:
            # Handle unexpected errors
            await self._log_authentication_error(auth_context, str(e), start_time)
            logger.error(f"Authentication middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal authentication error"
            )
    
    # ===== AUTHENTICATION METHODS =====
    
    async def _authenticate_request(self, request: Request, 
                                  auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate the incoming request."""
        try:
            # Extract authorization header
            authorization = request.headers.get("authorization")
            if not authorization:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authorization header",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Validate authorization format
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization format",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Initialize auth manager if not provided
            if not self.auth_manager:
                # Get credentials from environment/config
                from app.config.settings import get_settings
                settings = get_settings()
                
                self.auth_manager = create_enhanced_auth_manager(
                    tenant_id=settings.M365_TENANT_ID,
                    client_id=settings.M365_CLIENT_ID,
                    client_secret=settings.M365_CLIENT_SECRET
                )
            
            # Validate token using auth manager
            validation_result = await validate_request_authentication(
                self.auth_manager,
                authorization,
                auth_context
            )
            
            if not validation_result["authenticated"]:
                await self._record_failed_authentication(auth_context, validation_result["reason"])
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authentication failed: {validation_result['reason']}",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Create or update session
            session_info = await self._create_or_update_session(
                validation_result, auth_context
            )
            
            # Prepare authentication result
            auth_result = {
                "authenticated": True,
                "token_claims": validation_result.get("claims", {}),
                "security_checks": validation_result.get("security_checks", {}),
                "session_info": session_info,
                "auth_timestamp": datetime.utcnow().isoformat()
            }
            
            return auth_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Request authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication processing error"
            )
    
    async def _create_or_update_session(self, validation_result: Dict[str, Any],
                                      auth_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user session."""
        try:
            claims = validation_result.get("claims", {})
            app_id = claims.get("app_id", "unknown")
            tenant_id = claims.get("tenant_id", "unknown")
            
            # Create session identifier
            session_id = f"session:{app_id}:{tenant_id}:{auth_context['client_ip']}"
            
            # Session information
            session_info = {
                "session_id": session_id,
                "app_id": app_id,
                "tenant_id": tenant_id,
                "client_ip": auth_context["client_ip"],
                "user_agent": auth_context["user_agent"],
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "request_count": 1,
                "security_score": 100  # Initial security score
            }
            
            if self.redis_client:
                # Check for existing session
                existing_session = await self.redis_client.get(session_id)
                if existing_session:
                    existing_data = json.loads(existing_session)
                    session_info["created_at"] = existing_data.get("created_at", session_info["created_at"])
                    session_info["request_count"] = existing_data.get("request_count", 0) + 1
                    session_info["security_score"] = existing_data.get("security_score", 100)
                
                # Store session in Redis
                session_data = json.dumps(session_info, default=str)
                await self.redis_client.setex(session_id, self.session_timeout, session_data)
                
                # Track concurrent sessions
                await self._track_concurrent_sessions(app_id, session_id)
            
            return session_info
            
        except Exception as e:
            logger.error(f"Session management error: {str(e)}")
            # Return minimal session info on error
            return {
                "session_id": f"fallback:{time.time()}",
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "request_count": 1
            }
    
    async def _track_concurrent_sessions(self, app_id: str, session_id: str):
        """Track concurrent sessions for rate limiting."""
        try:
            if not self.redis_client:
                return
            
            # Sessions tracking key
            sessions_key = f"user_sessions:{app_id}"
            current_time = int(time.time())
            
            # Add current session
            await self.redis_client.zadd(sessions_key, {session_id: current_time})
            
            # Remove expired sessions
            expired_threshold = current_time - self.session_timeout
            await self.redis_client.zremrangebyscore(sessions_key, 0, expired_threshold)
            
            # Check concurrent session limit
            session_count = await self.redis_client.zcard(sessions_key)
            
            if session_count > self.max_concurrent_sessions:
                # Remove oldest sessions
                oldest_sessions = await self.redis_client.zrange(
                    sessions_key, 0, session_count - self.max_concurrent_sessions - 1
                )
                
                for old_session in oldest_sessions:
                    await self.redis_client.delete(old_session)
                    await self.redis_client.zrem(sessions_key, old_session)
                
                await self._record_security_event(
                    "concurrent_session_limit_exceeded",
                    SecurityEventSeverity.MEDIUM,
                    f"Concurrent session limit exceeded for app {app_id}: {session_count} sessions",
                    {"app_id": app_id, "session_count": session_count}
                )
            
            # Set expiry for sessions tracking
            await self.redis_client.expire(sessions_key, self.session_timeout * 2)
            
        except Exception as e:
            logger.error(f"Concurrent session tracking error: {str(e)}")
    
    async def _update_session_activity(self, auth_result: Dict[str, Any],
                                     auth_context: Dict[str, Any]):
        """Update session activity timestamp."""
        try:
            if not self.redis_client:
                return
            
            session_info = auth_result.get("session_info", {})
            session_id = session_info.get("session_id")
            
            if session_id:
                # Update last activity
                session_info["last_activity"] = datetime.utcnow().isoformat()
                
                # Store updated session
                session_data = json.dumps(session_info, default=str)
                await self.redis_client.setex(session_id, self.session_timeout, session_data)
                
        except Exception as e:
            logger.error(f"Session activity update error: {str(e)}")
    
    # ===== PATH MANAGEMENT =====
    
    def _is_authentication_required(self, path: str) -> bool:
        """Check if authentication is required for the given path."""
        # Normalize path
        normalized_path = path.rstrip("/")
        if not normalized_path:
            normalized_path = "/"
        
        # Check public paths
        if normalized_path in self.public_paths or f"{normalized_path}/" in self.public_paths:
            return False
        
        # Check for public path prefixes
        for public_path in self.public_paths:
            if normalized_path.startswith(public_path.rstrip("/")):
                return False
        
        # Check explicitly required paths
        if self.auth_required_paths:
            for required_path in self.auth_required_paths:
                if normalized_path.startswith(required_path.rstrip("/")):
                    return True
            return False  # If specific paths are defined, others are public
        
        # Default: require authentication for all non-public paths
        return True
    
    def add_public_path(self, path: str):
        """Add a path that doesn't require authentication."""
        self.public_paths.add(path)
        logger.info(f"Added public path: {path}")
    
    def remove_public_path(self, path: str):
        """Remove a path from public paths."""
        self.public_paths.discard(path)
        logger.info(f"Removed public path: {path}")
    
    def add_auth_required_path(self, path: str):
        """Add a path that explicitly requires authentication."""
        self.auth_required_paths.add(path)
        logger.info(f"Added auth required path: {path}")
    
    def configure_public_paths(self, paths: List[str]):
        """Configure the list of public paths."""
        self.public_paths = set(paths)
        logger.info(f"Configured {len(paths)} public paths")
    
    # ===== UTILITY METHODS =====
    
    async def _prepare_auth_context(self, request: Request) -> Dict[str, Any]:
        """Prepare authentication context from request."""
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Generate request ID
        import hashlib
        request_id = hashlib.md5(
            f"{client_ip}:{time.time()}:{request.method}:{request.url.path}".encode()
        ).hexdigest()[:16]
        
        return {
            "request_id": request_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query),
            "user_agent": request.headers.get("user-agent", ""),
            "referer": request.headers.get("referer", ""),
            "timestamp": datetime.utcnow().isoformat(),
            "content_type": request.headers.get("content-type", ""),
            "authorization_present": bool(request.headers.get("authorization"))
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "127.0.0.1"
    
    # ===== LOGGING METHODS =====
    
    async def _log_public_access(self, auth_context: Dict[str, Any], 
                               response: Response, start_time: float):
        """Log public endpoint access."""
        try:
            execution_time = int((time.time() - start_time) * 1000)
            
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=AuditLogType.API_REQUEST,
                    action="public_access",
                    ip_address=auth_context["client_ip"],
                    user_agent=auth_context["user_agent"],
                    success=True,
                    details={
                        "method": auth_context["method"],
                        "path": auth_context["path"],
                        "status_code": response.status_code,
                        "execution_time_ms": execution_time,
                        "request_id": auth_context["request_id"],
                        "access_type": "public"
                    },
                    execution_time_ms=execution_time
                )
        except Exception as e:
            logger.error(f"Failed to log public access: {str(e)}")
    
    async def _log_authenticated_access(self, auth_context: Dict[str, Any],
                                      auth_result: Dict[str, Any],
                                      response: Response, start_time: float):
        """Log authenticated endpoint access."""
        try:
            execution_time = int((time.time() - start_time) * 1000)
            
            claims = auth_result.get("token_claims", {})
            session_info = auth_result.get("session_info", {})
            
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=AuditLogType.API_REQUEST,
                    action="authenticated_access",
                    user_id=claims.get("app_id"),
                    session_id=session_info.get("session_id"),
                    ip_address=auth_context["client_ip"],
                    user_agent=auth_context["user_agent"],
                    success=True,
                    details={
                        "method": auth_context["method"],
                        "path": auth_context["path"],
                        "status_code": response.status_code,
                        "execution_time_ms": execution_time,
                        "request_id": auth_context["request_id"],
                        "access_type": "authenticated",
                        "tenant_id": claims.get("tenant_id"),
                        "session_request_count": session_info.get("request_count", 1)
                    },
                    execution_time_ms=execution_time
                )
        except Exception as e:
            logger.error(f"Failed to log authenticated access: {str(e)}")
    
    async def _log_authentication_failure(self, auth_context: Dict[str, Any],
                                        error: str, start_time: float):
        """Log authentication failure."""
        try:
            execution_time = int((time.time() - start_time) * 1000)
            
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=AuditLogType.AUTHENTICATION,
                    action="authentication_failed",
                    ip_address=auth_context["client_ip"],
                    user_agent=auth_context["user_agent"],
                    success=False,
                    error_message=error,
                    details={
                        "method": auth_context["method"],
                        "path": auth_context["path"],
                        "execution_time_ms": execution_time,
                        "request_id": auth_context["request_id"],
                        "failure_reason": error
                    },
                    execution_time_ms=execution_time
                )
        except Exception as e:
            logger.error(f"Failed to log authentication failure: {str(e)}")
    
    async def _log_authentication_error(self, auth_context: Dict[str, Any],
                                      error: str, start_time: float):
        """Log authentication processing error."""
        try:
            execution_time = int((time.time() - start_time) * 1000)
            
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=AuditLogType.ERROR,
                    action="authentication_error",
                    ip_address=auth_context["client_ip"],
                    user_agent=auth_context["user_agent"],
                    success=False,
                    error_message=error,
                    details={
                        "method": auth_context["method"],
                        "path": auth_context["path"],
                        "execution_time_ms": execution_time,
                        "request_id": auth_context["request_id"],
                        "error_type": "processing_error"
                    },
                    execution_time_ms=execution_time
                )
        except Exception as e:
            logger.error(f"Failed to log authentication error: {str(e)}")
    
    async def _record_failed_authentication(self, auth_context: Dict[str, Any], reason: str):
        """Record failed authentication attempt."""
        try:
            await self._record_security_event(
                "authentication_failed",
                SecurityEventSeverity.MEDIUM,
                f"Authentication failed from {auth_context['client_ip']}: {reason}",
                auth_context
            )
        except Exception as e:
            logger.error(f"Failed to record failed authentication: {str(e)}")
    
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
                    source_ip=context.get("client_ip"),
                    details=context
                )
        except Exception as e:
            logger.error(f"Failed to record security event: {str(e)}")
    
    # ===== SESSION MANAGEMENT =====
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information by session ID."""
        try:
            if not self.redis_client:
                return None
            
            session_data = await self.redis_client.get(session_id)
            if session_data:
                return json.loads(session_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Get session info error: {str(e)}")
            return None
    
    async def invalidate_session(self, session_id: str):
        """Invalidate a session."""
        try:
            if self.redis_client:
                await self.redis_client.delete(session_id)
                logger.info(f"Session invalidated: {session_id}")
        except Exception as e:
            logger.error(f"Session invalidation error: {str(e)}")
    
    async def get_active_sessions(self, app_id: str) -> List[Dict[str, Any]]:
        """Get active sessions for an app."""
        try:
            if not self.redis_client:
                return []
            
            sessions_key = f"user_sessions:{app_id}"
            session_ids = await self.redis_client.zrange(sessions_key, 0, -1)
            
            sessions = []
            for session_id in session_ids:
                session_info = await self.get_session_info(session_id)
                if session_info:
                    sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Get active sessions error: {str(e)}")
            return []


# ===== UTILITY FUNCTIONS =====

def create_authentication_middleware(tenant_id: str = None, client_id: str = None,
                                   client_secret: str = None) -> AuthenticationMiddleware:
    """Create authentication middleware instance."""
    auth_manager = None
    
    if tenant_id and client_id and client_secret:
        auth_manager = create_enhanced_auth_manager(tenant_id, client_id, client_secret)
    
    return AuthenticationMiddleware(auth_manager)


def get_current_user_info(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user information from request context."""
    if hasattr(request.state, "auth_context"):
        return request.state.auth_context.get("token_claims", {})
    return None


def get_current_session_info(request: Request) -> Optional[Dict[str, Any]]:
    """Get current session information from request context."""
    if hasattr(request.state, "session_info"):
        return request.state.session_info
    return None


def require_authentication(func):
    """Decorator to require authentication for a function."""
    async def wrapper(request: Request, *args, **kwargs):
        if not hasattr(request.state, "auth_context"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return await func(request, *args, **kwargs)
    
    return wrapper


# Authentication dependency for FastAPI
async def get_authenticated_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency to get authenticated user information."""
    if not hasattr(request.state, "auth_context"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    auth_context = request.state.auth_context
    if not auth_context.get("authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return auth_context.get("token_claims", {}) 