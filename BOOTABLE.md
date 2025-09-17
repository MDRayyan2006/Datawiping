# DataWipe Bootable System

A complete bootable ISO version of DataWipe for secure offline system wipes.

## Overview

The DataWipe Bootable System is a self-contained, bootable ISO that provides secure data wiping capabilities without requiring an existing operating system. It includes both the FastAPI backend and a minimal web frontend for easy operation.

## Features

### 🔒 Complete Offline Operation
- No internet connection required
- Self-contained system
- Bootable from CD/DVD or USB

### 💾 Full System Wipe Capabilities
- Secure wiping of entire storage devices
- Multiple wipe standards (DoD, NIST, Gutmann)
- Real-time progress monitoring
- Certificate generation

### 🌐 Minimal Web Interface
- Simple HTML frontend
- Device selection and management
- Wipe method configuration
- Progress tracking

### 📄 Certificate Generation
- Digital certificates for verification
- PDF and JSON formats
- Cryptographic signatures
- Audit trail

## Quick Start

### 1. Create Bootable ISO
```bash
# Install requirements
pip install -r requirements-build.txt

# Create bootable ISO
python create_bootable_datawipe.py

# Or with custom name
python create_bootable_datawipe.py --output MyDataWipe.iso
```

### 2. Boot from ISO
1. Burn ISO to CD/DVD or create bootable USB
2. Boot from the media
3. Select "DataWipe - Secure System Wipe" from menu
4. Open browser to http://localhost:3000
5. Follow the web interface

## System Requirements

### Hardware Requirements
- **CPU**: x86_64 processor
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 1GB free space for ISO
- **Network**: Optional (for updates)

### Software Requirements (for building)
- **Python 3.8+**
- **GRUB** or **XORRISO** (for ISO creation)
- **Linux Live System** (Ubuntu/Debian based)

## Building the Bootable System

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install grub-pc-bin grub-efi-amd64-bin xorriso

# CentOS/RHEL
sudo yum install grub2-tools xorriso

# Install Python dependencies
pip install -r requirements-build.txt
```

### Build Process
```bash
# Create bootable ISO
python create_bootable_datawipe.py

# Output will be in bootable/DataWipe-Bootable.iso
```

### Build Options
```bash
# Custom output name
python create_bootable_datawipe.py --output CustomName.iso

# Verbose output
python create_bootable_datawipe.py --verbose
```

## ISO Structure

```
DataWipe-Bootable.iso
├── boot/
│   └── grub/
│       └── grub.cfg          # GRUB boot configuration
├── live/
│   └── datawipe/
│       ├── backend/          # FastAPI backend
│       │   ├── main.py       # Bootable main application
│       │   ├── models/       # Database models
│       │   ├── routers/      # API routes
│       │   ├── services/     # Business logic
│       │   └── utils/        # Utilities
│       ├── frontend/         # HTML interface
│       │   └── index.html    # Main web interface
│       ├── config/           # Configuration files
│       ├── certificates/     # Generated certificates
│       ├── logs/             # Application logs
│       └── scripts/          # Boot scripts
└── EFI/BOOT/                 # UEFI boot files
```

## Usage

### 1. Boot Process
1. Insert bootable media (CD/DVD/USB)
2. Boot from the media
3. Select "DataWipe - Secure System Wipe" from GRUB menu
4. Wait for system to load
5. Browser will open automatically to http://localhost:3000

### 2. Web Interface
1. **User Information**: Enter name, organization, device serial
2. **Device Selection**: Choose target device from detected list
3. **Wipe Method**: Select security standard
4. **Options**: Enable certificate generation
5. **Start Wipe**: Confirm and begin process
6. **Monitor Progress**: Watch real-time progress updates
7. **Download Certificate**: Get verification document

### 3. Wipe Methods Available
- **DoD 5220.22-M**: 3-pass military standard
- **NIST 800-88**: Government standard (1-3 passes)
- **Gutmann Method**: 35-pass maximum security
- **Single Pass**: Quick wipe with random data
- **Random Data**: 3-pass random overwrite
- **Zero Overwrite**: Single zero pass

## Security Features

### Privilege Management
- Automatic privilege detection
- Elevated operation for device access
- Secure file handling
- Permission validation

### Certificate Generation
- Digital signatures using cryptography
- Cryptographic verification
- PDF and JSON formats
- Tamper-proof records
- Audit trail maintenance

### Data Destruction
- Multiple overwrite passes
- Cryptographic verification
- Complete sector coverage
- HPA/DCO detection and handling
- Secure random data generation

## Bootable System Components

### Backend (FastAPI)
- Complete API server
- Database management
- Device detection
- Wipe operations
- Certificate generation
- Progress monitoring

### Frontend (HTML/JavaScript)
- Minimal web interface
- Device selection
- Form validation
- Progress tracking
- Real-time updates
- Certificate downloads

### Boot System
- GRUB bootloader
- Linux live system
- Automatic startup
- Network configuration
- Service management

## Creating Bootable Media

### Bootable USB (Linux/macOS)
```bash
# Using dd
sudo dd if=DataWipe-Bootable.iso of=/dev/sdX bs=4M status=progress

