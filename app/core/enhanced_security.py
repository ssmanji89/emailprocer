import asyncio
import logging
import hashlib
import secrets
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import jwt

from app.config.settings import settings
from app.services.database_service import database_service
from app.utils.retry import AsyncRetry

logger = logging.getLogger(__name__)


class SecurityException(Exception):
    """Custom security exception."""
    pass


class EncryptionManager:
    """Advanced encryption manager for data protection."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption manager with master key."""
        self.master_key = master_key or settings.master_encryption_key
        if not self.master_key:
            raise SecurityException("Master encryption key is required")
        
        # Initialize Fernet for symmetric encryption
        self.fernet = self._create_fernet_key(self.master_key)
        
        # Initialize RSA key pair for asymmetric encryption
        self.private_key, self.public_key = self._generate_rsa_keypair()
    
    def _create_fernet_key(self, password: str) -> Fernet:
        """Create Fernet encryption key from password."""
        password_bytes = password.encode()
        salt = b'emailbot_salt_2025'  # Should be random in production
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def _generate_rsa_keypair(self):
        """Generate RSA key pair for asymmetric encryption."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def encrypt_sensitive_data(self, data: Union[str, Dict[str, Any]]) -> str:
        """Encrypt sensitive data using Fernet."""
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise SecurityException(f"Encryption failed: {str(e)}")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Union[str, Dict[str, Any]]:
        """Decrypt sensitive data using Fernet."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes).decode()
            
            # Try to parse as JSON, return string if it fails
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                return decrypted_data
                
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise SecurityException(f"Decryption failed: {str(e)}")
    
    def encrypt_with_rsa(self, data: str) -> str:
        """Encrypt data using RSA public key."""
        try:
            encrypted = self.public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.urlsafe_b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error(f"RSA encryption failed: {str(e)}")
            raise SecurityException(f"RSA encryption failed: {str(e)}")
    
    def decrypt_with_rsa(self, encrypted_data: str) -> str:
        """Decrypt data using RSA private key."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"RSA decryption failed: {str(e)}")
            raise SecurityException(f"RSA decryption failed: {str(e)}")


class APIKeyManager:
    """Secure API key management with rotation and validation."""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption = encryption_manager
        self.key_store = {}
        self.key_metadata = {}
    
    def generate_api_key(self, user_id: str, permissions: List[str], expires_days: int = 90) -> Dict[str, Any]:
        """Generate secure API key with metadata."""
        try:
            # Generate cryptographically secure random key
            key_bytes = secrets.token_bytes(32)
            key_string = base64.urlsafe_b64encode(key_bytes).decode()
            
            # Create key ID hash
            key_id = hashlib.sha256(key_string.encode()).hexdigest()[:16]
            
            # Create key metadata
            now = datetime.utcnow()
            metadata = {
                "key_id": key_id,
                "user_id": user_id,
                "permissions": permissions,
                "created_at": now.isoformat(),
                "expires_at": (now + timedelta(days=expires_days)).isoformat(),
                "revoked": False,
                "last_used": None,
                "usage_count": 0,
                "rate_limit": 1000  # requests per hour
            }
            
            # Encrypt and store metadata
            encrypted_metadata = self.encryption.encrypt_sensitive_data(metadata)
            self.key_metadata[key_id] = encrypted_metadata
            
            # Create JWT token with key information
            token_payload = {
                "key_id": key_id,
                "user_id": user_id,
                "permissions": permissions,
                "exp": int((now + timedelta(days=expires_days)).timestamp()),
                "iat": int(now.timestamp())
            }
            
            api_token = jwt.encode(
                token_payload,
                settings.jwt_secret_key,
                algorithm="HS256"
            )
            
            return {
                "api_key": api_token,
                "key_id": key_id,
                "expires_at": metadata["expires_at"],
                "permissions": permissions
            }
            
        except Exception as e:
            logger.error(f"API key generation failed: {str(e)}")
            raise SecurityException(f"API key generation failed: {str(e)}")
    
    async def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate API key and return user information."""
        try:
            # Decode JWT token
            payload = jwt.decode(
                api_key,
                settings.jwt_secret_key,
                algorithms=["HS256"]
            )
            
            key_id = payload["key_id"]
            
            # Get metadata
            if key_id not in self.key_metadata:
                # Try to load from database
                await self._load_key_metadata(key_id)
            
            if key_id not in self.key_metadata:
                raise SecurityException("API key not found")
            
            # Decrypt metadata
            metadata = self.encryption.decrypt_sensitive_data(self.key_metadata[key_id])
            
            # Check if key is revoked
            if metadata["revoked"]:
                raise SecurityException("API key has been revoked")
            
            # Check expiration
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            if datetime.utcnow() > expires_at:
                raise SecurityException("API key has expired")
            
            # Update usage statistics
            metadata["last_used"] = datetime.utcnow().isoformat()
            metadata["usage_count"] += 1
            
            # Re-encrypt and store updated metadata
            self.key_metadata[key_id] = self.encryption.encrypt_sensitive_data(metadata)
            await self._save_key_metadata(key_id, metadata)
            
            return {
                "valid": True,
                "user_id": metadata["user_id"],
                "permissions": metadata["permissions"],
                "key_id": key_id,
                "usage_count": metadata["usage_count"]
            }
            
        except jwt.ExpiredSignatureError:
            raise SecurityException("API key has expired")
        except jwt.InvalidTokenError as e:
            raise SecurityException(f"Invalid API key: {str(e)}")
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            raise SecurityException(f"API key validation failed: {str(e)}")
    
    async def revoke_api_key(self, key_id: str, reason: str = "Manual revocation") -> bool:
        """Revoke an API key."""
        try:
            if key_id not in self.key_metadata:
                await self._load_key_metadata(key_id)
            
            if key_id not in self.key_metadata:
                return False
            
            # Decrypt, update, and re-encrypt metadata
            metadata = self.encryption.decrypt_sensitive_data(self.key_metadata[key_id])
            metadata["revoked"] = True
            metadata["revoked_at"] = datetime.utcnow().isoformat()
            metadata["revocation_reason"] = reason
            
            self.key_metadata[key_id] = self.encryption.encrypt_sensitive_data(metadata)
            await self._save_key_metadata(key_id, metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"API key revocation failed: {str(e)}")
            return False
    
    async def _load_key_metadata(self, key_id: str):
        """Load key metadata from database."""
        try:
            result = await database_service.get_api_key_metadata(key_id)
            if result:
                self.key_metadata[key_id] = result["metadata"]
        except Exception as e:
            logger.error(f"Failed to load key metadata: {str(e)}")
    
    async def _save_key_metadata(self, key_id: str, metadata: Dict[str, Any]):
        """Save key metadata to database."""
        try:
            encrypted_metadata = self.encryption.encrypt_sensitive_data(metadata)
            await database_service.save_api_key_metadata(key_id, encrypted_metadata)
        except Exception as e:
            logger.error(f"Failed to save key metadata: {str(e)}")


