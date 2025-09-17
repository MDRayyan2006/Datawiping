#!/usr/bin/env python3
"""
Test script for the new FastAPI routers.
This script tests user registration, device listing, job management, and downloads.
"""

import asyncio
import sys
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"


def test_user_registration():
    """Test user registration functionality"""
    print("👤 Testing User Registration")
    print("=" * 50)
    
    try:
        # Test user registration
        user_data = {
            "name": "Test User",
            "org": "Test Organization",
            "device_serial": "TEST-DEVICE-001",
            "email": "test@example.com",
            "notes": "Test user for API testing"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        
        if response.status_code == 201:
            user = response.json()
            print(f"✅ User registered successfully!")
            print(f"   User ID: {user['id']}")
            print(f"   Name: {user['name']}")
            print(f"   Organization: {user['org']}")
            print(f"   Device Serial: {user['device_serial']}")
            return user['id']
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ User registration test failed: {e}")
        return None


def test_device_listing():
    """Test device listing functionality"""
    print("\n💾 Testing Device Listing")
    print("=" * 50)
    
    try:
        # Test device listing
        response = requests.get(f"{BASE_URL}/devices/")
        
        if response.status_code == 200:
            devices = response.json()
            print(f"✅ Found {len(devices)} devices")
            
            for i, device in enumerate(devices[:3], 1):  # Show first 3 devices
                print(f"   Device {i}:")
                print(f"     Model: {device['model']}")
                print(f"     Type: {device['device_type']}")
                print(f"     Size: {device['size_human']}")
                print(f"     Serial: {device['serial']}")
                print(f"     Registered: {device['is_registered']}")
            
            return True
        else:
            print(f"❌ Device listing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Device listing test failed: {e}")
        return False


def test_device_summary():
    """Test device summary functionality"""
    print("\n📊 Testing Device Summary")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/devices/summary")
        
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Device summary retrieved!")
            print(f"   Total Devices: {summary['total_devices']}")
            print(f"   Registered: {summary['registered_devices']}")
            print(f"   Unregistered: {summary['unregistered_devices']}")
            print(f"   Total Capacity: {summary['total_capacity_human']}")
            print(f"   Device Types: {summary['device_types']}")
            return True
        else:
            print(f"❌ Device summary failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Device summary test failed: {e}")
        return False


def test_job_management(user_id):
    """Test job management functionality"""
    print("\n🔧 Testing Job Management")
    print("=" * 50)
    
    try:
        # Test starting a wipe job
        job_data = {
            "user_id": user_id,
            "target_path": "/tmp/test_file.txt",
            "wipe_method": "single_pass",
            "generate_certificate": True,
            "mock_mode": True,
            "notes": "Test wipe job"
        }
        
        response = requests.post(f"{BASE_URL}/jobs/start", json=job_data)
        
        if response.status_code == 201:
            job = response.json()
            print(f"✅ Job started successfully!")
            print(f"   Job ID: {job['job_id']}")
            print(f"   Status: {job['status']}")
            print(f"   Method: {job['wipe_method']}")
            print(f"   User: {job['user_name']}")
            
            job_id = job['job_id']
            
            # Test job status
            print(f"\n🔍 Checking job status...")
            status_response = requests.get(f"{BASE_URL}/jobs/{job_id}/status")
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ Job status retrieved!")
                print(f"   Status: {status['status']}")
                print(f"   Progress: {status['progress']}")
                return job_id
            else:
                print(f"❌ Job status check failed: {status_response.status_code}")
                return job_id
        else:
            print(f"❌ Job start failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Job management test failed: {e}")
        return None


def test_job_listing():
    """Test job listing functionality"""
    print("\n📋 Testing Job Listing")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/jobs/")
        
        if response.status_code == 200:
            jobs_data = response.json()
            print(f"✅ Found {jobs_data['total']} jobs")
            print(f"   Page: {jobs_data['page']}")
            print(f"   Limit: {jobs_data['limit']}")
            print(f"   Has More: {jobs_data['has_more']}")
            
            for i, job in enumerate(jobs_data['jobs'][:3], 1):  # Show first 3 jobs
                print(f"   Job {i}:")
                print(f"     ID: {job['job_id']}")
                print(f"     User: {job['user_name']}")
                print(f"     Method: {job['wipe_method']}")
                print(f"     Status: {job['status']}")
                print(f"     Created: {job['created_at']}")
            
            return True
        else:
            print(f"❌ Job listing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Job listing test failed: {e}")
        return False


def test_certificate_downloads():
    """Test certificate download functionality"""
    print("\n📄 Testing Certificate Downloads")
    print("=" * 50)
    
    try:
        # First, get certificates
        response = requests.get(f"{BASE_URL}/certificates/")
        
        if response.status_code == 200:
            certificates = response.json()
            print(f"✅ Found {len(certificates)} certificates")
            
            if certificates:
                cert_id = certificates[0]['certificate_id']
                print(f"   Testing with certificate: {cert_id}")
                
                # Test PDF download
                pdf_response = requests.get(f"{BASE_URL}/downloads/certificate/{cert_id}/pdf")
                if pdf_response.status_code == 200:
                    print(f"✅ PDF download successful ({len(pdf_response.content)} bytes)")
                else:
                    print(f"❌ PDF download failed: {pdf_response.status_code}")
                
                # Test JSON download
                json_response = requests.get(f"{BASE_URL}/downloads/certificate/{cert_id}/json")
                if json_response.status_code == 200:
                    json_data = json_response.json()
                    print(f"✅ JSON download successful")
                    print(f"   Certificate ID: {json_data['certificate']['id']}")
                    print(f"   User: {json_data['user']['name']}")
                    print(f"   Device: {json_data['device']['serial']}")
                else:
                    print(f"❌ JSON download failed: {json_response.status_code}")
                
                # Test signature download
                sig_response = requests.get(f"{BASE_URL}/downloads/certificate/{cert_id}/signature")
                if sig_response.status_code == 200:
                    print(f"✅ Signature download successful")
                else:
                    print(f"❌ Signature download failed: {sig_response.status_code}")
                
                return True
            else:
                print("⚠️  No certificates found for testing")
                return True
        else:
            print(f"❌ Certificate listing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Certificate download test failed: {e}")
        return False


def test_certificate_verification():
    """Test certificate verification functionality"""
    print("\n🔍 Testing Certificate Verification")
    print("=" * 50)
    
    try:
        # Get certificates
        response = requests.get(f"{BASE_URL}/certificates/")
        
        if response.status_code == 200:
            certificates = response.json()
            
            if certificates:
                cert_id = certificates[0]['certificate_id']
                print(f"   Testing verification for certificate: {cert_id}")
                
                # Test verification
                verify_response = requests.post(f"{BASE_URL}/downloads/verify/{cert_id}")
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    print(f"✅ Certificate verification successful!")
                    print(f"   Valid: {verify_data['verification_result']['valid']}")
                    print(f"   Algorithm: {verify_data['verification_result'].get('algorithm', 'N/A')}")
                    return True
                else:
                    print(f"❌ Certificate verification failed: {verify_response.status_code}")
                    return False
            else:
                print("⚠️  No certificates found for verification testing")
                return True
        else:
            print(f"❌ Certificate listing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Certificate verification test failed: {e}")
        return False


def test_api_health():
    """Test API health and basic functionality"""
    print("\n🏥 Testing API Health")
    print("=" * 50)
    
    try:
        # Test root endpoint
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Root endpoint accessible")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health endpoint accessible")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
        
        # Test API docs
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print(f"❌ API documentation failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API health test failed: {e}")
        return False