# Using Rufus (Windows)
# Select ISO file and USB device
# Use DD mode for best compatibility
```

### Burning to CD/DVD
```bash
# Using growisofs
growisofs -dvd-compat -Z /dev/dvd=DataWipe-Bootable.iso

# Using Brasero (GUI)
# File → Burn Image → Select ISO
```

## Troubleshooting

### Boot Issues
```bash
# If system doesn't boot
1. Check BIOS/UEFI settings
2. Enable legacy boot if needed
3. Try "Safe Mode" option
4. Verify ISO integrity
5. Check media for errors
```

### Network Issues
```bash
# If browser doesn't open
1. Manually open browser
2. Navigate to http://localhost:3000
3. Check if backend is running
4. Review logs in /live/datawipe/logs/
5. Verify network configuration
```

### Wipe Issues
```bash
# If wipe fails
1. Check device permissions
2. Verify target device selection
3. Review error logs
4. Try different wipe method
5. Check device health status
```

### Device Detection Issues
```bash
# If devices not detected
1. Check hardware connections
2. Verify device power
3. Review system logs
4. Try different USB ports
5. Check for hardware conflicts
```

## Advanced Configuration

### Custom Wipe Methods
Edit the wipe service to add custom methods:
```python
# Add to services/wipe.py
custom_methods = {
    "custom_3_pass": "Custom 3-pass method",
    "custom_7_pass": "Custom 7-pass method"
}
```

### Network Configuration
```bash
# Enable network access
dhclient eth0
# or
dhclient wlan0

# Static IP configuration
ip addr add 192.168.1.100/24 dev eth0
ip route add default via 192.168.1.1
```

### Logging Configuration
```python
# Modify logging in bootable_main.py
logging.basicConfig(
    level=logging.DEBUG,  # More verbose
    handlers=[
        logging.FileHandler('/live/datawipe/logs/debug.log'),
        logging.StreamHandler()
    ]
)
```

## Security Considerations

### Physical Security
- Store bootable media securely
- Limit access to authorized personnel
- Document all wipe operations
- Maintain audit trails
- Secure disposal of media

### Operational Security
- Verify device selection before wiping
- Use appropriate wipe methods
- Generate certificates for all operations
- Maintain proper documentation
- Follow organizational policies

### Legal Compliance
- Follow organizational policies
- Comply with data protection regulations
- Maintain proper authorization
- Document all procedures
- Ensure audit trail compliance

## Performance Optimization

### Boot Time Optimization
- Minimize startup services
- Optimize kernel parameters
- Use fast storage media
- Enable hardware acceleration

### Wipe Performance
- Use appropriate wipe methods
- Optimize for target hardware
- Monitor system resources
- Balance security vs. speed

## Distribution

### File Structure
```
bootable/
├── DataWipe-Bootable.iso     # Bootable ISO
├── create_bootable.py        # ISO creation script
├── bootable_main.py          # Bootable application
├── build_bootable.sh         # Linux build script
├── build_bootable.bat        # Windows build script
└── README.md                 # Documentation
```

### Distribution Methods
1. **Direct ISO Distribution**: Provide ISO file directly
2. **USB Distribution**: Pre-configured bootable USB
3. **Network Boot**: PXE boot configuration
4. **Cloud Distribution**: Download from secure repository

## Support

### Common Issues
1. **Boot fails**: Check BIOS settings and media integrity
2. **No devices found**: Verify hardware detection
3. **Wipe fails**: Check permissions and device status
4. **Certificate errors**: Verify file system permissions
5. **Network issues**: Check network configuration

### Getting Help
1. Check logs in `/live/datawipe/logs/`
2. Review system information at `/api/system`
3. Test with mock mode first
4. Contact support with error details
5. Review troubleshooting section

## Changelog

### Version 1.0.0
- Initial bootable system
- Complete offline operation
- Minimal web interface
- Multiple wipe standards
- Certificate generation
- Bootable ISO creation
- Cross-platform support
- Comprehensive documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- FastAPI team for the excellent web framework
- PyInstaller team for packaging support
- GRUB team for bootloader support
- Linux community for live system tools
