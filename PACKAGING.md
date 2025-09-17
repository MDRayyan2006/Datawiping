# DataWipe Packaging Guide

This document provides a comprehensive guide for packaging the DataWipe application into standalone executables.

## Overview

The DataWipe application can be packaged into standalone executables for Windows (.exe) and Linux/macOS (binary) using PyInstaller. This allows distribution without requiring Python installation on target systems.

## Quick Start

### Windows
```bash
# Install build requirements
pip install -r requirements-build.txt

# Build executable
python build.py

# Or use the batch script
build.bat
```

### Linux/macOS
```bash
# Install build requirements
pip3 install -r requirements-build.txt

# Build executable
python3 build.py

# Or use the shell script
./build.sh
```

## Files Created

### Core Build Files
- `datawipe.spec` - PyInstaller specification file
- `build.py` - Automated build script
- `requirements-build.txt` - Build dependencies
- `build.bat` - Windows build script
- `build.sh` - Linux/macOS build script

### Output Files
After building, the `dist/` directory contains:
- `DataWipe.exe` (Windows) / `DataWipe` (Linux/macOS) - Main executable
- `start_datawipe.*` - Platform-specific launcher scripts
- `README.txt` - Distribution documentation
- `certificates/` - Certificate storage directory
- `logs/` - Log files directory
- `install.sh` (Linux) - Installation script
- `DataWipe-Installer.exe` (Windows) - NSIS installer (if created)

## Build Options

### 1. Single File Distribution (Default)
```bash
python build.py
```
- Creates a single executable file
- Easy to distribute and run
- Slower startup time
- Larger memory usage

### 2. Directory Distribution
```bash
python build.py --onedir
```
- Creates a directory with multiple files
- Faster startup time
- Smaller memory usage
- Requires maintaining directory structure

### 3. Debug Build
```bash
python build.py --debug
```
- Includes debug symbols
- Verbose error messages
- Console output
- Larger file size

### 4. Build with Installer
```bash
python build.py --installer
```
- Creates platform-specific installer
- Windows: NSIS installer
- Linux: Shell installation script

## Platform-Specific Instructions

### Windows

#### Prerequisites
- Python 3.8+
- Visual Studio Build Tools (for some dependencies)
- NSIS (optional, for installer creation)

#### Build Process
```bash
# Install dependencies
pip install -r requirements-build.txt

# Build executable
python build.py

# Build with installer (requires NSIS)
python build.py --installer
```

#### Output
- `DataWipe.exe` - Main executable
- `start_datawipe.bat` - Batch launcher
- `start_datawipe.ps1` - PowerShell launcher
- `DataWipe-Installer.exe` - NSIS installer

### Linux

#### Prerequisites
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
sudo yum install openssl-devel libffi-devel python3-devel
```

#### Build Process
```bash
# Install dependencies
pip3 install -r requirements-build.txt

# Build executable
python3 build.py

# Build with installer
python3 build.py --installer
```

#### Output
- `DataWipe` - Main executable
- `start_datawipe.sh` - Shell launcher
- `install.sh` - Installation script

### macOS

#### Prerequisites
```bash
# Install Xcode command line tools
xcode-select --install

# Install dependencies
pip3 install -r requirements-build.txt
```

#### Build Process
```bash
# Build executable
python3 build.py

# Build directory distribution
python3 build.py --onedir
```

#### Output
- `DataWipe` - Main executable
- `start_datawipe.sh` - Shell launcher

## PyInstaller Configuration

### Spec File Features
The `datawipe.spec` file includes:

1. **Comprehensive Hidden Imports**
   - FastAPI and related modules
   - SQLAlchemy and database modules
   - Cryptography and security modules
   - ReportLab for PDF generation
   - Platform-specific modules

2. **Data Files**
   - Project structure (models, routers, services, utils)
   - Configuration files
   - Documentation files
   - Test files (optional)

3. **Exclusions**
   - Unnecessary modules (tkinter, matplotlib, etc.)
   - Development tools
   - Testing frameworks

4. **Optimizations**
   - UPX compression enabled
   - Duplicate removal
   - Console mode for debugging

### Customization

#### Adding New Modules
Edit `datawipe.spec` and add to `hiddenimports`:
```python
hiddenimports = [
    # ... existing imports ...
    'your_new_module',
]
```

#### Excluding Modules
Add to `excludes` in the spec file:
```python
excludes = [
    # ... existing exclusions ...
    'unwanted_module',
]
```

#### Adding Data Files
Add to `datas` in the spec file:
```python
datas = [
    # ... existing data files ...
    ('path/to/file', 'destination'),
]
```

## Distribution

### File Structure
```
dist/
├── DataWipe[.exe]          # Main executable
├── start_datawipe.*        # Launcher scripts
├── README.txt              # Distribution docs
├── certificates/           # Certificate storage
├── logs/                   # Log files
└── [installer files]       # Platform installers
```

### Distribution Methods

#### 1. Direct Distribution
- Zip the entire `dist` directory
- Provide installation instructions
- Include platform-specific launchers

#### 2. Installer Distribution
- Use platform-specific installers
- Automatic installation process
- System integration

#### 3. Package Managers
- Create platform-specific packages
- Integration with system package managers

## Testing

### Local Testing
```bash
# Test the built executable
cd dist
./DataWipe  # Linux/macOS
DataWipe.exe  # Windows
```

### Clean System Testing
1. Copy distribution to clean system
2. Install no additional dependencies
3. Test all functionality
4. Verify privilege requirements

### Privilege Testing
```bash
# Test without elevated privileges
./DataWipe

# Test with elevated privileges
sudo ./DataWipe  # Linux/macOS
# Run as administrator on Windows
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: Missing modules in executable
**Solution**: Add to `hiddenimports` in spec file

#### 2. Large File Size
**Problem**: Executable too large
**Solutions**:
- Use `--onedir` distribution
- Add modules to `excludes`
- Use UPX compression

#### 3. Slow Startup
**Problem**: Long startup time
**Solutions**:
- Use directory distribution
- Disable UPX compression
- Optimize imports

#### 4. Permission Errors
**Problem**: Cannot access files/devices
**Solution**: Run with elevated privileges

#### 5. Missing Dependencies
**Problem**: Runtime errors
**Solutions**:
- Check `hiddenimports`
- Verify dependencies
- Test on clean system

### Debug Mode
```bash
# Build with debug information
python build.py --debug
```

This provides:
- Debug symbols
- Verbose error messages
- Console output
- Better stack traces

## Security Considerations

### Code Signing (Windows)
```bash
# Sign executable (requires certificate)
signtool sign /f certificate.pfx /p password DataWipe.exe
```

### Verification
- Test on multiple systems
- Verify all functionality
- Check security features
- Validate certificates

## Performance Optimization

### Build Optimization
1. Exclude unnecessary modules
2. Use UPX compression
3. Optimize imports
4. Use directory distribution

### Runtime Optimization
1. Lazy loading
2. Caching
3. Memory management
4. Async operations

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

For packaging issues:
1. Check this documentation
2. Review PyInstaller documentation
3. Check project issues
4. Create new issue with build logs

## Changelog

### Version 1.0.0
- Initial PyInstaller configuration
- Cross-platform build support
- Automated build scripts
- Installer generation
- Comprehensive documentation
