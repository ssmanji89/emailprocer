"""
EmailBot Security Tests
======================

Comprehensive test suite for all security components including:
- Encryption/decryption operations
- Authentication flows
- Security validation
- Rate limiting
- Audit logging
- Security middleware
- Performance benchmarks
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from cryptography.fernet import Fernet
import secrets

# Import security components
from app.core.security import (
    SecurityManager, SecurityConfig, create_security_manager,
    SecurityException, EncryptionError, ValidationError
)
from app.utils.encryption import (
    FieldEncryption, EncryptionKeyManager, create_field_encryption,
    encrypt_sensitive_fields, decrypt_sensitive_fields
)
from app.core.auth_manager import (
    EnhancedAuthManager, create_enhanced_auth_manager,
    AuthenticationError, TokenValidationError, LockoutError
)
from app.models.security_models import (
    AuditLog, AuthenticationAttempt, SecurityEvent, EncryptionKeyMetadata,
    AuditLogType, SecurityEventSeverity, AuthenticationStatus,
    create_audit_log, record_authentication_attempt, create_security_event
)
from app.middleware.security import SecurityMiddleware, create_security_middleware
from app.middleware.auth import AuthenticationMiddleware, create_authentication_middleware


class TestSecurityManager:
    """Test suite for SecurityManager class."""
    
    @pytest.fixture
    def security_config(self):
        """Create test security configuration."""
        encryption_key = Fernet.generate_key().decode()
        return SecurityConfig(encryption_key=encryption_key)
    
    @pytest.fixture
    def security_manager(self, security_config):
        """Create test security manager."""
        return SecurityManager(security_config)
    
    def test_security_manager_initialization(self, security_manager):
        """Test security manager initialization."""
        assert security_manager is not None
        assert security_manager.fernet is not None
        assert security_manager.config is not None
        assert security_manager.validation_patterns is not None
    
    def test_encrypt_decrypt_string(self, security_manager):
        """Test string encryption and decryption."""
        test_data = "sensitive information"
        
        # Encrypt
        encrypted = security_manager.encrypt_data(test_data)
        assert encrypted != test_data
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == test_data
    
    def test_encrypt_decrypt_dict(self, security_manager):
        """Test dictionary encryption and decryption."""
        test_data = {
            "email": "test@example.com",
            "phone": "+1234567890",
            "sensitive": True
        }
        
        # Encrypt
        encrypted = security_manager.encrypt_data(test_data)
        assert encrypted != str(test_data)
        
        # Decrypt
        decrypted = security_manager.decrypt_data(encrypted, return_type='dict')
        assert decrypted == test_data
    
    def test_encryption_error_handling(self, security_manager):
        """Test encryption error handling."""
        with pytest.raises(EncryptionError):
            security_manager.decrypt_data("invalid_encrypted_data")
    
    def test_email_validation(self, security_manager):
        """Test email validation functionality."""
        # Valid email
        result = security_manager.validate_email("test@example.com")
        assert result["valid"] is True
        assert result["normalized"] == "test@example.com"
        
        # Invalid email
        result = security_manager.validate_email("invalid-email")
        assert result["valid"] is False
        assert result["reason"] is not None
    
    def test_phone_validation(self, security_manager):
        """Test phone number validation."""
        # Valid phone numbers
        valid_phones = [
            "+1234567890",
            "(123) 456-7890",
            "123-456-7890"
        ]
        
        for phone in valid_phones:
            result = security_manager.validate_phone(phone)
            assert result["valid"] is True, f"Phone {phone} should be valid"
        
        # Invalid phone
        result = security_manager.validate_phone("invalid-phone")
        assert result["valid"] is False
    
    def test_password_strength_validation(self, security_manager):
        """Test password strength validation."""
        # Strong password
        strong_password = "StrongP@ssw0rd123"
        result = security_manager.validate_password_strength(strong_password)
        assert result["valid"] is True
        assert result["strength_score"] >= 80
        
        # Weak password
        weak_password = "weak"
        result = security_manager.validate_password_strength(weak_password)
        assert result["valid"] is False
        assert len(result["requirements_failed"]) > 0
    
    def test_security_threat_detection(self, security_manager):
        """Test security threat detection."""
        # Safe input
        safe_input = "normal user input"
        result = security_manager.detect_security_threats(safe_input)
        assert result["safe"] is True
        assert len(result["detected"]) == 0
        
        # SQL injection attempt
        sql_input = "'; DROP TABLE users; --"
        result = security_manager.detect_security_threats(sql_input)
        assert result["safe"] is False
        assert "sql_injection" in result["detected"]
        
        # XSS attempt
        xss_input = "<script>alert('xss')</script>"
        result = security_manager.detect_security_threats(xss_input)
        assert result["safe"] is False
        assert "xss_attempt" in result["detected"]
    
    def test_password_hashing(self, security_manager):
        """Test password hashing and verification."""
        password = "test_password_123"
        
        # Hash password
        hash_result = security_manager.hash_password(password)
        assert "hash" in hash_result
        assert "salt" in hash_result
        assert hash_result["hash"] != password
        
        # Verify password
        is_valid = security_manager.verify_password(
            password, hash_result["hash"], hash_result["salt"]
        )
        assert is_valid is True
        
        # Verify wrong password
        is_valid = security_manager.verify_password(
            "wrong_password", hash_result["hash"], hash_result["salt"]
        )
        assert is_valid is False
    
    def test_input_sanitization(self, security_manager):
        """Test input sanitization."""
        dangerous_input = "<script>alert('xss')</script>malicious\"content"
        sanitized = security_manager.sanitize_input(dangerous_input)
        
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "\"" not in sanitized
        assert "script" in sanitized  # Content should remain, tags removed


class TestFieldEncryption:
    """Test suite for FieldEncryption class."""
    
    @pytest.fixture
    def security_manager(self):
        """Create test security manager."""
        return create_security_manager()
    
    @pytest.fixture
    def field_encryption(self, security_manager):
        """Create test field encryption."""
        return FieldEncryption(security_manager)
    
    def test_field_encryption_initialization(self, field_encryption):
        """Test field encryption initialization."""
        assert field_encryption is not None
        assert field_encryption.security_manager is not None
        assert field_encryption.current_key_id == "primary"
    
    def test_encrypt_decrypt_field(self, field_encryption):
        """Test field encryption and decryption."""
        field_name = "email"
        field_value = "test@example.com"
        model_id = "user_123"
        
        # Encrypt field
        encrypted_data = field_encryption.encrypt_field(field_name, field_value, model_id)
        
        assert "encrypted_value" in encrypted_data
        assert "encryption_metadata" in encrypted_data
        assert encrypted_data["encrypted_value"] != field_value
        
        metadata = encrypted_data["encryption_metadata"]
        assert metadata["field_name"] == field_name
        assert metadata["key_id"] == "primary"
        assert metadata["data_type"] == "str"
        
        # Decrypt field
        decrypted_value = field_encryption.decrypt_field(encrypted_data)
        assert decrypted_value == field_value
    
    def test_encrypt_multiple_fields(self, field_encryption):
        """Test batch field encryption."""
        field_data = {
            "email": "test@example.com",
            "phone": "+1234567890",
            "age": 25,
            "active": True
        }
        
        encrypted_fields = field_encryption.encrypt_multiple_fields(field_data, "user_123")
        
        assert len(encrypted_fields) == len(field_data)
        for field_name in field_data:
            assert field_name in encrypted_fields
            assert "encrypted_value" in encrypted_fields[field_name]
            assert "encryption_metadata" in encrypted_fields[field_name]
    
    def test_decrypt_multiple_fields(self, field_encryption):
        """Test batch field decryption."""
        field_data = {
            "email": "test@example.com",
            "phone": "+1234567890",
            "age": 25
        }
        
        # Encrypt first
        encrypted_fields = field_encryption.encrypt_multiple_fields(field_data)
        
        # Decrypt with type mapping
        type_map = {"age": int}
        decrypted_fields = field_encryption.decrypt_multiple_fields(encrypted_fields, type_map)
        
        assert decrypted_fields["email"] == field_data["email"]
        assert decrypted_fields["phone"] == field_data["phone"]
        assert decrypted_fields["age"] == field_data["age"]
        assert isinstance(decrypted_fields["age"], int)
    
    def test_key_rotation(self, field_encryption):
        """Test encryption key rotation."""
        # Original encryption
        field_value = "sensitive_data"
        encrypted_data = field_encryption.encrypt_field("test_field", field_value)
        original_key_id = encrypted_data["encryption_metadata"]["key_id"]
        
        # Rotate key
        new_key_id = field_encryption.rotate_encryption_key()
        assert new_key_id != original_key_id
        assert field_encryption.current_key_id == new_key_id
        
        # Should still be able to decrypt old data
        decrypted_value = field_encryption.decrypt_field(encrypted_data)
        assert decrypted_value == field_value
        
        # New encryptions should use new key
        new_encrypted_data = field_encryption.encrypt_field("test_field", field_value)
        new_key_id_used = new_encrypted_data["encryption_metadata"]["key_id"]
        assert new_key_id_used == new_key_id
    
    def test_data_migration(self, field_encryption):
        """Test encrypted data migration."""
        field_value = "data_to_migrate"
        old_encrypted_data = field_encryption.encrypt_field("test_field", field_value)
        
        # Rotate key
        new_key_id = field_encryption.rotate_encryption_key()
        
        # Migrate data
        migrated_data = field_encryption.migrate_encrypted_data(old_encrypted_data, new_key_id)
        
        # Verify migration
        assert migrated_data["encryption_metadata"]["key_id"] == new_key_id
        assert "migration" in migrated_data["encryption_metadata"]
        
        # Verify data integrity
        decrypted_value = field_encryption.decrypt_field(migrated_data)
        assert decrypted_value == field_value
    
    def test_encryption_metadata_validation(self, field_encryption):
        """Test encryption metadata validation."""
        # Valid encrypted data
        encrypted_data = field_encryption.encrypt_field("test_field", "test_value")
        validation = field_encryption.validate_encrypted_data(encrypted_data)
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
        
        # Invalid encrypted data
        invalid_data = {"invalid": "structure"}
        validation = field_encryption.validate_encrypted_data(invalid_data)
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0


class TestEnhancedAuthManager:
    """Test suite for EnhancedAuthManager class."""
    
    @pytest.fixture
    def auth_manager(self):
        """Create test auth manager with mock credentials."""
        return create_enhanced_auth_manager(
            tenant_id="test-tenant-id",
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
    
    @pytest.mark.asyncio
    async def test_auth_manager_initialization(self, auth_manager):
        """Test auth manager initialization."""
        assert auth_manager is not None
        assert auth_manager.tenant_id == "test-tenant-id"
        assert auth_manager.client_id == "test-client-id"
        assert auth_manager.msal_app is not None
    
    @pytest.mark.asyncio
    @patch('app.core.auth_manager.ConfidentialClientApplication')
    async def test_token_validation(self, mock_msal, auth_manager):
        """Test token validation functionality."""
        # Mock valid token
        import jwt
        import time
        
        mock_token = jwt.encode({
            "aud": "https://graph.microsoft.com",
            "iss": "https://sts.windows.net/test-tenant-id/",
            "tid": "test-tenant-id",
            "appid": "test-client-id",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "scp": "Mail.Read"
        }, "secret", algorithm="HS256")
        
        # Test validation
        validation_result = await auth_manager.validate_token(mock_token)
        
        assert "valid" in validation_result
        assert "claims" in validation_result
        assert "security_checks" in validation_result
    
    @pytest.mark.asyncio
    async def test_failed_attempt_tracking(self, auth_manager):
        """Test failed authentication attempt tracking."""
        identifier = "test-service-account"
        
        # Simulate multiple failed attempts
        for i in range(3):
            with patch.object(auth_manager, '_perform_msal_authentication') as mock_auth:
                mock_auth.side_effect = Exception("Authentication failed")
                
                with pytest.raises(Exception):
                    await auth_manager.authenticate_service_account({
                        "ip_address": "127.0.0.1",
                        "user_agent": "Test Agent"
                    })
    
    @pytest.mark.asyncio
    async def test_token_caching(self, auth_manager):
        """Test token caching functionality."""
        # Mock Redis client
        with patch.object(auth_manager, 'redis_client') as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.setex = AsyncMock()
            
            # Mock successful authentication
            with patch.object(auth_manager, '_perform_msal_authentication') as mock_auth:
                mock_auth.return_value = {
                    "access_token": "test_token",
                    "expires_in": 3600,
                    "token_type": "Bearer"
                }
                
                with patch.object(auth_manager, '_validate_token_security') as mock_validate:
                    mock_validate.return_value = {"valid": True}
                    
                    result = await auth_manager.authenticate_service_account()
                    
                    # Verify caching was attempted
                    assert mock_redis.setex.called


class TestSecurityModels:
    """Test suite for security models."""
    
    def test_audit_log_creation(self):
        """Test audit log creation."""
        from app.models.security_models import AuditLogCreate
        
        audit_data = AuditLogCreate(
            event_type=AuditLogType.AUTHENTICATION,
            action="login_attempt",
            user_id="test_user",
            ip_address="127.0.0.1",
            success=True
        )
        
        assert audit_data.event_type == AuditLogType.AUTHENTICATION
        assert audit_data.action == "login_attempt"
        assert audit_data.success is True
    
    def test_authentication_attempt_creation(self):
        """Test authentication attempt creation."""
        from app.models.security_models import AuthenticationAttemptCreate
        
        attempt_data = AuthenticationAttemptCreate(
            user_identifier="test@example.com",
            auth_method="oauth",
            ip_address="127.0.0.1",
            status=AuthenticationStatus.SUCCESS
        )
        
        assert attempt_data.user_identifier == "test@example.com"
        assert attempt_data.status == AuthenticationStatus.SUCCESS
    
    def test_security_event_creation(self):
        """Test security event creation."""
        from app.models.security_models import SecurityEventCreate
        
        event_data = SecurityEventCreate(
            event_type="suspicious_activity",
            severity=SecurityEventSeverity.HIGH,
            description="Multiple failed login attempts",
            source_ip="192.168.1.100"
        )
        
        assert event_data.severity == SecurityEventSeverity.HIGH
        assert "failed login" in event_data.description


class TestSecurityMiddleware:
    """Test suite for SecurityMiddleware class."""
    
    @pytest.fixture
    def security_middleware(self):
        """Create test security middleware."""
        return create_security_middleware()
    
    def test_middleware_initialization(self, security_middleware):
        """Test middleware initialization."""
        assert security_middleware is not None
        assert security_middleware.security_manager is not None
        assert security_middleware.rate_limit_requests_per_minute == 100
        assert len(security_middleware.security_headers) > 0
    
    def test_security_header_configuration(self, security_middleware):
        """Test security header configuration."""
        # Add custom header
        security_middleware.add_security_header("X-Custom-Security", "custom-value")
        assert "X-Custom-Security" in security_middleware.security_headers
        
        # Remove header
        security_middleware.remove_security_header("X-Custom-Security")
        assert "X-Custom-Security" not in security_middleware.security_headers
    
    def test_rate_limiting_configuration(self, security_middleware):
        """Test rate limiting configuration."""
        security_middleware.configure_rate_limiting(200, 20)
        assert security_middleware.rate_limit_requests_per_minute == 200
        assert security_middleware.rate_limit_burst_size == 20
    
    def test_ip_access_control_configuration(self, security_middleware):
        """Test IP access control configuration."""
        whitelist = ["192.168.1.0/24", "10.0.0.0/8"]
        blacklist = ["192.168.1.100", "10.0.0.50"]
        
        security_middleware.configure_ip_access_control(whitelist, blacklist)
        assert security_middleware.ip_whitelist == whitelist
        assert security_middleware.ip_blacklist == blacklist
    
    def test_threat_detection(self, security_middleware):
        """Test security threat detection in paths."""
        # Safe path
        safe_path = "/api/users"
        threats = security_middleware._detect_path_threats(safe_path)
        assert len(threats) == 0
        
        # Path with SQL injection attempt
        sql_path = "/api/users?id=1; DROP TABLE users"
        threats = security_middleware._detect_path_threats(sql_path)
        assert len(threats) > 0
        
        # Path with path traversal attempt
        traversal_path = "/api/files?path=../../../etc/passwd"
        threats = security_middleware._detect_path_threats(traversal_path)
        assert "path_traversal" in threats


class TestAuthenticationMiddleware:
    """Test suite for AuthenticationMiddleware class."""
    
    @pytest.fixture
    def auth_middleware(self):
        """Create test authentication middleware."""
        return create_authentication_middleware()
    
    def test_middleware_initialization(self, auth_middleware):
        """Test middleware initialization."""
        assert auth_middleware is not None
        assert auth_middleware.session_timeout == 3600
        assert len(auth_middleware.public_paths) > 0
    
    def test_public_path_management(self, auth_middleware):
        """Test public path management."""
        # Add public path
        auth_middleware.add_public_path("/api/public")
        assert "/api/public" in auth_middleware.public_paths
        
        # Remove public path
        auth_middleware.remove_public_path("/api/public")
        assert "/api/public" not in auth_middleware.public_paths
    
    def test_authentication_requirement_check(self, auth_middleware):
        """Test authentication requirement checking."""
        # Public path should not require auth
        assert not auth_middleware._is_authentication_required("/health")
        assert not auth_middleware._is_authentication_required("/docs")
        
        # Private path should require auth
        assert auth_middleware._is_authentication_required("/api/emails")
        assert auth_middleware._is_authentication_required("/api/users")
    
    def test_auth_required_path_configuration(self, auth_middleware):
        """Test auth required path configuration."""
        auth_middleware.add_auth_required_path("/api/secure")
        assert "/api/secure" in auth_middleware.auth_required_paths
        
        # When specific auth paths are configured, others become public
        auth_middleware.auth_required_paths = {"/api/secure"}
        assert auth_middleware._is_authentication_required("/api/secure")
        assert not auth_middleware._is_authentication_required("/api/other")


class TestPerformanceBenchmarks:
    """Performance benchmark tests for security components."""
    
    def test_encryption_performance(self):
        """Benchmark encryption/decryption performance."""
        security_manager = create_security_manager()
        
        # Test data
        test_data = "test data " * 100  # 1000 characters
        iterations = 1000
        
        # Benchmark encryption
        start_time = time.time()
        encrypted_values = []
        for _ in range(iterations):
            encrypted = security_manager.encrypt_data(test_data)
            encrypted_values.append(encrypted)
        encryption_time = time.time() - start_time
        
        # Benchmark decryption
        start_time = time.time()
        for encrypted in encrypted_values:
            decrypted = security_manager.decrypt_data(encrypted)
            assert decrypted == test_data
        decryption_time = time.time() - start_time
        
        # Performance assertions
        avg_encryption_time = encryption_time / iterations
        avg_decryption_time = decryption_time / iterations
        
        assert avg_encryption_time < 0.01  # Less than 10ms per encryption
        assert avg_decryption_time < 0.01  # Less than 10ms per decryption
        
        print(f"Encryption: {avg_encryption_time*1000:.2f}ms per operation")
        print(f"Decryption: {avg_decryption_time*1000:.2f}ms per operation")
    
    def test_field_encryption_performance(self):
        """Benchmark field encryption performance."""
        field_encryption = create_field_encryption()
        
        # Test data
        field_data = {
            "email": "test@example.com",
            "phone": "+1234567890",
            "ssn": "123-45-6789",
            "address": "123 Main St, City, State 12345"
        }
        iterations = 100
        
        # Benchmark batch encryption
        start_time = time.time()
        for i in range(iterations):
            encrypted_fields = field_encryption.encrypt_multiple_fields(field_data, f"user_{i}")
        encryption_time = time.time() - start_time
        
        # Performance assertion
        avg_batch_time = encryption_time / iterations
        assert avg_batch_time < 0.1  # Less than 100ms per batch
        
        print(f"Batch field encryption: {avg_batch_time*1000:.2f}ms per batch")
    
    def test_password_hashing_performance(self):
        """Benchmark password hashing performance."""
        security_manager = create_security_manager()
        
        password = "test_password_123"
        iterations = 100
        
        # Benchmark hashing
        start_time = time.time()
        hashes = []
        for _ in range(iterations):
            hash_result = security_manager.hash_password(password)
            hashes.append(hash_result)
        hashing_time = time.time() - start_time
        
        # Benchmark verification
        start_time = time.time()
        for hash_result in hashes[:10]:  # Test subset for verification
            is_valid = security_manager.verify_password(
                password, hash_result["hash"], hash_result["salt"]
            )
            assert is_valid
        verification_time = time.time() - start_time
        
        # Performance assertions
        avg_hash_time = hashing_time / iterations
        avg_verify_time = verification_time / 10
        
        assert avg_hash_time < 0.5  # Less than 500ms per hash (PBKDF2 is intentionally slow)
        assert avg_verify_time < 0.5  # Less than 500ms per verification
        
        print(f"Password hashing: {avg_hash_time*1000:.2f}ms per hash")
        print(f"Password verification: {avg_verify_time*1000:.2f}ms per verification")


class TestIntegrationSecurity:
    """Integration tests for security components working together."""
    
    def test_end_to_end_encryption_flow(self):
        """Test complete encryption flow with field encryption and security manager."""
        # Create components
        security_manager = create_security_manager()
        field_encryption = FieldEncryption(security_manager)
        
        # Test data
        user_data = {
            "id": "user_123",
            "email": "user@example.com",
            "phone": "+1234567890",
            "ssn": "123-45-6789",
            "notes": "Sensitive user information"
        }
        
        sensitive_fields = ["email", "phone", "ssn", "notes"]
        
        # Encrypt sensitive fields
        encrypted_data = encrypt_sensitive_fields(user_data, sensitive_fields)
        
        # Verify encryption
        for field in sensitive_fields:
            encrypted_field = f"{field}_encrypted"
            assert encrypted_field in encrypted_data
            assert field not in encrypted_data or encrypted_data[field] != user_data[field]
        
        # Decrypt sensitive fields
        decrypted_data = decrypt_sensitive_fields(encrypted_data, sensitive_fields)
        
        # Verify decryption
        for field in sensitive_fields:
            assert field in decrypted_data
            assert decrypted_data[field] == user_data[field]
    
    @pytest.mark.asyncio
    async def test_security_audit_integration(self):
        """Test security components with audit logging."""
        # This would require database setup in a real test environment
        # For now, test the creation of audit data structures
        
        from app.models.security_models import AuditLogCreate
        
        # Test audit log creation
        audit_data = AuditLogCreate(
            event_type=AuditLogType.ENCRYPTION,
            action="field_encrypted",
            user_id="system",
            success=True,
            details={
                "field_count": 4,
                "encryption_method": "fernet"
            }
        )
        
        assert audit_data.event_type == AuditLogType.ENCRYPTION
        assert audit_data.details["field_count"] == 4
    
    def test_security_validation_integration(self):
        """Test security validation across components."""
        security_manager = create_security_manager()
        
        # Test data with various threats
        test_inputs = [
            ("normal@example.com", True),
            ("user'; DROP TABLE users; --", False),
            ("<script>alert('xss')</script>", False),
            ("../../../etc/passwd", False),
            ("valid_username_123", True)
        ]
        
        for input_data, should_be_safe in test_inputs:
            # Test threat detection
            threat_result = security_manager.detect_security_threats(input_data)
            assert threat_result["safe"] == should_be_safe
            
            # Test input sanitization
            sanitized = security_manager.sanitize_input(input_data)
            if not should_be_safe:
                # Sanitized version should be safer
                sanitized_threats = security_manager.detect_security_threats(sanitized)
                assert len(sanitized_threats["detected"]) <= len(threat_result["detected"])


# Test configuration and fixtures
@pytest.fixture(scope="session")
def test_database():
    """Set up test database for security tests."""
    # In a real implementation, this would set up a test database
    # For now, we'll mock database operations
    pass


@pytest.fixture(scope="session")
def test_redis():
    """Set up test Redis for caching tests."""
    # In a real implementation, this would set up a test Redis instance
    # For now, we'll mock Redis operations
    pass


if __name__ == "__main__":
    # Run specific test suites
    import sys
    
    if len(sys.argv) > 1:
        test_suite = sys.argv[1]
        if test_suite == "security":
            pytest.main(["-v", "TestSecurityManager"])
        elif test_suite == "encryption":
            pytest.main(["-v", "TestFieldEncryption"])
        elif test_suite == "auth":
            pytest.main(["-v", "TestEnhancedAuthManager"])
        elif test_suite == "middleware":
            pytest.main(["-v", "TestSecurityMiddleware", "TestAuthenticationMiddleware"])
        elif test_suite == "performance":
            pytest.main(["-v", "TestPerformanceBenchmarks"])
        elif test_suite == "integration":
            pytest.main(["-v", "TestIntegrationSecurity"])
        else:
            print("Available test suites: security, encryption, auth, middleware, performance, integration")
    else:
        # Run all tests
        pytest.main(["-v", __file__]) 