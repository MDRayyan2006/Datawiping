#!/usr/bin/env python3
"""
Demonstration script showing privilege checking functionality.
"""

import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from privilege_checker import PrivilegeChecker


def demo_privilege_checking():
    """Demonstrate privilege checking functionality"""
    print("🔐 DataWipe Privilege Checking Demo")
    print("=" * 50)
    
    # Initialize privilege checker
    checker = PrivilegeChecker()
    
    print(f"Operating System: {checker.os_type}")
    print()
    
    # Check current privileges
    print("1️⃣ Checking current privileges...")
    is_elevated, message = checker.check_privileges()
    print(f"   Status: {message}")
    print(f"   Elevated: {'✅ Yes' if is_elevated else '❌ No'}")
    print(f"   Method: {checker.elevation_method or 'None'}")
    print()
    
    # Show what this means for the application
    print("2️⃣ What this means for DataWipe:")
    if is_elevated:
        print("   ✅ Full functionality available")
        print("   ✅ Can perform secure wiping operations")
        print("   ✅ Can access storage devices directly")
        print("   ✅ Can generate certificates")
    else:
        print("   ⚠️  Limited functionality")
        print("   ❌ Cannot perform secure wiping operations")
        print("   ❌ Cannot access storage devices directly")
        print("   ✅ Can use mock mode for testing")
        print("   ✅ Can generate certificates (if files accessible)")
    print()
    
    # Show elevation options
    print("3️⃣ Elevation Options:")
    if not is_elevated:
        print("   Option 1: Request automatic elevation")
        print("   Option 2: Manual elevation instructions")
        print("   Option 3: Use mock mode for testing")
        print()
        
        # Show elevation instructions
        print("📋 Manual Elevation Instructions:")
        checker.print_elevation_instructions()
    else:
        print("   ✅ Already running with elevated privileges")
        print("   No elevation needed")
    print()
    
    # Show mock mode information
    print("4️⃣ Mock Mode Information:")
    print("   Mock mode allows testing without elevated privileges")
    print("   - Simulates wipe operations")
    print("   - Generates test certificates")
    print("   - Safe for development and testing")
    print("   - No actual data destruction")
    print()
    
    return is_elevated


def demo_wipe_service_integration():
    """Demonstrate how privilege checking integrates with wipe service"""
    print("5️⃣ Wipe Service Integration Demo:")
    
    try:
        from services.wipe import WipeService
        
        print("   Testing wipe service with different privilege scenarios...")
        print()
        
        # Test with mock mode
        print("   🧪 Mock Mode (bypasses privilege checks):")
        wipe_service_mock = WipeService(mock_mode=True)
        try:
            wipe_service_mock._validate_privileges_for_operation("demo operation")
            print("   ✅ Mock mode validation passed")
        except Exception as e:
            print(f"   ❌ Mock mode validation failed: {e}")
        print()
        
        # Test without mock mode
        print("   🔒 Real Mode (requires privileges):")
        wipe_service_real = WipeService(mock_mode=False)
        try:
            wipe_service_real._validate_privileges_for_operation("demo operation")
            print("   ✅ Real mode validation passed (elevated privileges)")
        except PermissionError as e:
            print(f"   ⚠️  Real mode validation failed (expected if not elevated): {e}")
        except Exception as e:
            print(f"   ❌ Real mode validation failed: {e}")
        print()
        
    except ImportError as e:
        print(f"   ❌ Could not import wipe service: {e}")
    except Exception as e:
        print(f"   ❌ Error testing wipe service: {e}")


def main():
    """Main demonstration function"""
    try:
        # Run privilege checking demo
        is_elevated = demo_privilege_checking()
        
        # Run wipe service integration demo
        demo_wipe_service_integration()
        
        # Summary
        print("📊 Demo Summary:")
        print("=" * 50)
        if is_elevated:
            print("✅ You are running with elevated privileges")
            print("   DataWipe will have full functionality")
            print("   All secure wiping operations will work")
        else:
            print("⚠️  You are not running with elevated privileges")
            print("   DataWipe will have limited functionality")
            print("   Use mock mode for testing or elevate privileges")
        
        print("\n🚀 Next Steps:")
        if is_elevated:
            print("   1. Run: python main.py")
            print("   2. Access: http://localhost:8000/docs")
            print("   3. Start secure wiping operations")
        else:
            print("   1. Run: python start_datawipe.py (for elevation)")
            print("   2. Or enable mock mode in the application")
            print("   3. Or run: sudo python main.py (Linux/macOS)")
        
        return 0
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
