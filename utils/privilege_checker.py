#!/usr/bin/env python3
"""
Privilege checker utility for DataWipe application.
Checks if the application is running with administrator/root privileges
and handles elevation requests on Windows or provides instructions on Linux.
"""

import os
import sys
import platform
import subprocess
import ctypes
from typing import Tuple, Optional


class PrivilegeChecker:
    """Utility class for checking and requesting elevated privileges"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.is_elevated = False
        self.elevation_method = None
    
    def check_privileges(self) -> Tuple[bool, str]:
        """
        Check if the application is running with elevated privileges.
        
        Returns:
            Tuple[bool, str]: (is_elevated, message)
        """
        if self.os_type == "Windows":
            return self._check_windows_privileges()
        elif self.os_type == "Linux":
            return self._check_linux_privileges()
        elif self.os_type == "Darwin":  # macOS
            return self._check_macos_privileges()
        else:
            return False, f"Unsupported operating system: {self.os_type}"
    
    def _check_windows_privileges(self) -> Tuple[bool, str]:
        """Check Windows administrator privileges"""
        try:
            # Method 1: Check if we can access system directories
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            
            if is_admin:
                self.is_elevated = True
                self.elevation_method = "Windows UAC"
                return True, "Running with administrator privileges"
            
            # Method 2: Try to access a system directory
            try:
                test_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32')
                os.listdir(test_path)
                # If we can list System32, we likely have admin privileges
                self.is_elevated = True
                self.elevation_method = "Windows UAC"
                return True, "Running with administrator privileges"
            except PermissionError:
                pass
            
            # Method 3: Check if we're in a UAC-elevated process
            try:
                import winreg
                # Try to access a restricted registry key
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"):
                    self.is_elevated = True
                    self.elevation_method = "Windows UAC"
                    return True, "Running with administrator privileges"
            except PermissionError:
                pass
            
            self.is_elevated = False
            return False, "Not running with administrator privileges"
            
        except Exception as e:
            return False, f"Error checking Windows privileges: {e}"
    
    def _check_linux_privileges(self) -> Tuple[bool, str]:
        """Check Linux root privileges"""
        try:
            # Check if we're running as root (UID 0)
            if os.geteuid() == 0:
                self.is_elevated = True
                self.elevation_method = "Linux root"
                return True, "Running with root privileges"
            
            # Check if we have sudo privileges
            try:
                result = subprocess.run(
                    ['sudo', '-n', 'true'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.is_elevated = False  # We can get root, but aren't currently
                    self.elevation_method = "sudo"
                    return False, "Not running as root, but sudo privileges available"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            self.is_elevated = False
            return False, "Not running with root privileges"
            
        except Exception as e:
            return False, f"Error checking Linux privileges: {e}"
    
    def _check_macos_privileges(self) -> Tuple[bool, str]:
        """Check macOS administrator privileges"""
        try:
            # Check if we're running as root (UID 0)
            if os.geteuid() == 0:
                self.is_elevated = True
                self.elevation_method = "macOS root"
                return True, "Running with root privileges"
            
            # Check if we can use sudo
            try:
                result = subprocess.run(
                    ['sudo', '-n', 'true'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.is_elevated = False
                    self.elevation_method = "sudo"
                    return False, "Not running as root, but sudo privileges available"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            self.is_elevated = False
            return False, "Not running with administrator privileges"
            
        except Exception as e:
            return False, f"Error checking macOS privileges: {e}"
    
    def request_elevation(self, script_path: Optional[str] = None) -> bool:
        """
        Request elevation of privileges.
        
        Args:
            script_path: Path to the script to run with elevated privileges
            
        Returns:
            bool: True if elevation was requested successfully
        """
        if self.os_type == "Windows":
            return self._request_windows_elevation(script_path)
        elif self.os_type in ["Linux", "Darwin"]:
            return self._request_unix_elevation(script_path)
        else:
            print(f"Elevation not supported on {self.os_type}")
            return False
    
    def _request_windows_elevation(self, script_path: Optional[str] = None) -> bool:
        """Request Windows UAC elevation"""
        try:
            if script_path is None:
                script_path = sys.executable
            
            # Use ShellExecute with 'runas' verb to request UAC elevation
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                script_path,
                " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "",
                None,
                1  # SW_SHOWNORMAL
            )
            
            # ShellExecute returns a value > 32 on success
            if result > 32:
                print("UAC elevation requested. Please approve the elevation prompt.")
                return True
            else:
                print(f"Failed to request UAC elevation. Error code: {result}")
                return False
                
        except Exception as e:
            print(f"Error requesting Windows elevation: {e}")
            return False
    
    def _request_unix_elevation(self, script_path: Optional[str] = None) -> bool:
        """Request Unix elevation using sudo"""
        try:
            if script_path is None:
                script_path = sys.executable
            
            # Try to run with sudo
            cmd = ['sudo', script_path] + sys.argv[1:]
            
            print("Requesting sudo privileges...")
            result = subprocess.run(cmd)
            
            # If we reach here, the sudo command was executed
            # The current process will exit and the elevated process will continue
            sys.exit(result.returncode)
            
        except KeyboardInterrupt:
            print("\nElevation cancelled by user")
            return False
        except Exception as e:
            print(f"Error requesting Unix elevation: {e}")
            return False
    
    def print_elevation_instructions(self):
        """Print instructions for manual elevation"""
        print("\n" + "="*60)
        print("ELEVATION REQUIRED")
        print("="*60)
        
        if self.os_type == "Windows":
            print("This application requires administrator privileges to perform secure wiping operations.")
            print("\nTo run with administrator privileges:")
            print("1. Right-click on Command Prompt or PowerShell")
            print("2. Select 'Run as administrator'")
            print("3. Navigate to the application directory")
            print("4. Run the application again")
            print("\nAlternatively, you can:")
            print("1. Right-click on the application file")
            print("2. Select 'Run as administrator'")
            
        elif self.os_type == "Linux":
            print("This application requires root privileges to perform secure wiping operations.")
            print("\nTo run with root privileges:")
            print("1. Use sudo: sudo python3 main.py")
            print("2. Or switch to root: su -")
            print("3. Then run: python3 main.py")
            print("\nNote: Secure wiping operations require direct access to storage devices,")
            print("which typically requires root privileges on Linux.")
            
        elif self.os_type == "Darwin":  # macOS
            print("This application requires administrator privileges to perform secure wiping operations.")
            print("\nTo run with administrator privileges:")
            print("1. Use sudo: sudo python3 main.py")
            print("2. Or run from Terminal with administrator privileges")
            print("\nNote: You may be prompted for your password.")
        
        print("\n" + "="*60)
    
    def check_and_handle_privileges(self, auto_elevate: bool = False) -> bool:
        """
        Check privileges and handle elevation if needed.
        
        Args:
            auto_elevate: If True, automatically request elevation
            
        Returns:
            bool: True if running with elevated privileges
        """
        is_elevated, message = self.check_privileges()
        
        print(f"Privilege check: {message}")
        
        if is_elevated:
            print("✅ Application is running with elevated privileges")
            return True
        
        print("❌ Application is not running with elevated privileges")
        
        if auto_elevate:
            print("Attempting to request elevation...")
            if self.request_elevation():
                # If elevation was requested, the current process should exit
                # and the elevated process will continue
                return False
            else:
                print("Failed to request elevation")
        
        self.print_elevation_instructions()
        return False


def main():
    """Main function for testing the privilege checker"""
    checker = PrivilegeChecker()
    
    print("DataWipe Privilege Checker")
    print("=" * 40)
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {sys.version}")
    print()
    
    # Check current privileges
    is_elevated, message = checker.check_privileges()
    print(f"Current privileges: {message}")
    
    if not is_elevated:
        print("\nWould you like to request elevation? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                checker.request_elevation()
            else:
                checker.print_elevation_instructions()
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            sys.exit(1)
    
    return is_elevated


if __name__ == "__main__":
    main()