class AuditLogger:
    """Comprehensive audit logging for security events."""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption = encryption_manager
        
    async def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        details: Dict[str, Any],
        severity: str = "INFO",
        source_ip: Optional[str] = None
    ):
        """Log security-related events."""
        try:
            audit_entry = {
                "event_id": secrets.token_hex(16),
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "user_id": user_id,
                "source_ip": source_ip,
                "severity": severity,
                "details": details,
                "service": "EmailBot"
            }
            
            # Encrypt sensitive audit data
            encrypted_entry = self.encryption.encrypt_sensitive_data(audit_entry)
            
            # Store in database
            await database_service.store_audit_log(encrypted_entry)
            
            # Log to application logger
            log_level = getattr(logging, severity.upper(), logging.INFO)
            logger.log(log_level, f"AUDIT [{event_type}] User: {user_id}, IP: {source_ip}")
            
        except Exception as e:
            logger.error(f"Audit logging failed: {str(e)}")
    
    async def log_authentication_event(
        self,
        event_type: str,
        user_id: Optional[str],
        success: bool,
        source_ip: Optional[str] = None,
        additional_details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication events."""
        details = {
            "success": success,
            "authentication_method": "API_KEY",
            **(additional_details or {})
        }
        
        severity = "INFO" if success else "WARNING"
        await self.log_security_event(
            event_type="AUTHENTICATION",
            user_id=user_id,
            details=details,
            severity=severity,
            source_ip=source_ip
        )
    
    async def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        source_ip: Optional[str] = None
    ):
        """Log data access events."""
        details = {
            "resource": resource,
            "action": action,
            "success": success
        }
        
        await self.log_security_event(
            event_type="DATA_ACCESS",
            user_id=user_id,
            details=details,
            severity="INFO",
            source_ip=source_ip
        )
    
    async def log_configuration_change(
        self,
        user_id: str,
        component: str,
        change_type: str,
        old_value: Any,
        new_value: Any,
        source_ip: Optional[str] = None
    ):
        """Log configuration changes."""
        details = {
            "component": component,
            "change_type": change_type,
            "old_value": str(old_value)[:100],  # Truncate for security
            "new_value": str(new_value)[:100],
        }
        
        await self.log_security_event(
            event_type="CONFIGURATION_CHANGE",
            user_id=user_id,
            details=details,
            severity="WARNING",
            source_ip=source_ip
        )


class AccessControlManager:
    """Role-based access control manager."""
    
    def __init__(self):
        self.permissions = {
            "admin": [
                "read:all",
                "write:all",
                "delete:all",
                "manage:users",
                "manage:system",
                "view:audit_logs"
            ],
            "operator": [
                "read:emails",
                "write:emails",
                "read:classifications",
                "read:analytics",
                "manage:escalations"
            ],
            "viewer": [
                "read:emails",
                "read:classifications",
                "read:analytics"
            ],
            "api_user": [
                "read:emails",
                "write:classifications",
                "read:analytics"
            ]
        }
    
    def check_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """Check if user has required permission."""
        # Check for exact permission
        if required_permission in user_permissions:
            return True
        
        # Check for wildcard permissions
        for permission in user_permissions:
            if permission.endswith(":all"):
                permission_type = permission.split(":")[0]
                required_type = required_permission.split(":")[0]
                if permission_type == required_type or permission == "write:all" and required_type in ["read", "write"]:
                    return True
        
        return False
    
    def get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a specific role."""
        return self.permissions.get(role, [])
    
    def validate_access(
        self,
        user_permissions: List[str],
        resource: str,
        action: str
    ) -> bool:
        """Validate user access to a resource with specific action."""
        required_permission = f"{action}:{resource}"
        return self.check_permission(user_permissions, required_permission)


class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_email_content(content: str) -> Dict[str, Any]:
        """Validate email content for security threats."""
        threats = []
        
        # Check for potential malicious patterns
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'data:.*base64',
            r'<iframe[^>]*>',
            r'eval\s*\(',
            r'document\.cookie',
            r'window\.location'
        ]
        
        import re
        for pattern in malicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                threats.append(f"Potential malicious pattern: {pattern}")
        
        # Check content length
        if len(content) > 1000000:  # 1MB limit
            threats.append("Content exceeds size limit")
        
        return {
            "is_safe": len(threats) == 0,
            "threats": threats,
            "content_length": len(content)
        }
    
    @staticmethod
    def sanitize_user_input(input_data: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        import html
        
        # HTML escape
        sanitized = html.escape(input_data)
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '`']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)


# Global security services
encryption_manager = EncryptionManager()
api_key_manager = APIKeyManager(encryption_manager)
audit_logger = AuditLogger(encryption_manager)
access_control = AccessControlManager()
security_validator = SecurityValidator() 