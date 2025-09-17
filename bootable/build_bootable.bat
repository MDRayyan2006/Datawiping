@echo off
title DataWipe Bootable Builder
echo DataWipe Bootable Builder
echo ========================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please run this script from the DataWipe project directory
    pause
    exit /b 1
)

echo Project files found
echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements-build.txt
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo Python dependencies installed
echo.

REM Note about Windows limitations
echo NOTE: Windows has limitations for creating bootable ISOs.
echo This script will create the bootable structure, but you may need
echo to use Linux or WSL to create the actual bootable ISO.
echo.

REM Create bootable structure
echo Creating bootable DataWipe structure...
python bootable/create_bootable.py

if %errorLevel% neq 0 (
    echo ERROR: Failed to create bootable structure
    pause
    exit /b 1
)

echo.
echo Bootable DataWipe structure created successfully!
echo.
echo Files created:
dir /b bootable
echo.
echo To create a bootable ISO on Linux:
echo 1. Copy the bootable directory to a Linux system
echo 2. Run: sudo ./bootable/build_bootable.sh
echo.
echo Or use WSL (Windows Subsystem for Linux):
echo 1. Install WSL with Ubuntu
echo 2. Copy files to WSL
echo 3. Run the Linux build script
echo.
pause
