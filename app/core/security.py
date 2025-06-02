"""
EmailBot Core Security Module
============================

Provides comprehensive security utilities including encryption, validation,
and security configuration management.

This module implements the foundation security layer for EmailBot with:
- Fernet symmetric encryption for sensitive data
- Security validation functions
- Password strength validation
- Security exception handling
- Security configuration helpers
"""

import base64
import hashlib
import secrets
import re
import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import email_validator
from pydantic import BaseModel, EmailStr, validator

logger = logging.getLogger(__name__)


class SecurityException(Exception):
    """Base exception for security-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class EncryptionError(SecurityException):
    """Exception raised for encryption/decryption errors."""
    pass


class ValidationError(SecurityException):
    """Exception raised for security validation errors."""
    pass


class SecurityConfig(BaseModel):
    """Security configuration model with validation."""
    
    encryption_key: str
    max_password_age_days: int = 90
    min_password_length: int = 12
    require_password_complexity: bool = True
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15
    token_expiry_hours: int = 1
    rate_limit_requests_per_minute: int = 100
    enable_audit_logging: bool = True
    
    @validator('encryption_key')
    def validate_encryption_key(cls, v):
        """Validate encryption key format."""
        try:
            base64.urlsafe_b64decode(v)
            return v
        except Exception:
            raise ValueError('Invalid encryption key format')


class SecurityManager:
    """
    Core security manager providing encryption, validation, and security utilities.
    
    This class implements the main security functionality for EmailBot including:
    - Fernet-based encryption/decryption
    - Security validation functions
    - Password strength validation
    - Security audit logging
    """
    
    def __init__(self, config: SecurityConfig):
        """Initialize security manager with configuration."""
        self.config = config
        self._init_encryption()
        self._init_validation_patterns()
        
    def _init_encryption(self):
        """Initialize encryption utilities."""
        try:
            # Validate and set primary encryption key
            key_bytes = base64.urlsafe_b64decode(self.config.encryption_key.encode())
            self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
            
            # Initialize key rotation support
            self.key_versions = {
                "primary": self.fernet,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Security manager encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {str(e)}")
            raise EncryptionError(f"Encryption initialization failed: {str(e)}")
    
    def _init_validation_patterns(self):
        """Initialize validation regex patterns."""
        self.validation_patterns = {
            'phone': re.compile(r'^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'),
            'password_strong': re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'),
            'sql_injection': re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)', re.IGNORECASE),
            'xss_basic': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
        }
    
    # ===== ENCRYPTION METHODS =====
    
    def encrypt_data(self, data: Union[str, bytes, dict]) -> str:
        """
        Encrypt sensitive data using Fernet encryption.
        
        Args:
            data: Data to encrypt (string, bytes, or dict)
            
        Returns:
            Base64 encoded encrypted string
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Convert data to bytes
            if isinstance(data, dict):
                import json
                data_bytes = json.dumps(data, default=str).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                data_bytes = str(data).encode('utf-8')
            
            # Encrypt data
            encrypted_bytes = self.fernet.encrypt(data_bytes)
            encrypted_string = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
            
            # Log encryption event (without sensitive data)
            if self.config.enable_audit_logging:
                logger.info(f"Data encrypted successfully - size: {len(data_bytes)} bytes")
            
            return encrypted_string
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt_data(self, encrypted_data: str, return_type: str = 'string') -> Union[str, bytes, dict]:
        """
        Decrypt data using Fernet decryption.
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            return_type: Type to return ('string', 'bytes', 'dict')
            
        Returns:
            Decrypted data in specified format
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            # Decode and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # Convert to requested type
            if return_type == 'bytes':
                result = decrypted_bytes
            elif return_type == 'dict':
                import json
                result = json.loads(decrypted_bytes.decode('utf-8'))
            else:  # string
                result = decrypted_bytes.decode('utf-8')
            
            # Log decryption event
            if self.config.enable_audit_logging:
                logger.info(f"Data decrypted successfully - size: {len(decrypted_bytes)} bytes")
            
            return result
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise EncryptionError(f"Failed to decrypt data: {str(e)}")
    
    def generate_encryption_key(self) -> str:
        """Generate a new Fernet-compatible encryption key."""
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode('utf-8')
    
    def derive_key_from_password(self, password: str, salt: bytes = None) -> str:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt bytes (generated if not provided)
            
        Returns:
            Base64 encoded derived key
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode('utf-8')
    
    # ===== VALIDATION METHODS =====
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """
        Validate email address format and deliverability.
        
        Args:
            email: Email address to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            "valid": False,
            "email": email,
            "normalized": None,
            "deliverable": None,
            "reason": None
        }
        
        try:
            # Use email-validator for comprehensive validation
            validated_email = email_validator.validate_email(
                email,
                check_deliverability=True
            )
            
            result.update({
                "valid": True,
                "normalized": validated_email.email,
                "deliverable": True
            })
            
        except email_validator.EmailNotValidError as e:
            result["reason"] = str(e)
            logger.warning(f"Email validation failed for {email}: {str(e)}")
        
        return result
    
    def validate_phone(self, phone: str) -> Dict[str, Any]:
        """
        Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            "valid": False,
            "phone": phone,
            "normalized": None,
            "reason": None
        }
        
        # Remove whitespace and common separators
        clean_phone = re.sub(r'[-.\s()]', '', phone)
        
        if self.validation_patterns['phone'].match(phone):
            result.update({
                "valid": True,
                "normalized": clean_phone
            })
        else:
            result["reason"] = "Invalid phone number format"
        
        return result
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Validate password strength according to security policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Dict with validation results and strength score
        """
        result = {
            "valid": False,
            "strength_score": 0,
            "requirements_met": [],
            "requirements_failed": [],
            "recommendations": []
        }
        
        # Check length requirement
        if len(password) >= self.config.min_password_length:
            result["requirements_met"].append("minimum_length")
            result["strength_score"] += 20
        else:
            result["requirements_failed"].append("minimum_length")
            result["recommendations"].append(f"Use at least {self.config.min_password_length} characters")
        
        if self.config.require_password_complexity:
            # Check complexity requirements
            checks = {
                "lowercase": bool(re.search(r'[a-z]', password)),
                "uppercase": bool(re.search(r'[A-Z]', password)),
                "digits": bool(re.search(r'\d', password)),
                "special_chars": bool(re.search(r'[@$!%*?&]', password))
            }
            
            for check, passed in checks.items():
                if passed:
                    result["requirements_met"].append(check)
                    result["strength_score"] += 20
                else:
                    result["requirements_failed"].append(check)
                    if check == "special_chars":
                        result["recommendations"].append("Include special characters (@$!%*?&)")
                    else:
                        result["recommendations"].append(f"Include {check.replace('_', ' ')}")
        
        # Determine if password is valid
        result["valid"] = len(result["requirements_failed"]) == 0
        
        return result
    
    def detect_security_threats(self, input_data: str) -> Dict[str, Any]:
        """
        Detect potential security threats in input data.
        
        Args:
            input_data: String data to analyze
            
        Returns:
            Dict with threat detection results
        """
        threats = {
            "detected": [],
            "risk_level": "low",
            "safe": True
        }
        
        # Check for SQL injection patterns
        if self.validation_patterns['sql_injection'].search(input_data):
            threats["detected"].append("sql_injection")
            threats["risk_level"] = "high"
            threats["safe"] = False
        
        # Check for XSS patterns
        if self.validation_patterns['xss_basic'].search(input_data):
            threats["detected"].append("xss_attempt")
            threats["risk_level"] = "high"
            threats["safe"] = False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'(eval|exec|system|shell_exec)\s*\(',
            r'<iframe[^>]*>',
            r'javascript:',
            r'data:text/html'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                threats["detected"].append("suspicious_content")
                if threats["risk_level"] == "low":
                    threats["risk_level"] = "medium"
                threats["safe"] = False
        
        return threats
    
    # ===== SECURITY HELPERS =====
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: str = None) -> Dict[str, str]:
        """
        Hash password using PBKDF2 with SHA-256.
        
        Args:
            password: Password to hash
            salt: Salt string (generated if not provided)
            
        Returns:
            Dict with hash and salt
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Create hash using PBKDF2
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return {
            "hash": password_hash.hex(),
            "salt": salt
        }
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash."""
        computed_hash = self.hash_password(password, salt)["hash"]
        return secrets.compare_digest(stored_hash, computed_hash)
    
    def sanitize_input(self, input_data: str) -> str:
        """Sanitize input data to prevent security issues."""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\';\\]', '', input_data)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return sanitized


# Security utility functions
def create_security_manager(encryption_key: str = None) -> SecurityManager:
    """Create configured security manager instance."""
    if encryption_key is None:
        # Generate new key if not provided
        encryption_key = Fernet.generate_key().decode()
    
    config = SecurityConfig(encryption_key=encryption_key)
    return SecurityManager(config)


def validate_api_request(request_data: dict) -> Dict[str, Any]:
    """Validate API request for security threats."""
    security_manager = create_security_manager()
    
    validation_results = {
        "safe": True,
        "threats": [],
        "sanitized_data": {}
    }
    
    for key, value in request_data.items():
        if isinstance(value, str):
            # Check for threats
            threat_check = security_manager.detect_security_threats(value)
            if not threat_check["safe"]:
                validation_results["safe"] = False
                validation_results["threats"].extend(threat_check["detected"])
            
            # Sanitize the value
            validation_results["sanitized_data"][key] = security_manager.sanitize_input(value)
        else:
            validation_results["sanitized_data"][key] = value
    
    return validation_results 