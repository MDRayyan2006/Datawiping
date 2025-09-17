#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI setup works correctly.
Run this after installing dependencies to test the basic functionality.
"""

import asyncio
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our models and database setup
from database import Base, engine
from models.user import User
from models.wipe_log import WipeLog, WipeStatus


def test_database_connection():
    """Test database connection and table creation"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database connection successful")
        print("✅ Tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_model_creation():
    """Test that models can be instantiated"""
    try:
        # Test User model
        user = User(
            name="Test User",
            org="Test Organization",
            device_serial="TEST001-2024"
        )
        print("✅ User model instantiation successful")
        
        # Test WipeLog model
        from models.wipe_log import WipeMethod, VerificationStatus
        wipe_log = WipeLog(
            user_id=1,
            wipe_method=WipeMethod.SECURE_DELETE,
            verification_status=VerificationStatus.PENDING
        )
        print("✅ WipeLog model instantiation successful")
        return True
    except Exception as e:
        print(f"❌ Model instantiation failed: {e}")
        return False


def test_imports():
    """Test that all modules can be imported"""
    try:
        from routers import users, wipe_logs
        from services import user_service, wipe_service
        print("✅ All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing FastAPI DataWipe setup...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Connection Test", test_database_connection),
        ("Model Creation Test", test_model_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your FastAPI setup is ready.")
        print("\n🚀 To start the server, run:")
        print("   python main.py")
        print("\n📖 Or visit the API docs at:")
        print("   http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
