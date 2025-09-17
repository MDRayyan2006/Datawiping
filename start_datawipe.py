#!/usr/bin/env python3
"""
DataWipe Application Startup Script
Handles privilege checking and elevation automatically.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from privilege_checker import PrivilegeChecker


def main():
    """Main startup function"""
    print("DataWipe Application Launcher")
    print("=" * 50)
    
    # Initialize privilege checker
    checker = PrivilegeChecker()
    
    # Check current privileges
    is_elevated, message = checker.check_privileges()
    print(f"Current privileges: {message}")
    
    if is_elevated:
        print("✅ Running with elevated privileges")
        # Start the application directly
        start_application()
    else:
        print("❌ Not running with elevated privileges")
        print("\nThis application requires elevated privileges for secure wiping operations.")
        
        # Ask user what they want to do
        print("\nOptions:")
        print("1. Request elevation (recommended)")
        print("2. Continue without elevation (limited functionality)")
        print("3. Exit")
        
        try:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                print("\nRequesting elevation...")
                if checker.request_elevation():
                    # If elevation was successful, the current process will exit
                    # and the elevated process will continue
                    return
                else:
                    print("Failed to request elevation. Please try running manually with elevated privileges.")
                    checker.print_elevation_instructions()
                    sys.exit(1)
                    
            elif choice == "2":
                print("\n⚠️  WARNING: Continuing without elevated privileges!")
                print("Some operations may fail or be limited.")
                start_application()
                
            elif choice == "3":
                print("Exiting...")
                sys.exit(0)
                
            else:
                print("Invalid choice. Exiting...")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            sys.exit(1)


def start_application():
    """Start the DataWipe application"""
    print("\nStarting DataWipe API server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Import and run the main application
        import main
        # The main module will handle the rest
    except ImportError as e:
        print(f"Error importing main module: {e}")
        print("Make sure you're running this script from the correct directory")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


def create_elevation_scripts():
    """Create platform-specific elevation scripts"""
    os_type = platform.system()
    
    if os_type == "Windows":
        create_windows_scripts()
    elif os_type in ["Linux", "Darwin"]:
        create_unix_scripts()


def create_windows_scripts():
    """Create Windows batch files for elevation"""
    # Create run_as_admin.bat
    batch_content = '''@echo off
echo DataWipe - Running with Administrator Privileges
echo ================================================
echo.
echo This will start the DataWipe API server with administrator privileges.
echo Please approve the UAC prompt if it appears.
echo.
pause
python main.py
pause
'''
    
    with open("run_as_admin.bat", "w") as f:
        f.write(batch_content)
    
    # Create PowerShell script
    ps_content = '''# DataWipe PowerShell Launcher
Write-Host "DataWipe - Running with Administrator Privileges" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "This will start the DataWipe API server with administrator privileges." -ForegroundColor Yellow
Write-Host "Please approve the UAC prompt if it appears." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"

try {
    python main.py
} catch {
    Write-Host "Error starting application: $_" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
'''
    
    with open("run_as_admin.ps1", "w") as f:
        f.write(ps_content)
    
    print("Created Windows elevation scripts:")
    print("- run_as_admin.bat (Batch file)")
    print("- run_as_admin.ps1 (PowerShell script)")


def create_unix_scripts():
    """Create Unix shell scripts for elevation"""
    # Create run_as_root.sh
    shell_content = '''#!/bin/bash
echo "DataWipe - Running with Root Privileges"
echo "======================================="
echo ""
echo "This will start the DataWipe API server with root privileges."
echo "You may be prompted for your password."
echo ""
read -p "Press Enter to continue..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Requesting sudo privileges..."
    sudo python3 main.py
else
    echo "Already running as root, starting application..."
    python3 main.py
fi
'''
    
    with open("run_as_root.sh", "w") as f:
        f.write(shell_content)
    
    # Make it executable
    os.chmod("run_as_root.sh", 0o755)
    
    print("Created Unix elevation script:")
    print("- run_as_root.sh (Shell script)")


if __name__ == "__main__":
    # Check if user wants to create elevation scripts
    if len(sys.argv) > 1 and sys.argv[1] == "--create-scripts":
        create_elevation_scripts()
        sys.exit(0)
    
    main()
