#!/usr/bin/env python3
"""
Test script for the certificate service.
This script tests certificate generation, verification, and management.
"""

import asyncio
import sys
import os
import tempfile
from datetime import datetime, timezone

from services.certificate_service import certificate_service, WipeCertificate
from services.certificate_db_service import CertificateDBService
from database import SessionLocal, engine, Base
from models.certificate import WipeCertificate as WipeCertificateModel


async def test_certificate_generation():
    """Test certificate generation functionality"""
    print("🔐 Testing Certificate Generation")
    print("=" * 50)
    
    try:
        # Test data
        test_data = {
            "user_id": 1,
            "user_name": "John Doe",
            "user_org": "Test Organization",
            "device_serial": "TEST001-2024",
            "device_model": "Test SSD 1TB",
            "device_type": "SSD",
            "wipe_method": "dod_5220_22_m",
            "wipe_status": "completed",
            "target_path": "/test/path/file.txt",
            "size_bytes": 1024 * 1024,  # 1MB
            "passes_completed": 3,
            "total_passes": 3,
            "duration_seconds": 1.5,
            "verification_hash": "abc123def456"
        }
        
        print("📄 Generating certificate...")
        cert_data = await certificate_service.generate_certificate(**test_data)
        
        print(f"✅ Certificate generated successfully!")
        print(f"   Certificate ID: {cert_data.certificate_id}")
        print(f"   Created at: {cert_data.created_at}")
        print(f"   Expires at: {cert_data.expires_at}")
        print(f"   JSON path: {cert_data.json_path}")
        print(f"   PDF path: {cert_data.pdf_path}")
        print(f"   Signature path: {cert_data.signature_path}")
        
        # Check if files exist
        files_exist = all([
            os.path.exists(cert_data.json_path),
            os.path.exists(cert_data.pdf_path),
            os.path.exists(cert_data.signature_path)
        ])
        
        print(f"   Files created: {'✅' if files_exist else '❌'}")
        
        return cert_data
        
    except Exception as e:
        print(f"❌ Certificate generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_certificate_verification():
    """Test certificate verification functionality"""
    print("\n🔍 Testing Certificate Verification")
    print("=" * 50)
    
    try:
        # First generate a certificate
        cert_data = await test_certificate_generation()
        if not cert_data:
            print("❌ Cannot test verification without certificate")
            return False
        
        print(f"\n🔍 Verifying certificate: {cert_data.certificate_id}")
        verification_result = await certificate_service.verify_certificate(cert_data.certificate_id)
        
        print(f"Verification result: {'✅' if verification_result.get('valid') else '❌'}")
        print(f"   Valid: {verification_result.get('valid')}")
        print(f"   Algorithm: {verification_result.get('algorithm')}")
        print(f"   Key size: {verification_result.get('key_size')}")
        
        if verification_result.get('error'):
            print(f"   Error: {verification_result.get('error')}")
        
        return verification_result.get('valid', False)
        
    except Exception as e:
        print(f"❌ Certificate verification failed: {e}")
        return False


async def test_database_integration():
    """Test certificate database integration"""
    print("\n💾 Testing Database Integration")
    print("=" * 50)
    
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        
        # Create database session
        db = SessionLocal()
        cert_db_service = CertificateDBService(db)
        
        # Generate certificate
        cert_data = await test_certificate_generation()
        if not cert_data:
            print("❌ Cannot test database without certificate")
            return False
        
        print(f"\n💾 Saving certificate to database...")
        db_certificate = await cert_db_service.create_certificate(cert_data)
        
        print(f"✅ Certificate saved to database!")
        print(f"   Database ID: {db_certificate.id}")
        print(f"   Certificate ID: {db_certificate.certificate_id}")
        print(f"   User ID: {db_certificate.user_id}")
        print(f"   Device Serial: {db_certificate.device_serial}")
        
        # Test retrieval
        print(f"\n🔍 Retrieving certificate from database...")
        retrieved_cert = await cert_db_service.get_certificate(cert_data.certificate_id)
        
        if retrieved_cert:
            print(f"✅ Certificate retrieved successfully!")
            print(f"   Retrieved ID: {retrieved_cert.id}")
            print(f"   Retrieved Certificate ID: {retrieved_cert.certificate_id}")
        else:
            print(f"❌ Failed to retrieve certificate")
            return False
        
        # Test statistics
        print(f"\n📊 Getting certificate statistics...")
        stats = await cert_db_service.get_certificate_stats()
        print(f"   Total certificates: {stats['total_certificates']}")
        print(f"   Valid certificates: {stats['valid_certificates']}")
        print(f"   Verified certificates: {stats['verified_certificates']}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_certificate_search():
    """Test certificate search functionality"""
    print("\n🔍 Testing Certificate Search")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        cert_db_service = CertificateDBService(db)
        
        # Test search by user
        print("🔍 Searching by user ID...")
        user_certs = await cert_db_service.get_certificates_by_user(user_id=1)
        print(f"   Found {len(user_certs)} certificates for user 1")
        
        # Test search by device
        print("🔍 Searching by device serial...")
        device_certs = await cert_db_service.get_certificates_by_device("TEST001-2024")
        print(f"   Found {len(device_certs)} certificates for device TEST001-2024")
        
        # Test search by organization
        print("🔍 Searching by organization...")
        org_certs = await cert_db_service.get_certificates_by_org("Test Organization")
        print(f"   Found {len(org_certs)} certificates for Test Organization")
        
        # Test general search
        print("🔍 Testing general search...")
        search_results = await cert_db_service.search_certificates(
            query="TEST001",
            skip=0,
            limit=10
        )
        print(f"   Found {len(search_results)} certificates matching 'TEST001'")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Certificate search test failed: {e}")
        return False


async def test_certificate_management():
    """Test certificate management operations"""
    print("\n⚙️  Testing Certificate Management")
    print("=" * 50)
    
    try:
        db = SessionLocal()
        cert_db_service = CertificateDBService(db)
        
        # Get a certificate to test with
        certificates = await cert_db_service.get_all_certificates(limit=1)
        if not certificates:
            print("❌ No certificates found for management testing")
            return False
        
        cert = certificates[0]
        print(f"🔧 Testing management with certificate: {cert.certificate_id}")
        
        # Test verification update
        print("🔧 Testing verification update...")
        updated_cert = await cert_db_service.update_certificate_verification(
            cert.certificate_id, is_verified=True
        )
        if updated_cert and updated_cert.is_verified:
            print("✅ Verification update successful")
        else:
            print("❌ Verification update failed")
        
        # Test invalidation
        print("🔧 Testing certificate invalidation...")
        invalidated_cert = await cert_db_service.invalidate_certificate(cert.certificate_id)
        if invalidated_cert and not invalidated_cert.is_valid:
            print("✅ Certificate invalidation successful")
        else:
            print("❌ Certificate invalidation failed")
        
        # Test soft delete
        print("🔧 Testing certificate deletion...")
        delete_success = await cert_db_service.delete_certificate(cert.certificate_id)
        if delete_success:
            print("✅ Certificate deletion successful")
        else:
            print("❌ Certificate deletion failed")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Certificate management test failed: {e}")
        return False


async def test_file_operations():
    """Test certificate file operations"""
    print("\n📁 Testing File Operations")
    print("=" * 50)
    
    try:
        # Generate a certificate
        cert_data = await test_certificate_generation()
        if not cert_data:
            print("❌ Cannot test file operations without certificate")
            return False
        
        print(f"📁 Testing file operations for certificate: {cert_data.certificate_id}")
        
        # Test file path retrieval
        file_paths = certificate_service.get_certificate_paths(cert_data.certificate_id)
        print(f"   Certificate directory: {file_paths['certificate_dir']}")
        print(f"   JSON file: {file_paths['json_path']}")
        print(f"   PDF file: {file_paths['pdf_path']}")
        print(f"   Signature file: {file_paths['signature_path']}")
        
        # Check if all files exist
        all_files_exist = all(os.path.exists(path) for path in file_paths.values())
        print(f"   All files exist: {'✅' if all_files_exist else '❌'}")
        
        # Test file sizes
        for file_type, path in file_paths.items():
            if file_type != 'certificate_dir' and os.path.exists(path):
                size = os.path.getsize(path)
                print(f"   {file_type}: {size} bytes")
        
        return all_files_exist
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False


async def main():
    """Run all certificate service tests"""
    print("🚀 Certificate Service Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Certificate Generation", test_certificate_generation),
        ("Certificate Verification", test_certificate_verification),
        ("Database Integration", test_database_integration),
        ("Certificate Search", test_certificate_search),
        ("Certificate Management", test_certificate_management),
        ("File Operations", test_file_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 Running {test_name} test...")
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All certificate service tests passed!")
        print("\n🚀 The certificate service is ready to use.")
        print("📖 You can now use the certificate endpoints:")
        print("   GET /api/v1/certificates/")
        print("   GET /api/v1/certificates/{certificate_id}")
        print("   POST /api/v1/certificates/{certificate_id}/verify")
        print("   GET /api/v1/certificates/stats")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
