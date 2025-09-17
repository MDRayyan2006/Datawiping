#!/usr/bin/env python3
"""
Build script for DataWipe application using PyInstaller.
Creates standalone executables for Windows and Linux.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import argparse


class DataWipeBuilder:
    """Builder class for DataWipe application"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.spec_file = self.project_root / "datawipe.spec"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.os_type = platform.system()
        self.arch = platform.machine()
        
    def check_requirements(self):
        """Check if all required tools are installed"""
        print("🔍 Checking build requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            return False
        
        print(f"✅ Python {sys.version.split()[0]} detected")
        
        # Check PyInstaller
        try:
            import PyInstaller
            print(f"✅ PyInstaller {PyInstaller.__version__} detected")
        except ImportError:
            print("❌ PyInstaller not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller installed")
        
        # Check if spec file exists
        if not self.spec_file.exists():
            print("❌ datawipe.spec file not found")
            return False
        
        print("✅ datawipe.spec file found")
        
        # Check if main.py exists
        main_py = self.project_root / "main.py"
        if not main_py.exists():
            print("❌ main.py file not found")
            return False
        
        print("✅ main.py file found")
        
        return True
    
    def clean_build_dirs(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning previous build artifacts...")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print("✅ Removed dist directory")
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print("✅ Removed build directory")
    
    def create_directories(self):
        """Create necessary directories"""
        print("📁 Creating directories...")
        
        # Create certificates directory if it doesn't exist
        certs_dir = self.project_root / "certificates"
        certs_dir.mkdir(exist_ok=True)
        print("✅ Certificates directory ready")
        
        # Create logs directory if it doesn't exist
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        print("✅ Logs directory ready")
    
    def build_executable(self, onefile=True, debug=False):
        """Build the executable using PyInstaller"""
        print("🔨 Building executable...")
        
        # Build command
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
        ]
        
        if onefile:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")
        
        if debug:
            cmd.append("--debug=all")
        else:
            cmd.append("--noconsole")  # Remove console window for production
        
        # Add spec file
        cmd.append(str(self.spec_file))
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ Build completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def create_launcher_scripts(self):
        """Create platform-specific launcher scripts"""
        print("📝 Creating launcher scripts...")
        
        if self.os_type == "Windows":
            self._create_windows_launcher()
        else:
            self._create_unix_launcher()
    
    def _create_windows_launcher(self):
        """Create Windows launcher scripts"""
        # Batch file launcher
        batch_content = '''@echo off
title DataWipe Server
echo Starting DataWipe Server...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges
) else (
    echo WARNING: Not running as administrator
    echo Some operations may be limited
    echo.
    echo To run with administrator privileges:
    echo 1. Right-click this file
    echo 2. Select "Run as administrator"
    echo.
    pause
)

echo Starting DataWipe API server...
echo Server will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo Press Ctrl+C to stop the server
echo.

DataWipe.exe

pause
'''
        
        batch_file = self.dist_dir / "start_datawipe.bat"
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        print("✅ Created start_datawipe.bat")
        
        # PowerShell launcher
        ps_content = '''# DataWipe PowerShell Launcher
Write-Host "Starting DataWipe Server..." -ForegroundColor Green
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if ($isAdmin) {
    Write-Host "Running with administrator privileges" -ForegroundColor Green
} else {
    Write-Host "WARNING: Not running as administrator" -ForegroundColor Yellow
    Write-Host "Some operations may be limited" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To run with administrator privileges:" -ForegroundColor Cyan
    Write-Host "1. Right-click this file" -ForegroundColor Cyan
    Write-Host "2. Select 'Run with PowerShell'" -ForegroundColor Cyan
    Write-Host "3. Or run PowerShell as administrator" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to continue"
}

Write-Host "Starting DataWipe API server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    .\\DataWipe.exe
} catch {
    Write-Host "Error starting application: $_" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
'''
        
        ps_file = self.dist_dir / "start_datawipe.ps1"
        with open(ps_file, 'w') as f:
            f.write(ps_content)
        print("✅ Created start_datawipe.ps1")
    
    def _create_unix_launcher(self):
        """Create Unix launcher script"""
        shell_content = '''#!/bin/bash

echo "Starting DataWipe Server..."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Running with root privileges"
else
    echo "WARNING: Not running as root"
    echo "Some operations may be limited"
    echo ""
    echo "To run with root privileges:"
    echo "1. Use sudo: sudo ./start_datawipe.sh"
    echo "2. Or switch to root: su -"
    echo ""
    read -p "Press Enter to continue..."
fi

echo "Starting DataWipe API server..."
echo "Server will be available at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo ""

# Make the executable runnable
chmod +x ./DataWipe

# Run the application
./DataWipe
'''
        
        shell_file = self.dist_dir / "start_datawipe.sh"
        with open(shell_file, 'w') as f:
            f.write(shell_content)
        
        # Make it executable
        os.chmod(shell_file, 0o755)
        print("✅ Created start_datawipe.sh")
    
    def create_readme(self):
        """Create README for the distribution"""
        print("📖 Creating distribution README...")
        
        readme_content = f'''# DataWipe Standalone Application

This is a standalone distribution of the DataWipe application.

## System Information
- Operating System: {self.os_type}
- Architecture: {self.arch}
- Python Version: {sys.version.split()[0]}

## Quick Start

### Windows
1. Double-click `start_datawipe.bat` to start the server
2. Or right-click and "Run as administrator" for full functionality
3. Open your browser to http://localhost:8000/docs

### Linux/macOS
1. Run `./start_datawipe.sh` to start the server
2. Or use `sudo ./start_datawipe.sh` for full functionality
3. Open your browser to http://localhost:8000/docs

## Files Included
- `DataWipe.exe` (Windows) / `DataWipe` (Linux/macOS) - Main application
- `start_datawipe.*` - Launcher scripts
- `certificates/` - Directory for generated certificates
- `logs/` - Directory for application logs

## Features
- Secure data wiping with multiple standards
- Device detection and management
- Certificate generation and verification
- RESTful API with interactive documentation
- Cross-platform support

## API Documentation
Once the server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Troubleshooting
- If you get permission errors, run with administrator/root privileges
- Check the logs directory for error messages
- Ensure port 8000 is not in use by another application

## Support
For support and documentation, visit the project repository.
'''
        
        readme_file = self.dist_dir / "README.txt"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        print("✅ Created README.txt")
    
    def copy_additional_files(self):
        """Copy additional files to the distribution"""
        print("📋 Copying additional files...")
        
        # Copy certificates directory
        certs_src = self.project_root / "certificates"
        if certs_src.exists():
            certs_dst = self.dist_dir / "certificates"
            shutil.copytree(certs_src, certs_dst, dirs_exist_ok=True)
            print("✅ Copied certificates directory")
        
        # Copy logs directory
        logs_src = self.project_root / "logs"
        if logs_src.exists():
            logs_dst = self.dist_dir / "logs"
            shutil.copytree(logs_src, logs_dst, dirs_exist_ok=True)
            print("✅ Copied logs directory")
        
        # Copy README.md if it exists
        readme_src = self.project_root / "README.md"
        if readme_src.exists():
            readme_dst = self.dist_dir / "README.md"
            shutil.copy2(readme_src, readme_dst)
            print("✅ Copied README.md")
    
    def create_installer(self):
        """Create platform-specific installer (optional)"""
        print("📦 Creating installer...")
        
        if self.os_type == "Windows":
            self._create_windows_installer()
        else:
            self._create_unix_installer()
    
    def _create_windows_installer(self):
        """Create Windows installer using NSIS (if available)"""
        try:
            # Check if NSIS is available
            subprocess.run(["makensis", "/VERSION"], check=True, capture_output=True)
            print("✅ NSIS found, creating Windows installer...")
            
            # Create NSIS script
            nsis_script = self.dist_dir / "installer.nsi"
            nsis_content = '''!define APPNAME "DataWipe"
!define COMPANYNAME "DataWipe"
!define DESCRIPTION "Secure Data Wiping Application"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "https://github.com/your-repo/datawipe"
!define UPDATEURL "https://github.com/your-repo/datawipe"
!define ABOUTURL "https://github.com/your-repo/datawipe"
!define INSTALLSIZE 50000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\\${APPNAME}"
Name "${APPNAME}"
Icon "DataWipe.exe"
outFile "DataWipe-Installer.exe"

!include LogicLib.nsh

page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    file "DataWipe.exe"
    file "start_datawipe.bat"
    file "start_datawipe.ps1"
    file "README.txt"
    
    setOutPath "$INSTDIR\\certificates"
    file /r "certificates\\*"
    
    setOutPath "$INSTDIR\\logs"
    file /r "logs\\*"
    
    writeUninstaller "$INSTDIR\\uninstall.exe"
    
    createDirectory "$SMPROGRAMS\\${APPNAME}"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\DataWipe.exe" "" "$INSTDIR\\DataWipe.exe"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\Start DataWipe.lnk" "$INSTDIR\\start_datawipe.bat" "" "$INSTDIR\\start_datawipe.bat"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe" "" "$INSTDIR\\uninstall.exe"
sectionEnd

section "uninstall"
    delete "$INSTDIR\\DataWipe.exe"
    delete "$INSTDIR\\start_datawipe.bat"
    delete "$INSTDIR\\start_datawipe.ps1"
    delete "$INSTDIR\\README.txt"
    delete "$INSTDIR\\uninstall.exe"
    
    rmDir /r "$INSTDIR\\certificates"
    rmDir /r "$INSTDIR\\logs"
    rmDir "$INSTDIR"
    
    delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
    delete "$SMPROGRAMS\\${APPNAME}\\Start DataWipe.lnk"
    delete "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk"
    rmDir "$SMPROGRAMS\\${APPNAME}"
sectionEnd
'''
            
            with open(nsis_script, 'w') as f:
                f.write(nsis_content)
            
            # Run NSIS
            subprocess.run(["makensis", str(nsis_script)], check=True)
            print("✅ Windows installer created")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  NSIS not found, skipping Windows installer creation")
    
    def _create_unix_installer(self):
        """Create Unix installer script"""
        install_script = self.dist_dir / "install.sh"
        install_content = '''#!/bin/bash

echo "DataWipe Installation Script"
echo "============================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script requires root privileges to install system-wide."
    echo "Please run with sudo: sudo ./install.sh"
    exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/datawipe"
echo "Installing to $INSTALL_DIR..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/certificates"
mkdir -p "$INSTALL_DIR/logs"

# Copy files
cp DataWipe "$INSTALL_DIR/"
cp start_datawipe.sh "$INSTALL_DIR/"
cp README.txt "$INSTALL_DIR/"
cp -r certificates/* "$INSTALL_DIR/certificates/" 2>/dev/null || true
cp -r logs/* "$INSTALL_DIR/logs/" 2>/dev/null || true

# Make executable
chmod +x "$INSTALL_DIR/DataWipe"
chmod +x "$INSTALL_DIR/start_datawipe.sh"

# Create symlink in /usr/local/bin
ln -sf "$INSTALL_DIR/DataWipe" /usr/local/bin/datawipe
ln -sf "$INSTALL_DIR/start_datawipe.sh" /usr/local/bin/start-datawipe

# Create desktop entry
cat > /usr/share/applications/datawipe.desktop << EOF
[Desktop Entry]
Name=DataWipe
Comment=Secure Data Wiping Application
Exec=$INSTALL_DIR/DataWipe
Icon=application-x-executable
Terminal=true
Type=Application
Categories=System;Security;
EOF

echo "✅ Installation completed successfully!"
echo ""
echo "You can now run DataWipe using:"
echo "  datawipe"
echo "  start-datawipe"
echo "  $INSTALL_DIR/start_datawipe.sh"
echo ""
echo "Or find it in your applications menu."
'''
        
        with open(install_script, 'w') as f:
            f.write(install_content)
        
        os.chmod(install_script, 0o755)
        print("✅ Created install.sh")
    
    def build(self, onefile=True, debug=False, create_installer=False):
        """Main build method"""
        print("🚀 Starting DataWipe build process...")
        print(f"Platform: {self.os_type} {self.arch}")
        print(f"Python: {sys.version.split()[0]}")
        print("")
        
        # Check requirements
        if not self.check_requirements():
            return False
        
        # Clean previous builds
        self.clean_build_dirs()
        
        # Create directories
        self.create_directories()
        
        # Build executable
        if not self.build_executable(onefile=onefile, debug=debug):
            return False
        
        # Create launcher scripts
        self.create_launcher_scripts()
        
        # Copy additional files
        self.copy_additional_files()
        
        # Create README
        self.create_readme()
        
        # Create installer if requested
        if create_installer:
            self.create_installer()
        
        print("")
        print("🎉 Build completed successfully!")
        print(f"📁 Output directory: {self.dist_dir}")
        print("")
        print("Files created:")
        for file in self.dist_dir.iterdir():
            if file.is_file():
                size = file.stat().st_size
                size_str = f"{size / 1024 / 1024:.1f} MB" if size > 1024 * 1024 else f"{size / 1024:.1f} KB"
                print(f"  📄 {file.name} ({size_str})")
            elif file.is_dir():
                print(f"  📁 {file.name}/")
        
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build DataWipe application")
    parser.add_argument("--onedir", action="store_true", help="Create directory distribution instead of single file")
    parser.add_argument("--debug", action="store_true", help="Build with debug information")
    parser.add_argument("--installer", action="store_true", help="Create platform-specific installer")
    
    args = parser.parse_args()
    
    builder = DataWipeBuilder()
    success = builder.build(
        onefile=not args.onedir,
        debug=args.debug,
        create_installer=args.installer
    )
    
    if success:
        print("\n✅ Build completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
