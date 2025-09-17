@echo off
title DataWipe Build Script
echo DataWipe Build Script
echo ====================
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

REM Install build requirements
echo Installing build requirements...
pip install -r requirements-build.txt
if %errorLevel% neq 0 (
    echo ERROR: Failed to install build requirements
    pause
    exit /b 1
)

echo.
echo Build requirements installed successfully
echo.

REM Ask user for build options
echo Build Options:
echo 1. Single file executable (default)
echo 2. Directory distribution
echo 3. Debug build
echo 4. Build with installer
echo 5. All options
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Building single file executable...
    python build.py
) else if "%choice%"=="2" (
    echo Building directory distribution...
    python build.py --onedir
) else if "%choice%"=="3" (
    echo Building debug version...
    python build.py --debug
) else if "%choice%"=="4" (
    echo Building with installer...
    python build.py --installer
) else if "%choice%"=="5" (
    echo Building all versions...
    echo.
    echo Building single file...
    python build.py
    echo.
    echo Building directory distribution...
    python build.py --onedir
    echo.
    echo Building debug version...
    python build.py --debug
) else (
    echo Invalid choice. Building single file executable...
    python build.py
)

if %errorLevel% neq 0 (
    echo.
    echo ERROR: Build failed
    echo Check the error messages above
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo.
echo Output files are in the 'dist' directory:
dir /b dist
echo.
echo You can now distribute the DataWipe application.
echo.
pause
