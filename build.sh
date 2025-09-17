#!/bin/bash

echo "DataWipe Build Script"
echo "===================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

echo "Python found:"
python3 --version
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found"
    echo "Please run this script from the DataWipe project directory"
    exit 1
fi

echo "Project files found"
echo ""

# Install build requirements
echo "Installing build requirements..."
pip3 install -r requirements-build.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install build requirements"
    exit 1
fi

echo ""
echo "Build requirements installed successfully"
echo ""

# Ask user for build options
echo "Build Options:"
echo "1. Single file executable (default)"
echo "2. Directory distribution"
echo "3. Debug build"
echo "4. Build with installer"
echo "5. All options"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "Building single file executable..."
        python3 build.py
        ;;
    2)
        echo "Building directory distribution..."
        python3 build.py --onedir
        ;;
    3)
        echo "Building debug version..."
        python3 build.py --debug
        ;;
    4)
        echo "Building with installer..."
        python3 build.py --installer
        ;;
    5)
        echo "Building all versions..."
        echo ""
        echo "Building single file..."
        python3 build.py
        echo ""
        echo "Building directory distribution..."
        python3 build.py --onedir
        echo ""
        echo "Building debug version..."
        python3 build.py --debug
        ;;
    *)
        echo "Invalid choice. Building single file executable..."
        python3 build.py
        ;;
esac

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Build failed"
    echo "Check the error messages above"
    exit 1
fi

echo ""
echo "Build completed successfully!"
echo ""
echo "Output files are in the 'dist' directory:"
ls -la dist/
echo ""
echo "You can now distribute the DataWipe application."
echo ""

# Make executables runnable
chmod +x dist/DataWipe 2>/dev/null
chmod +x dist/start_datawipe.sh 2>/dev/null
chmod +x dist/install.sh 2>/dev/null

echo "Made executables runnable"
echo ""
