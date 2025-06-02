"""
EmailBot Security Middleware
===========================

Provides comprehensive security middleware for request validation,
rate limiting, and security header enforcement.

This module implements:
- Request validation and sanitization
- Rate limiting with Redis backing
- Security headers enforcement (HSTS, CSP, etc.)
- IP-based access controls
- Request/response audit logging
- Security policy enforcement
"""

import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

from app.core.security import SecurityManager, SecurityException, create_security_manager
from app.models.security_models import (
    AuditLog, SecurityEvent, AuditLogType, SecurityEventSeverity,
    create_audit_log, create_security_event
)
from app.config.redis_client import get_redis_client
from app.config.database import get_db_session

logger = logging.getLogger(__name__)


class SecurityMiddlewareError(SecurityException):
    """Exception raised for security middleware errors."""
    pass


class RateLimitExceeded(SecurityException):
    """Exception raised when rate limit is exceeded."""
    pass


class SecurityPolicyViolation(SecurityException):
    """Exception raised for security policy violations."""
    pass


class SecurityMiddleware:
    """
    Comprehensive security middleware for request processing.
    
    This middleware provides:
    - Request validation and sanitization
    - Rate limiting with configurable limits
    - Security headers enforcement
    - IP whitelist/blacklist enforcement
    - Request/response audit logging
    - Security threat detection
    """
    
    def __init__(self, security_manager: SecurityManager = None):
        """Initialize security middleware."""
        self.security_manager = security_manager or create_security_manager()
        
        # Initialize Redis for rate limiting
        self._init_redis_client()
        
        # Security configuration
        self.rate_limit_requests_per_minute = 100
        self.rate_limit_burst_size = 10
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_header_size = 8192  # 8KB
        
        # Security headers
        self.security_headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        # IP access control
        self.ip_whitelist = []
        self.ip_blacklist = []
        
        # Security patterns
        self._init_security_patterns()
        
    def _init_redis_client(self):
        """Initialize Redis client for rate limiting."""
        try:
            self.redis_client = get_redis_client()
            logger.info("Redis client initialized for security middleware")
        except Exception as e:
            logger.warning(f"Redis initialization failed, rate limiting disabled: {str(e)}")
            self.redis_client = None
    
    def _init_security_patterns(self):
        """Initialize security detection patterns."""
        self.security_patterns = {
            'sql_injection': [
                r'(\bunion\b.*\bselect\b)',
                r'(\bselect\b.*\bfrom\b)',
                r'(\binsert\b.*\binto\b)',
                r'(\bupdate\b.*\bset\b)',
                r'(\bdelete\b.*\bfrom\b)',
                r'(\bdrop\b.*\btable\b)',
                r'(\balter\b.*\btable\b)',
                r'(\'.*\bor\b.*\')',
                r'(\".*\bor\b.*\")',
                r'(\bor\b.*1\s*=\s*1)',
                r'(\band\b.*1\s*=\s*1)'
            ],
            'xss': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>',
                r'<link[^>]*>',
                r'<meta[^>]*>',
                r'onload\s*=',
                r'onerror\s*=',
                r'onclick\s*='
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'%2e%2e%2f',
                r'%2e%2e\\',
                r'%252e%252e%252f'
            ],
            'command_injection': [
                r';\s*(ls|cat|pwd|whoami|id|uname)',
                r'\|\s*(ls|cat|pwd|whoami|id|uname)',
                r'&&\s*(ls|cat|pwd|whoami|id|uname)',
                r'`.*`',
                r'\$\(.*\)'
            ]
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Main middleware entry point."""
        start_time = time.time()
        request_context = await self._prepare_request_context(request)
        
        try:
            # Pre-request security checks
            await self._perform_pre_request_security_checks(request, request_context)
            
            # Process request
            response = await call_next(request)
            
            # Post-request security enhancements
            response = await self._enhance_response_security(response, request_context)
            
            # Log successful request
            await self._log_request_success(request_context, response, start_time)
            
            return response
            
        except HTTPException as e:
            # Handle HTTP exceptions (rate limits, security violations)
            await self._log_security_violation(request_context, str(e), start_time)
            raise
        except Exception as e:
            # Handle unexpected errors
            await self._log_request_error(request_context, str(e), start_time)
            logger.error(f"Security middleware error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal security error")
    
    # ===== PRE-REQUEST SECURITY CHECKS =====
    
    async def _perform_pre_request_security_checks(self, request: Request, 
                                                 context: Dict[str, Any]):
        """Perform comprehensive pre-request security validation."""
        
        # Check rate limiting
        await self._check_rate_limit(request, context)
        
        # Check IP access control
        await self._check_ip_access_control(request, context)
        
        # Validate request size
        await self._validate_request_size(request, context)
        
        # Validate headers
        await self._validate_request_headers(request, context)
        
        # Check for security threats in request
        await self._check_request_security_threats(request, context)
        
        # Validate request path
        await self._validate_request_path(request, context)
    
    async def _check_rate_limit(self, request: Request, context: Dict[str, Any]):
        """Check rate limiting for the request."""
        if not self.redis_client:
            return  # Rate limiting disabled if Redis unavailable
        
        try:
            client_ip = context["client_ip"]
            current_time = int(time.time())
            window_start = current_time - 60  # 1-minute window
            
            # Rate limiting key
            rate_limit_key = f"rate_limit:{client_ip}"
            
            # Count requests in current window
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # Add current request
            pipe.zadd(rate_limit_key, {str(current_time): current_time})
            
            # Count requests in window
            pipe.zcard(rate_limit_key)
            
            # Set expiry
            pipe.expire(rate_limit_key, 120)  # 2 minutes
            
            results = await pipe.execute()
            request_count = results[2]
            
            # Check rate limit
            if request_count > self.rate_limit_requests_per_minute:
                await self._record_security_event(
                    "rate_limit_exceeded",
                    SecurityEventSeverity.MEDIUM,
                    f"Rate limit exceeded for IP {client_ip}: {request_count} requests/minute",
                    context
                )
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {request_count}/{self.rate_limit_requests_per_minute} requests per minute",
                    headers={"Retry-After": "60"}
                )
            
            # Check burst limit
            recent_window = current_time - 10  # Last 10 seconds
            recent_count = await self.redis_client.zcount(rate_limit_key, recent_window, current_time)
            
            if recent_count > self.rate_limit_burst_size:
                await self._record_security_event(
                    "burst_limit_exceeded",
                    SecurityEventSeverity.HIGH,
                    f"Burst limit exceeded for IP {client_ip}: {recent_count} requests in 10s",
                    context
                )
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Burst limit exceeded: {recent_count}/{self.rate_limit_burst_size} requests in 10 seconds",
                    headers={"Retry-After": "10"}
                )
            
            # Store request count in context for logging
            context["rate_limit_info"] = {
                "requests_per_minute": request_count,
                "burst_requests": recent_count
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # Continue processing if rate limiting fails
    
    async def _check_ip_access_control(self, request: Request, context: Dict[str, Any]):
        """Check IP-based access control."""
        client_ip = context["client_ip"]
        
        try:
            ip_addr = ip_address(client_ip)
            
            # Check blacklist
            for blocked_network in self.ip_blacklist:
                if ip_addr in ip_network(blocked_network):
                    await self._record_security_event(
                        "blocked_ip_access",
                        SecurityEventSeverity.HIGH,
                        f"Access attempt from blacklisted IP: {client_ip}",
                        context
                    )
                    
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: IP address blocked"
                    )
            
            # Check whitelist (if configured)
            if self.ip_whitelist:
                ip_allowed = False
                for allowed_network in self.ip_whitelist:
                    if ip_addr in ip_network(allowed_network):
                        ip_allowed = True
                        break
                
                if not ip_allowed:
                    await self._record_security_event(
                        "non_whitelisted_ip_access",
                        SecurityEventSeverity.MEDIUM,
                        f"Access attempt from non-whitelisted IP: {client_ip}",
                        context
                    )
                    
                    raise HTTPException(
                        status_code=403,
                        detail="Access denied: IP address not whitelisted"
                    )
            
        except ValueError:
            # Invalid IP address
            await self._record_security_event(
                "invalid_ip_address",
                SecurityEventSeverity.MEDIUM,
                f"Invalid IP address format: {client_ip}",
                context
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"IP access control error: {str(e)}")
    
    async def _validate_request_size(self, request: Request, context: Dict[str, Any]):
        """Validate request size limits."""
        try:
            content_length = request.headers.get("content-length")
            if content_length:
                content_length = int(content_length)
                if content_length > self.max_request_size:
                    await self._record_security_event(
                        "request_too_large",
                        SecurityEventSeverity.MEDIUM,
                        f"Request size {content_length} exceeds limit {self.max_request_size}",
                        context
                    )
                    
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request too large: {content_length} bytes (max: {self.max_request_size})"
                    )
        except ValueError:
            # Invalid content-length header
            pass
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Request size validation error: {str(e)}")
    
    async def _validate_request_headers(self, request: Request, context: Dict[str, Any]):
        """Validate request headers for security issues."""
        try:
            # Check total header size
            total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
            
            if total_header_size > self.max_header_size:
                await self._record_security_event(
                    "headers_too_large",
                    SecurityEventSeverity.MEDIUM,
                    f"Request headers size {total_header_size} exceeds limit {self.max_header_size}",
                    context
                )
                
                raise HTTPException(
                    status_code=431,
                    detail=f"Request headers too large: {total_header_size} bytes"
                )
            
            # Check for suspicious header values
            for name, value in request.headers.items():
                # Check for control characters
                if any(ord(c) < 32 and c not in '\t\n\r' for c in value):
                    await self._record_security_event(
                        "suspicious_header_content",
                        SecurityEventSeverity.MEDIUM,
                        f"Header '{name}' contains control characters",
                        context
                    )
                
                # Check for potential injection attempts
                threat_check = self.security_manager.detect_security_threats(value)
                if not threat_check["safe"]:
                    await self._record_security_event(
                        "header_security_threat",
                        SecurityEventSeverity.HIGH,
                        f"Security threat detected in header '{name}': {threat_check['detected']}",
                        context
                    )
                    
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid header content: {name}"
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Header validation error: {str(e)}")
    
    async def _check_request_security_threats(self, request: Request, context: Dict[str, Any]):
        """Check request for security threats."""
        try:
            # Check URL path
            path = str(request.url.path)
            threats = self._detect_path_threats(path)
            
            if threats:
                await self._record_security_event(
                    "path_security_threat",
                    SecurityEventSeverity.HIGH,
                    f"Security threats detected in path: {threats}",
                    context
                )
                
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request path"
                )
            
            # Check query parameters
            query_params = str(request.url.query)
            if query_params:
                threat_check = self.security_manager.detect_security_threats(query_params)
                if not threat_check["safe"]:
                    await self._record_security_event(
                        "query_security_threat",
                        SecurityEventSeverity.HIGH,
                        f"Security threats in query parameters: {threat_check['detected']}",
                        context
                    )
                    
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid query parameters"
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Request threat detection error: {str(e)}")
    
    async def _validate_request_path(self, request: Request, context: Dict[str, Any]):
        """Validate request path for security issues."""
        try:
            path = str(request.url.path)
            
            # Normalize path
            normalized_path = path.replace('\\', '/').replace('//', '/')
            
            # Check for path traversal
            if '..' in normalized_path:
                await self._record_security_event(
                    "path_traversal_attempt",
                    SecurityEventSeverity.HIGH,
                    f"Path traversal attempt detected: {path}",
                    context
                )
                
                raise HTTPException(
                    status_code=400,
                    detail="Invalid path: path traversal not allowed"
                )
            
            # Check for null bytes
            if '\x00' in path:
                await self._record_security_event(
                    "null_byte_injection",
                    SecurityEventSeverity.HIGH,
                    f"Null byte injection attempt: {path}",
                    context
                )
                
                raise HTTPException(
                    status_code=400,
                    detail="Invalid path: null bytes not allowed"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Path validation error: {str(e)}")
    
    # ===== POST-REQUEST SECURITY ENHANCEMENTS =====
    
    async def _enhance_response_security(self, response: Response, 
                                       context: Dict[str, Any]) -> Response:
        """Add security headers and enhancements to response."""
        try:
            # Add security headers
            for header, value in self.security_headers.items():
                response.headers[header] = value
            
            # Add request tracking header
            if "request_id" in context:
                response.headers["X-Request-ID"] = context["request_id"]
            
            # Add rate limit headers
            if "rate_limit_info" in context:
                rate_info = context["rate_limit_info"]
                response.headers["X-RateLimit-Limit"] = str(self.rate_limit_requests_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(
                    max(0, self.rate_limit_requests_per_minute - rate_info["requests_per_minute"])
                )
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except Exception as e:
            logger.error(f"Response security enhancement error: {str(e)}")
            return response
    
    # ===== UTILITY METHODS =====
    
    async def _prepare_request_context(self, request: Request) -> Dict[str, Any]:
        """Prepare request context for security processing."""
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Generate request ID
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
            "headers": dict(request.headers),
            "content_type": request.headers.get("content-type", ""),
            "content_length": request.headers.get("content-length", "0")
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded IP headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP from the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "127.0.0.1"
    
    def _detect_path_threats(self, path: str) -> List[str]:
        """Detect security threats in request path."""
        threats = []
        
        path_lower = path.lower()
        
        # Check each threat pattern
        for threat_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                import re
                if re.search(pattern, path_lower, re.IGNORECASE):
                    threats.append(threat_type)
                    break
        
        return threats
    
    # ===== LOGGING METHODS =====
    
    async def _log_request_success(self, context: Dict[str, Any], response: Response, start_time: float):
        """Log successful request processing."""
        try:
            execution_time = int((time.time() - start_time) * 1000)
            
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=AuditLogType.API_REQUEST,
                    action="request_processed",
                    ip_address=context["client_ip"],
                    user_agent=context["user_agent"],
                    success=True,
                    details={
                        "method": context["method"],
                        "path": context["path"],
                        "status_code": response.status_code,
                        "execution_time_ms": execution_time,
                        "request_id": context["request_id"]
                    },
                    execution_time_ms=execution_time
                )
        except Exception as e:
            logger.error(f"Failed to log request success: {str(e)}")
    
    async def _log_security_violation(self, context: Dict[str, Any], error: str, start_time: float):
        """Log security violation."""
        try:
            execution_time = int((time.time() - start_time) * 1000)
            
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=AuditLogType.SECURITY_EVENT,
                    action="security_violation",
                    ip_address=context["client_ip"],
                    user_agent=context["user_agent"],
                    success=False,
                    error_message=error,
                    details={
                        "method": context["method"],
                        "path": context["path"],
                        "violation_type": "security_policy",
                        "execution_time_ms": execution_time,
                        "request_id": context["request_id"]
                    },
                    execution_time_ms=execution_time
                )
        except Exception as e:
            logger.error(f"Failed to log security violation: {str(e)}")
    
    async def _log_request_error(self, context: Dict[str, Any], error: str, start_time: float):
        """Log request processing error."""
        try:
            execution_time = int((time.time() - start_time) * 1000)
            
            with get_db_session() as session:
                create_audit_log(
                    session,
                    event_type=AuditLogType.ERROR,
                    action="request_error",
                    ip_address=context["client_ip"],
                    user_agent=context["user_agent"],
                    success=False,
                    error_message=error,
                    details={
                        "method": context["method"],
                        "path": context["path"],
                        "error_type": "processing_error",
                        "execution_time_ms": execution_time,
                        "request_id": context["request_id"]
                    },
                    execution_time_ms=execution_time
                )
        except Exception as e:
            logger.error(f"Failed to log request error: {str(e)}")
    
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
                    source_ip=context["client_ip"],
                    details=context
                )
        except Exception as e:
            logger.error(f"Failed to record security event: {str(e)}")
    
    # ===== CONFIGURATION METHODS =====
    
    def configure_rate_limiting(self, requests_per_minute: int = 100, burst_size: int = 10):
        """Configure rate limiting parameters."""
        self.rate_limit_requests_per_minute = requests_per_minute
        self.rate_limit_burst_size = burst_size
        logger.info(f"Rate limiting configured: {requests_per_minute}/min, burst: {burst_size}")
    
    def configure_ip_access_control(self, whitelist: List[str] = None, blacklist: List[str] = None):
        """Configure IP access control lists."""
        self.ip_whitelist = whitelist or []
        self.ip_blacklist = blacklist or []
        logger.info(f"IP access control configured - Whitelist: {len(self.ip_whitelist)}, Blacklist: {len(self.ip_blacklist)}")
    
    def add_security_header(self, name: str, value: str):
        """Add custom security header."""
        self.security_headers[name] = value
        logger.info(f"Security header added: {name}")
    
    def remove_security_header(self, name: str):
        """Remove security header."""
        if name in self.security_headers:
            del self.security_headers[name]
            logger.info(f"Security header removed: {name}")


# ===== UTILITY FUNCTIONS =====

def create_security_middleware(encryption_key: str = None) -> SecurityMiddleware:
    """Create security middleware instance."""
    security_manager = create_security_manager(encryption_key)
    return SecurityMiddleware(security_manager)


def get_request_security_context(request: Request) -> Dict[str, Any]:
    """Extract security context from request."""
    return {
        "ip_address": request.headers.get("x-forwarded-for", "").split(",")[0].strip() or 
                     request.headers.get("x-real-ip", "") or 
                     getattr(request.client, "host", "127.0.0.1"),
        "user_agent": request.headers.get("user-agent", ""),
        "referer": request.headers.get("referer", ""),
        "method": request.method,
        "path": str(request.url.path),
        "query": str(request.url.query)
    } 