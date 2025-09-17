#!/usr/bin/env python3
"""
Standalone privilege checker for DataWipe application.
Can be run independently to check system privileges.
"""

import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from privilege_checker import PrivilegeChecker


def main():
    """Main function for standalone privilege checking"""
    print("DataWipe Privilege Checker")
    print("=" * 50)
    
    checker = PrivilegeChecker()
    
    # Check privileges
    is_elevated, message = checker.check_privileges()
    
    print(f"Operating System: {checker.os_type}")
    print(f"Privilege Status: {message}")
    print(f"Elevation Method: {checker.elevation_method or 'None'}")
    
    if is_elevated:
        print("\n✅ SUCCESS: Running with elevated privileges")
        print("All DataWipe operations should work correctly.")
    else:
        print("\n❌ WARNING: Not running with elevated privileges")
        print("Some operations may fail or be limited.")
        
        # Show elevation options
        print("\nElevation Options:")
        print("1. Request automatic elevation")
        print("2. Show manual elevation instructions")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                print("\nRequesting elevation...")
                if checker.request_elevation():
                    print("Elevation requested successfully.")
                else:
                    print("Failed to request elevation.")
                    checker.print_elevation_instructions()
                    
            elif choice == "2":
                checker.print_elevation_instructions()
                
            elif choice == "3":
                print("Exiting...")
                sys.exit(0)
                
            else:
                print("Invalid choice.")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(1)
    
    return is_elevated


if __name__ == "__main__":
    try:
        is_elevated = main()
        sys.exit(0 if is_elevated else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
