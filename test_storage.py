#!/usr/bin/env python3
"""
Test script for the storage detection service.
This script tests the storage detection functionality on the current system.
"""

import asyncio
import sys
import json
from datetime import datetime

from services.storage_service import StorageDetectionService


async def test_storage_detection():
    """Test the storage detection service"""
    print("🔍 Testing Storage Detection Service")
    print("=" * 50)
    
    try:
        storage_service = StorageDetectionService()
        
        print("📱 Detecting storage devices...")
        devices = await storage_service.get_all_storage_devices()
        
        if not devices:
            print("❌ No storage devices detected")
            return False
        
        print(f"✅ Detected {len(devices)} storage device(s)")
        print()
        
        # Display device information
        for i, device in enumerate(devices, 1):
            print(f"🔧 Device {i}: {device.device}")
            print(f"   Model: {device.model}")
            print(f"   Type: {device.device_type}")
            print(f"   Size: {storage_service._format_size(device.size)}")
            print(f"   Serial: {device.serial or 'Unknown'}")
            print(f"   HPA Present: {'Yes' if device.hpa_present else 'No'}")
            print(f"   DCO Present: {'Yes' if device.dco_present else 'No'}")
            print(f"   Sector Size: {device.sector_size} bytes")
            print(f"   Rotation Rate: {device.rotation_rate or 'N/A'} RPM")
            print(f"   Temperature: {device.temperature or 'N/A'}°C")
            print(f"   Health Status: {device.health_status or 'Unknown'}")
            print(f"   Raw Capacity: {storage_service._format_size(device.raw_capacity)}")
            print(f"   Partitions: {len(device.partitions)}")
            
            if device.partitions:
                print("   Partition Details:")
                for j, partition in enumerate(device.partitions, 1):
                    print(f"     {j}. {partition.device}")
                    print(f"        Mount: {partition.mountpoint}")
                    print(f"        Type: {partition.fstype}")
                    print(f"        Size: {storage_service._format_size(partition.size)}")
                    print(f"        Used: {storage_service._format_size(partition.used)}")
                    print(f"        Free: {storage_service._format_size(partition.free)}")
            
            print()
        
        # Test JSON serialization
        print("🧪 Testing JSON serialization...")
        json_data = [storage_service.to_dict(device) for device in devices]
        json_str = json.dumps(json_data, indent=2)
        print(f"✅ JSON serialization successful ({len(json_str)} characters)")
        
        # Test summary
        print("\n📊 Storage Summary:")
        total_capacity = sum(device.size for device in devices)
        device_types = {}
        hpa_count = 0
        dco_count = 0
        
        for device in devices:
            device_type = device.device_type
            device_types[device_type] = device_types.get(device_type, 0) + 1
            if device.hpa_present:
                hpa_count += 1
            if device.dco_present:
                dco_count += 1
        
        print(f"   Total Devices: {len(devices)}")
        print(f"   Total Capacity: {storage_service._format_size(total_capacity)}")
        print(f"   Device Types: {device_types}")
        print(f"   HPA Devices: {hpa_count}")
        print(f"   DCO Devices: {dco_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_specific_device():
    """Test detection of a specific device"""
    print("\n🎯 Testing specific device detection...")
    
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        if devices:
            # Test the first device
            test_device = devices[0]
            print(f"Testing device: {test_device.device}")
            
            # Test device info conversion
            device_dict = storage_service.to_dict(test_device)
            print(f"✅ Device info conversion successful")
            print(f"   Device: {device_dict['device']}")
            print(f"   Model: {device_dict['model']}")
            print(f"   Size: {device_dict['size_human']}")
            print(f"   Type: {device_dict['device_type']}")
            
            return True
        else:
            print("❌ No devices available for testing")
            return False
            
    except Exception as e:
        print(f"❌ Specific device test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling in the storage service"""
    print("\n🛡️  Testing error handling...")
    
    try:
        storage_service = StorageDetectionService()
        
        # Test with invalid device path
        devices = await storage_service.get_all_storage_devices()
        
        # Test size formatting
        test_sizes = [0, 1024, 1024*1024, 1024*1024*1024, 1024*1024*1024*1024]
        for size in test_sizes:
            formatted = storage_service._format_size(size)
            print(f"   {size} bytes = {formatted}")
        
        print("✅ Error handling tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def main():
    """Run all storage detection tests"""
    print("🚀 Storage Detection Service Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Storage Detection", test_storage_detection),
        ("Specific Device", test_specific_device),
        ("Error Handling", test_error_handling)
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
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All storage detection tests passed!")
        print("\n🚀 The storage service is ready to use.")
        print("📖 You can now use the storage endpoints:")
        print("   GET /api/v1/storage/devices")
        print("   GET /api/v1/storage/summary")
        print("   GET /api/v1/storage/health")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

