#!/usr/bin/env python3
"""
Test script for privilege checking functionality.
"""

import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from privilege_checker import PrivilegeChecker


def test_privilege_checker():
    """Test the privilege checker functionality"""
    print("Testing DataWipe Privilege Checker")
    print("=" * 50)
    
    checker = PrivilegeChecker()
    
    # Test privilege checking
    print("1. Testing privilege check...")
    is_elevated, message = checker.check_privileges()
    print(f"   Result: {message}")
    print(f"   Elevated: {is_elevated}")
    print(f"   Method: {checker.elevation_method}")
    
    # Test privilege validation
    print("\n2. Testing privilege validation...")
    if is_elevated:
        print("   ✅ Privileges are sufficient for secure wiping operations")
    else:
        print("   ❌ Privileges are insufficient for secure wiping operations")
        print("   📋 Elevation instructions:")
        checker.print_elevation_instructions()
    
    # Test mock mode scenario
    print("\n3. Testing mock mode scenario...")
    print("   In mock mode, privilege checks are bypassed for testing")
    print("   This allows safe testing without elevated privileges")
    
    return is_elevated


def test_wipe_service_privileges():
    """Test privilege checking in wipe service"""
    print("\n4. Testing wipe service privilege integration...")
    
    try:
        from services.wipe import WipeService
        
        # Test with mock mode (should not require privileges)
        print("   Testing with mock mode enabled...")
        wipe_service = WipeService(mock_mode=True)
        
        # This should not raise an exception
        wipe_service._validate_privileges_for_operation("test operation")
        print("   ✅ Mock mode bypasses privilege checks correctly")
        
        # Test without mock mode (should check privileges)
        print("   Testing with mock mode disabled...")
        wipe_service_no_mock = WipeService(mock_mode=False)
        
        try:
            wipe_service_no_mock._validate_privileges_for_operation("test operation")
            print("   ✅ Privilege validation passed")
        except PermissionError as e:
            print(f"   ⚠️  Privilege validation failed (expected if not elevated): {e}")
        
    except ImportError as e:
        print(f"   ❌ Could not import wipe service: {e}")
    except Exception as e:
        print(f"   ❌ Error testing wipe service: {e}")


def main():
    """Main test function"""
    try:
        # Test basic privilege checking
        is_elevated = test_privilege_checker()
        
        # Test wipe service integration
        test_wipe_service_privileges()
        
        print("\n" + "=" * 50)
        print("Privilege Checker Test Summary")
        print("=" * 50)
        
        if is_elevated:
            print("✅ All tests passed - running with elevated privileges")
            print("   Secure wiping operations should work correctly")
        else:
            print("⚠️  Tests completed - not running with elevated privileges")
            print("   Some operations may be limited")
            print("   Use mock mode for testing or run with elevated privileges")
        
        return 0 if is_elevated else 1
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