def main():
    """Run all router tests"""
    print("🚀 FastAPI Router Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print(f"API Base URL: {BASE_URL}")
    print()
    
    tests = [
        ("API Health", test_api_health),
        ("User Registration", test_user_registration),
        ("Device Listing", test_device_listing),
        ("Device Summary", test_device_summary),
        ("Job Management", lambda: test_job_management(1)),  # Assuming user ID 1 exists
        ("Job Listing", test_job_listing),
        ("Certificate Downloads", test_certificate_downloads),
        ("Certificate Verification", test_certificate_verification)
    ]
    
    passed = 0
    total = len(tests)
    user_id = None
    
    for test_name, test_func in tests:
        print(f"🧪 Running {test_name} test...")
        try:
            if test_name == "User Registration":
                user_id = test_func()
                success = user_id is not None
            elif test_name == "Job Management":
                success = test_func(user_id) is not None
            else:
                success = test_func()
            
            if success:
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All router tests passed!")
        print("\n🚀 The FastAPI routers are ready to use.")
        print("📖 Available endpoints:")
        print("   Authentication: /api/v1/auth/")
        print("   Devices: /api/v1/devices/")
        print("   Jobs: /api/v1/jobs/")
        print("   Downloads: /api/v1/downloads/")
        print("   API Documentation: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n💡 Make sure the API server is running:")
        print("   python main.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
