#!/usr/bin/env python3
"""
Phase 1 Infrastructure Test Script
Tests the core infrastructure components implemented in Phase 1.
"""

import sys
import traceback

def test_settings_loading():
    """Test settings configuration loading."""
    try:
        from app.config.settings import settings
        print("✅ Settings loaded successfully")
        print(f"   App Name: {settings.app_name}")
        print(f"   App Version: {settings.app_version}")
        print(f"   Target Mailbox: {settings.target_mailbox}")
        print(f"   Database URL: {settings.database_url}")
        return True
    except Exception as e:
        print(f"❌ Settings loading failed: {str(e)}")
        traceback.print_exc()
        return False

def test_database_config():
    """Test database configuration."""
    try:
        from app.config.database import get_engine_config
        config = get_engine_config()
        print("✅ Database configuration loaded")
        print(f"   Engine config keys: {list(config.keys())}")
        return True
    except Exception as e:
        print(f"❌ Database configuration failed: {str(e)}")
        traceback.print_exc()
        return False

def test_redis_config():
    """Test Redis configuration."""
    try:
        from app.config.settings import settings
        redis_config = settings.get_redis_config()
        print("✅ Redis configuration loaded")
        print(f"   Redis URL: {redis_config['url']}")
        print(f"   Max connections: {redis_config['max_connections']}")
        return True
    except Exception as e:
        print(f"❌ Redis configuration failed: {str(e)}")
        traceback.print_exc()
        return False

def test_email_models():
    """Test email models import."""
    try:
        from app.models.email_models import EmailMessage, ClassificationResult, ProcessingResult
        print("✅ Email models imported successfully")
        
        # Test model creation
        from datetime import datetime
        test_email = EmailMessage(
            id="test-123",
            sender_email="test@example.com",
            recipient_email="target@example.com",
            subject="Test Subject",
            body="Test body",
            received_datetime=datetime.utcnow()
        )
        print(f"   Created test email: {test_email.id}")
        return True
    except Exception as e:
        print(f"❌ Email models test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_confidence_thresholds():
    """Test confidence threshold configuration."""
    try:
        from app.config.settings import settings
        thresholds = settings.get_confidence_thresholds()
        print("✅ Confidence thresholds configured")
        print(f"   Auto handle: {thresholds['auto_handle']}")
        print(f"   Suggest response: {thresholds['suggest_response']}")
        print(f"   Human review: {thresholds['human_review']}")
        return True
    except Exception as e:
        print(f"❌ Confidence thresholds test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all Phase 1 tests."""
    print("🚀 EmailBot Phase 1 Infrastructure Test")
    print("=" * 50)
    
    tests = [
        ("Settings Loading", test_settings_loading),
        ("Database Configuration", test_database_config),
        ("Redis Configuration", test_redis_config),
        ("Email Models", test_email_models),
        ("Confidence Thresholds", test_confidence_thresholds),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 1 Core Infrastructure: READY")
        return True
    else:
        print("❌ Phase 1 has failures - check configuration")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 