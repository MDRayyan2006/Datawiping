#!/usr/bin/env python3
"""
Test script for the wipe service.
This script tests the wipe functionality with various methods and mock mode.
"""

import asyncio
import sys
import tempfile
import os
from datetime import datetime

from services.wipe import WipeService, WipeMethod, WipeResult


async def test_wipe_methods():
    """Test all wipe methods in mock mode"""
    print("🧪 Testing Wipe Methods")
    print("=" * 50)
    
    wipe_service = WipeService(mock_mode=True)
    
    methods = [
        WipeMethod.DOD_5220_22_M,
        WipeMethod.NIST_800_88,
        WipeMethod.SINGLE_PASS,
        WipeMethod.GUTMANN,
        WipeMethod.RANDOM,
        WipeMethod.ZERO
    ]
    
    for method in methods:
        print(f"\n🔧 Testing {method.value}...")
        
        # Test file wiping
        result = await wipe_service.wipe_file("/tmp/test_file.txt", method)
        print(f"   File wipe: {'✅' if result.success else '❌'}")
        print(f"   Passes: {result.passes_completed}/{result.total_passes}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        
        # Test folder wiping
        result = await wipe_service.wipe_folder("/tmp/test_folder", method)
        print(f"   Folder wipe: {'✅' if result.success else '❌'}")
        print(f"   Passes: {result.passes_completed}/{result.total_passes}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        
        # Test drive wiping
        result = await wipe_service.wipe_drive("/dev/test", method)
        print(f"   Drive wipe: {'✅' if result.success else '❌'}")
        print(f"   Passes: {result.passes_completed}/{result.total_passes}")
        print(f"   Duration: {result.duration_seconds:.2f}s")


async def test_real_file_wipe():
    """Test real file wiping with a temporary file"""
    print("\n🗂️  Testing Real File Wipe")
    print("=" * 50)
    
    wipe_service = WipeService(mock_mode=False)
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".test") as temp_file:
            temp_file.write(b"Test data for secure wiping")
            temp_path = temp_file.name
        
        print(f"Created test file: {temp_path}")
        print(f"File size: {os.path.getsize(temp_path)} bytes")
        
        # Test single pass wipe
        print("\n🔧 Testing single pass wipe...")
        result = await wipe_service.wipe_file(temp_path, WipeMethod.SINGLE_PASS)
        
        print(f"Wipe result: {'✅' if result.success else '❌'}")
        print(f"Method: {result.method.value}")
        print(f"Passes: {result.passes_completed}/{result.total_passes}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"File exists after wipe: {os.path.exists(temp_path)}")
        
        if not result.success:
            print(f"Error: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Real file wipe test failed: {e}")
        return False


async def test_folder_wipe():
    """Test real folder wiping with temporary files"""
    print("\n📁 Testing Real Folder Wipe")
    print("=" * 50)
    
    wipe_service = WipeService(mock_mode=False)
    
    try:
        # Create a temporary directory with files
        temp_dir = tempfile.mkdtemp(prefix="wipe_test_")
        print(f"Created test directory: {temp_dir}")
        
        # Create some test files
        test_files = [
            "file1.txt",
            "file2.txt",
            "subdir/file3.txt",
            "subdir/file4.txt"
        ]
        
        for file_path in test_files:
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(f"Test data for {file_path}")
        
        print(f"Created {len(test_files)} test files")
        print(f"Directory exists: {os.path.exists(temp_dir)}")
        
        # Test folder wipe
        print("\n🔧 Testing folder wipe...")
        result = await wipe_service.wipe_folder(temp_dir, WipeMethod.SINGLE_PASS)
        
        print(f"Wipe result: {'✅' if result.success else '❌'}")
        print(f"Method: {result.method.value}")
        print(f"Passes: {result.passes_completed}/{result.total_passes}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"Directory exists after wipe: {os.path.exists(temp_dir)}")
        
        if not result.success:
            print(f"Error: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Real folder wipe test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling scenarios"""
    print("\n🛡️  Testing Error Handling")
    print("=" * 50)
    
    wipe_service = WipeService(mock_mode=False)
    
    # Test non-existent file
    print("Testing non-existent file...")
    result = await wipe_service.wipe_file("/nonexistent/file.txt", WipeMethod.SINGLE_PASS)
    print(f"Non-existent file: {'✅' if not result.success else '❌'}")
    print(f"Error message: {result.error_message}")
    
    # Test non-existent folder
    print("\nTesting non-existent folder...")
    result = await wipe_service.wipe_folder("/nonexistent/folder", WipeMethod.SINGLE_PASS)
    print(f"Non-existent folder: {'✅' if not result.success else '❌'}")
    print(f"Error message: {result.error_message}")
    
    # Test invalid device
    print("\nTesting invalid device...")
    result = await wipe_service.wipe_drive("/dev/invalid", WipeMethod.SINGLE_PASS)
    print(f"Invalid device: {'✅' if not result.success else '❌'}")
    print(f"Error message: {result.error_message}")
    
    return True


async def test_operation_tracking():
    """Test operation tracking and cancellation"""
    print("\n📊 Testing Operation Tracking")
    print("=" * 50)
    
    wipe_service = WipeService(mock_mode=True)
    
    # Test active operations
    active_ops = wipe_service.get_active_operations()
    print(f"Active operations: {len(active_ops)}")
    
    # Test operation cancellation
    test_op_id = "test_operation_123"
    wipe_service.active_operations[test_op_id] = wipe_service.WipeStatus.IN_PROGRESS
    
    print(f"Added test operation: {test_op_id}")
    print(f"Active operations: {len(wipe_service.get_active_operations())}")
    
    # Cancel operation
    success = wipe_service.cancel_operation(test_op_id)
    print(f"Cancellation successful: {'✅' if success else '❌'}")
    
    # Try to cancel non-existent operation
    success = wipe_service.cancel_operation("nonexistent")
    print(f"Cancellation of non-existent: {'✅' if not success else '❌'}")
    
    return True


async def test_mock_mode():
    """Test mock mode functionality"""
    print("\n🎭 Testing Mock Mode")
    print("=" * 50)
    
    wipe_service = WipeService(mock_mode=True)
    
    print(f"Initial mock mode: {wipe_service.mock_mode}")
    
    # Test with mock mode enabled
    result = await wipe_service.wipe_file("/tmp/test.txt", WipeMethod.DOD_5220_22_M)
    print(f"Mock mode result: {'✅' if result.success else '❌'}")
    print(f"Mock mode flag: {result.mock_mode}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    
    # Disable mock mode
    wipe_service.set_mock_mode(False)
    print(f"Mock mode after disable: {wipe_service.mock_mode}")
    
    # Re-enable mock mode
    wipe_service.set_mock_mode(True)
    print(f"Mock mode after re-enable: {wipe_service.mock_mode}")
    
    return True


async def test_performance():
    """Test performance with different methods"""
    print("\n⚡ Testing Performance")
    print("=" * 50)
    
    wipe_service = WipeService(mock_mode=True)
    
    methods = [
        (WipeMethod.SINGLE_PASS, "Single Pass"),
        (WipeMethod.DOD_5220_22_M, "DoD 5220.22-M"),
        (WipeMethod.GUTMANN, "Gutmann")
    ]
    
    for method, name in methods:
        start_time = datetime.now()
        result = await wipe_service.wipe_file("/tmp/large_file.bin", method)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        print(f"{name}:")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Passes: {result.passes_completed}/{result.total_passes}")
        print(f"  Success: {'✅' if result.success else '❌'}")
        print()


async def main():
    """Run all wipe service tests"""
    print("🚀 Wipe Service Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("Wipe Methods", test_wipe_methods),
        ("Real File Wipe", test_real_file_wipe),
        ("Real Folder Wipe", test_folder_wipe),
        ("Error Handling", test_error_handling),
        ("Operation Tracking", test_operation_tracking),
        ("Mock Mode", test_mock_mode),
        ("Performance", test_performance)
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
        print("🎉 All wipe service tests passed!")
        print("\n🚀 The wipe service is ready to use.")
        print("📖 You can now use the wipe endpoints:")
        print("   POST /api/v1/wipe/file")
        print("   POST /api/v1/wipe/folder")
        print("   POST /api/v1/wipe/drive")
        print("   GET /api/v1/wipe/methods")
        print("   GET /api/v1/wipe/status")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
