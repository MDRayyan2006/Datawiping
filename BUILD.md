# DataWipe Build Guide

This guide explains how to build standalone executables for the DataWipe application using PyInstaller.

## Prerequisites

### System Requirements
- **Python 3.8+** (recommended: Python 3.9 or 3.10)
- **Operating System**: Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **Memory**: At least 4GB RAM (8GB recommended for building)
- **Disk Space**: At least 2GB free space

### Required Tools

#### All Platforms
```bash
# Install Python dependencies
pip install -r requirements-build.txt
```

#### Windows (Optional - for installer creation)
- **NSIS** (Nullsoft Scriptable Install System)
  - Download from: https://nsis.sourceforge.io/
  - Add to PATH after installation

#### Linux (Optional - for installer creation)
```bash
# Ubuntu/Debian
sudo apt-get install fpm

# CentOS/RHEL
sudo yum install fpm
```

## Quick Start

### 1. Basic Build
```bash
# Build single-file executable
python build.py

# Build directory distribution
python build.py --onedir
```

### 2. Build with Debug Information
```bash
# Build with debug symbols (larger file, better error reporting)
python build.py --debug
```

### 3. Build with Installer
```bash
# Build executable and create platform-specific installer
python build.py --installer
```

## Build Options

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--onedir` | Create directory distribution instead of single file | `False` |
| `--debug` | Build with debug information | `False` |
| `--installer` | Create platform-specific installer | `False` |

### Build Types

#### Single File Distribution (`--onefile`)
- **Pros**: Single executable file, easy to distribute
- **Cons**: Slower startup time, larger memory usage
- **Use Case**: Simple distribution, portable applications

#### Directory Distribution (`--onedir`)
- **Pros**: Faster startup, smaller memory usage
- **Cons**: Multiple files, requires directory structure
- **Use Case**: Local installations, development

## Platform-Specific Instructions

### Windows

#### Prerequisites
```bash
# Install build requirements
pip install -r requirements-build.txt

# Optional: Install NSIS for installer creation
# Download from https://nsis.sourceforge.io/
```

#### Build Commands
```bash
# Basic build
python build.py

# Build with installer (requires NSIS)
python build.py --installer

# Build directory distribution
python build.py --onedir
```

#### Output Files
- `dist/DataWipe.exe` - Main executable
- `dist/start_datawipe.bat` - Windows batch launcher
- `dist/start_datawipe.ps1` - PowerShell launcher
- `dist/DataWipe-Installer.exe` - Windows installer (if created)

### Linux

#### Prerequisites
```bash
# Install build requirements
pip install -r requirements-build.txt

# Install system dependencies
sudo apt-get update
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev

# Optional: Install fpm for installer creation
sudo apt-get install fpm
```

#### Build Commands
```bash
# Basic build
python3 build.py

# Build with installer
python3 build.py --installer

# Build directory distribution
python3 build.py --onedir
```

#### Output Files
- `dist/DataWipe` - Main executable
- `dist/start_datawipe.sh` - Shell launcher
- `dist/install.sh` - Installation script

### macOS

#### Prerequisites
```bash
# Install build requirements
pip install -r requirements-build.txt

# Install Xcode command line tools
xcode-select --install
```

#### Build Commands
```bash
# Basic build
python3 build.py

# Build directory distribution
python3 build.py --onedir
```

#### Output Files
- `dist/DataWipe` - Main executable
- `dist/start_datawipe.sh` - Shell launcher

## Manual Build Process

If you prefer to build manually without the build script:

### 1. Install PyInstaller
```bash
pip install pyinstaller
```

### 2. Run PyInstaller
```bash
# Single file build
pyinstaller --onefile --clean datawipe.spec

# Directory build
pyinstaller --onedir --clean datawipe.spec

# Debug build
pyinstaller --debug=all --clean datawipe.spec
```

### 3. Manual File Management
After building, manually copy additional files:
```bash
# Copy certificates directory
cp -r certificates dist/

# Copy logs directory
cp -r logs dist/

# Copy documentation
cp README.md dist/
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: Missing modules in the built executable
**Solution**: Add missing modules to `hiddenimports` in `datawipe.spec`

#### 2. Large File Size
**Problem**: Executable is too large
**Solutions**:
- Use `--onedir` instead of `--onefile`
- Add unnecessary modules to `excludes` in `datawipe.spec`
- Use UPX compression (enabled by default)

#### 3. Slow Startup
**Problem**: Executable takes long to start
**Solutions**:
- Use `--onedir` distribution
- Disable UPX compression
- Optimize imports

#### 4. Permission Errors
**Problem**: Cannot access files or devices
**Solution**: Run with administrator/root privileges

#### 5. Missing Dependencies
**Problem**: Runtime errors about missing libraries
**Solutions**:
- Check `hiddenimports` in spec file
- Verify all dependencies are installed
- Test on clean system

### Debug Mode

Build with debug information for better error reporting:
```bash
python build.py --debug
```

This creates a larger executable with:
- Debug symbols
- Verbose error messages
- Console output
- Better stack traces

### Testing the Build

#### 1. Test on Build Machine
```bash
# Run the built executable
cd dist
./DataWipe  # Linux/macOS
DataWipe.exe  # Windows
```

#### 2. Test on Clean System
- Copy the distribution to a clean system
- Install no additional dependencies
- Test all functionality

#### 3. Test Privilege Requirements
```bash
# Test without elevated privileges
./DataWipe

# Test with elevated privileges
sudo ./DataWipe  # Linux/macOS
# Run as administrator on Windows
```

## Distribution

### File Structure
```
dist/
├── DataWipe[.exe]          # Main executable
├── start_datawipe.*        # Launcher scripts
├── README.txt              # Distribution documentation
├── certificates/           # Certificate storage
├── logs/                   # Log files
└── [installer files]       # Platform-specific installers
```

### Distribution Methods

#### 1. Direct Distribution
- Zip the entire `dist` directory
- Provide installation instructions
- Include platform-specific launchers

#### 2. Installer Distribution
- Use platform-specific installers
- Windows: NSIS installer
- Linux: Shell script installer
- macOS: DMG package (manual creation)

#### 3. Package Managers
- Create platform-specific packages
- Windows: MSI, NSIS installer
- Linux: DEB, RPM packages
- macOS: PKG, DMG packages

## Performance Optimization

### Build Optimization
1. **Exclude Unnecessary Modules**: Add to `excludes` in spec file
2. **Use UPX Compression**: Enabled by default
3. **Optimize Imports**: Remove unused imports
4. **Use Directory Distribution**: For better performance

### Runtime Optimization
1. **Lazy Loading**: Load modules only when needed
2. **Caching**: Cache frequently used data
3. **Memory Management**: Proper cleanup of resources
4. **Async Operations**: Use async/await for I/O operations

## Security Considerations

### Code Signing (Windows)
```bash
# Sign the executable (requires certificate)
signtool sign /f certificate.pfx /p password DataWipe.exe
```

### Verification
- Test on multiple systems
- Verify all functionality works
- Check for security vulnerabilities
- Validate certificate generation

## Continuous Integration

### GitHub Actions Example
```yaml
name: Build DataWipe
on: [push, pull_request]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: pip install -r requirements-build.txt
    
    - name: Build executable
      run: python build.py
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: DataWipe-${{ matrix.os }}
        path: dist/
```

## Support

For build-related issues:
1. Check this documentation
2. Review PyInstaller documentation
3. Check the project issues
4. Create a new issue with build logs

## Changelog

### Version 1.0.0
- Initial PyInstaller configuration
- Cross-platform build support
- Automatic launcher creation
- Installer generation
- Comprehensive documentation
