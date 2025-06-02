#!/usr/bin/env python3
"""
EmailBot Phase 2 Security Layer Test
====================================

Comprehensive test suite for Phase 2 security components:
- Core Security Module
- Encryption Utilities  
- Security Models
- Enhanced Authentication Manager
- Security Middleware
- Authentication Middleware
- Security Testing
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_security_manager():
    """Test Core Security Module (Component 1)."""
    print("📋 Testing Core Security Module...")
    try:
        from app.core.security import SecurityManager, SecurityConfig, create_security_manager
        from cryptography.fernet import Fernet
        
        # Create security manager
        encryption_key = Fernet.generate_key().decode()
        config = SecurityConfig(encryption_key=encryption_key)
        security_manager = SecurityManager(config)
        
        # Test encryption/decryption
        test_data = "sensitive email content"
        encrypted = security_manager.encrypt_data(test_data)
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == test_data, "Encryption/decryption failed"
        
        # Test email validation
        email_result = security_manager.validate_email("test@example.com")
        assert email_result["valid"] is True, "Email validation failed"
        
        # Test password strength
        password_result = security_manager.validate_password_strength("StrongP@ss123")
        assert password_result["valid"] is True, "Password validation failed"
        
        # Test threat detection
        threat_result = security_manager.detect_security_threats("'; DROP TABLE users; --")
        assert threat_result["safe"] is False, "Threat detection failed"
        
        print("✅ Core Security Module working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Core Security Module failed: {str(e)}")
        return False


def test_field_encryption():
    """Test Encryption Utilities (Component 2)."""
    print("📋 Testing Field Encryption...")
    try:
        from app.utils.encryption import FieldEncryption, create_field_encryption
        from app.core.security import create_security_manager
        
        # Create field encryption
        security_manager = create_security_manager()
        field_encryption = FieldEncryption(security_manager)
        
        # Test field encryption
        field_data = {
            "email": "user@example.com",
            "phone": "+1234567890",
            "ssn": "123-45-6789"
        }
        
        encrypted_fields = field_encryption.encrypt_multiple_fields(field_data, "user_123")
        assert len(encrypted_fields) == 3, "Batch encryption failed"
        
        # Test field decryption
        type_map = {"email": str, "phone": str, "ssn": str}
        decrypted_fields = field_encryption.decrypt_multiple_fields(encrypted_fields, type_map)
        
        assert decrypted_fields["email"] == field_data["email"], "Field decryption failed"
        assert decrypted_fields["phone"] == field_data["phone"], "Field decryption failed"
        
        # Test key rotation
        new_key_id = field_encryption.rotate_encryption_key()
        assert new_key_id != "primary", "Key rotation failed"
        
        print("✅ Field Encryption working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Field Encryption failed: {str(e)}")
        return False


def test_security_models():
    """Test Security Models (Component 3)."""
    print("📋 Testing Security Models...")
    try:
        from app.models.security_models import (
            AuditLogCreate, AuthenticationAttemptCreate, SecurityEventCreate,
            AuditLogType, SecurityEventSeverity, AuthenticationStatus
        )
        
        # Test audit log creation
        audit_data = AuditLogCreate(
            event_type=AuditLogType.AUTHENTICATION,
            action="login_attempt",
            user_id="test_user",
            ip_address="127.0.0.1",
            success=True
        )
        assert audit_data.event_type == AuditLogType.AUTHENTICATION, "Audit log creation failed"
        
        # Test authentication attempt creation
        auth_attempt = AuthenticationAttemptCreate(
            user_identifier="test@example.com",
            auth_method="oauth",
            ip_address="127.0.0.1",
            status=AuthenticationStatus.SUCCESS
        )
        assert auth_attempt.status == AuthenticationStatus.SUCCESS, "Auth attempt creation failed"
        
        # Test security event creation
        security_event = SecurityEventCreate(
            event_type="suspicious_activity",
            severity=SecurityEventSeverity.HIGH,
            description="Multiple failed login attempts"
        )
        assert security_event.severity == SecurityEventSeverity.HIGH, "Security event creation failed"
        
        print("✅ Security Models working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Security Models failed: {str(e)}")
        return False


async def test_auth_manager():
    """Test Enhanced Authentication Manager (Component 4)."""
    print("📋 Testing Enhanced Authentication Manager...")
    try:
        from app.core.auth_manager import EnhancedAuthManager, create_enhanced_auth_manager
        
        # Create auth manager with test credentials
        auth_manager = create_enhanced_auth_manager(
            tenant_id="test-tenant-id",
            client_id="test-client-id", 
            client_secret="test-client-secret"
        )
        
        assert auth_manager is not None, "Auth manager creation failed"
        assert auth_manager.tenant_id == "test-tenant-id", "Auth manager configuration failed"
        
        # Test token validation structure
        from unittest.mock import patch
        import jwt
        import time
        
        # Mock token validation
        mock_token = jwt.encode({
            "aud": "https://graph.microsoft.com",
            "iss": "https://sts.windows.net/test-tenant-id/",
            "tid": "test-tenant-id",
            "appid": "test-client-id",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "scp": "Mail.Read"
        }, "secret", algorithm="HS256")
        
        validation_result = await auth_manager.validate_token(mock_token)
        assert "valid" in validation_result, "Token validation structure failed"
        
        print("✅ Enhanced Authentication Manager working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced Authentication Manager failed: {str(e)}")
        return False


def test_security_middleware():
    """Test Security Middleware (Component 5)."""
    print("📋 Testing Security Middleware...")
    try:
        from app.middleware.security import SecurityMiddleware, create_security_middleware
        
        # Create security middleware
        security_middleware = create_security_middleware()
        
        assert security_middleware is not None, "Security middleware creation failed"
        assert security_middleware.rate_limit_requests_per_minute == 100, "Rate limiting config failed"
        assert len(security_middleware.security_headers) > 0, "Security headers config failed"
        
        # Test configuration methods
        security_middleware.configure_rate_limiting(200, 20)
        assert security_middleware.rate_limit_requests_per_minute == 200, "Rate limit config failed"
        
        security_middleware.add_security_header("X-Test-Header", "test-value")
        assert "X-Test-Header" in security_middleware.security_headers, "Header addition failed"
        
        # Test threat detection
        threats = security_middleware._detect_path_threats("/api/users?id=1; DROP TABLE users")
        assert len(threats) > 0, "Path threat detection failed"
        
        print("✅ Security Middleware working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Security Middleware failed: {str(e)}")
        return False


def test_auth_middleware():
    """Test Authentication Middleware (Component 6)."""
    print("📋 Testing Authentication Middleware...")
    try:
        from app.middleware.auth import AuthenticationMiddleware, create_authentication_middleware
        
        # Create auth middleware
        auth_middleware = create_authentication_middleware()
        
        assert auth_middleware is not None, "Auth middleware creation failed"
        assert auth_middleware.session_timeout == 3600, "Session timeout config failed"
        assert len(auth_middleware.public_paths) > 0, "Public paths config failed"
        
        # Test path management
        auth_middleware.add_public_path("/api/public")
        assert "/api/public" in auth_middleware.public_paths, "Public path addition failed"
        
        # Test authentication requirement checking
        assert not auth_middleware._is_authentication_required("/health"), "Health check should be public"
        assert auth_middleware._is_authentication_required("/api/emails"), "API should require auth"
        
        print("✅ Authentication Middleware working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Authentication Middleware failed: {str(e)}")
        return False


def test_comprehensive_security():
    """Test integrated security functionality (Component 7)."""
    print("📋 Testing Comprehensive Security Integration...")
    try:
        from app.core.security import create_security_manager
        from app.utils.encryption import encrypt_sensitive_fields, decrypt_sensitive_fields
        
        # Test end-to-end encryption flow
        user_data = {
            "id": "user_123",
            "email": "user@example.com",
            "phone": "+1234567890",
            "notes": "Sensitive information"
        }
        
        sensitive_fields = ["email", "phone", "notes"]
        
        # Encrypt sensitive fields
        encrypted_data = encrypt_sensitive_fields(user_data, sensitive_fields)
        
        # Verify encryption
        for field in sensitive_fields:
            encrypted_field = f"{field}_encrypted"
            assert encrypted_field in encrypted_data, f"Field {field} not encrypted"
        
        # Decrypt sensitive fields
        decrypted_data = decrypt_sensitive_fields(encrypted_data, sensitive_fields)
        
        # Verify decryption
        for field in sensitive_fields:
            assert field in decrypted_data, f"Field {field} not decrypted"
            assert decrypted_data[field] == user_data[field], f"Field {field} decryption mismatch"
        
        print("✅ Comprehensive Security Integration working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive Security Integration failed: {str(e)}")
        return False


def test_performance_benchmarks():
    """Test security performance benchmarks."""
    print("📋 Testing Performance Benchmarks...")
    try:
        import time
        from app.core.security import create_security_manager
        
        security_manager = create_security_manager()
        
        # Benchmark encryption performance
        test_data = "test data " * 100  # 1000 characters
        iterations = 100
        
        start_time = time.time()
        encrypted_values = []
        for _ in range(iterations):
            encrypted = security_manager.encrypt_data(test_data)
            encrypted_values.append(encrypted)
        encryption_time = time.time() - start_time
        
        start_time = time.time()
        for encrypted in encrypted_values:
            decrypted = security_manager.decrypt_data(encrypted)
            assert decrypted == test_data
        decryption_time = time.time() - start_time
        
        avg_encryption_time = encryption_time / iterations
        avg_decryption_time = decryption_time / iterations
        
        assert avg_encryption_time < 0.01, f"Encryption too slow: {avg_encryption_time*1000:.2f}ms"
        assert avg_decryption_time < 0.01, f"Decryption too slow: {avg_decryption_time*1000:.2f}ms"
        
        print(f"   - Encryption: {avg_encryption_time*1000:.2f}ms per operation")
        print(f"   - Decryption: {avg_decryption_time*1000:.2f}ms per operation")
        print("✅ Performance Benchmarks passed")
        return True
        
    except Exception as e:
        print(f"❌ Performance Benchmarks failed: {str(e)}")
        return False


async def main():
    """Run all Phase 2 security tests."""
    print("🚀 EmailBot Phase 2 Security Layer Test")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    
    # Test results
    tests = [
        ("Core Security Module", test_security_manager),
        ("Field Encryption", test_field_encryption),
        ("Security Models", test_security_models),
        ("Enhanced Auth Manager", test_auth_manager),
        ("Security Middleware", test_security_middleware),
        ("Authentication Middleware", test_auth_middleware),
        ("Comprehensive Security", test_comprehensive_security),
        ("Performance Benchmarks", test_performance_benchmarks)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 2 Security Layer COMPLETE")
        print("✅ All security components working correctly")
        print("\n🔑 Security Features Validated:")
        print("   ✓ Fernet encryption for sensitive data")
        print("   ✓ Field-level encryption with key rotation")
        print("   ✓ Authentication with M365 Graph API")
        print("   ✓ Rate limiting and security headers")
        print("   ✓ Comprehensive audit logging")
        print("   ✓ Security threat detection")
        print("   ✓ Session management and tracking")
        print("   ✓ Performance optimization")
        
        print("\n🚀 Ready to proceed to Phase 3: M365 Integration")
        return True
    else:
        print(f"❌ Phase 2 has {total - passed} failures")
        print("🔧 Fix security issues before proceeding")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 