# DataWipe Bootable System

A bootable ISO version of DataWipe for secure offline system wipes.

## Features

- **Complete Offline Operation**: No internet connection required
- **Full System Wipe**: Secure wiping of entire storage devices
- **Minimal Web Interface**: Simple HTML frontend for easy operation
- **Certificate Generation**: Digital certificates for wipe verification
- **Multiple Wipe Standards**: DoD, NIST, Gutmann, and custom methods
- **Bootable ISO**: Can be burned to CD/DVD or USB

## Quick Start

### 1. Create Bootable ISO
```bash
# Install requirements
pip install -r requirements-build.txt

# Create bootable ISO
python bootable/create_bootable.py

# Or with custom name
python bootable/create_bootable.py --output MyDataWipe.iso
```

### 2. Boot from ISO
1. Burn ISO to CD/DVD or create bootable USB
2. Boot from the media
3. Select "DataWipe - Secure System Wipe" from menu
4. Open browser to http://localhost:3000
5. Follow the web interface

## System Requirements

### Hardware
- **CPU**: x86_64 processor
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 1GB free space for ISO
- **Network**: Optional (for updates)

### Software
- **Python 3.8+** (for building)
- **GRUB** or **XORRISO** (for ISO creation)
- **Linux Live System** (Ubuntu/Debian based)

## Building the Bootable System

### Prerequisites
```bash
# Install build tools
sudo apt-get update
sudo apt-get install grub-pc-bin grub-efi-amd64-bin xorriso

# Install Python dependencies
pip install -r requirements-build.txt
```

### Build Process
```bash
# Create bootable ISO
python bootable/create_bootable.py

# Output will be in bootable/DataWipe-Bootable.iso
```

### Build Options
```bash
# Custom output name
python bootable/create_bootable.py --output CustomName.iso

# Verbose output
python bootable/create_bootable.py --verbose
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
│       ├── frontend/         # HTML interface
│       ├── config/           # Configuration files
│       ├── certificates/     # Generated certificates
│       ├── logs/             # Application logs
│       └── scripts/          # Boot scripts
└── EFI/BOOT/                 # UEFI boot files
```

## Usage

### 1. Boot Process
1. Insert bootable media
2. Boot from CD/DVD/USB
3. Select "DataWipe - Secure System Wipe"
4. Wait for system to load
5. Browser will open automatically

### 2. Web Interface
1. **User Information**: Enter name, organization, device serial
2. **Device Selection**: Choose target device from list
3. **Wipe Method**: Select security standard
4. **Options**: Enable certificate generation
5. **Start Wipe**: Confirm and begin process
6. **Monitor Progress**: Watch real-time progress
7. **Download Certificate**: Get verification document

### 3. Wipe Methods
- **DoD 5220.22-M**: 3-pass military standard
- **NIST 800-88**: Government standard
- **Gutmann Method**: 35-pass maximum security
- **Single Pass**: Quick wipe
- **Random Data**: 3-pass random overwrite
- **Zero Overwrite**: Single zero pass

## Security Features

### Privilege Management
- Automatic privilege detection
- Elevated operation for device access
- Secure file handling

### Certificate Generation
- Digital signatures
- Cryptographic verification
- PDF and JSON formats
- Tamper-proof records

### Data Destruction
- Multiple overwrite passes
- Cryptographic verification
- Complete sector coverage
- HPA/DCO detection

## Troubleshooting

### Boot Issues
```bash
# If system doesn't boot
1. Check BIOS/UEFI settings
2. Enable legacy boot if needed
3. Try "Safe Mode" option
4. Verify ISO integrity
```

### Network Issues
```bash
# If browser doesn't open
1. Manually open browser
2. Navigate to http://localhost:3000
3. Check if backend is running
4. Review logs in /live/datawipe/logs/
```

### Wipe Issues
```bash
# If wipe fails
1. Check device permissions
2. Verify target device selection
3. Review error logs
4. Try different wipe method
```

## Advanced Configuration

### Custom Wipe Methods
Edit `bootable/bootable_main.py` to add custom methods:
```python
# Add to wipe service
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

## Distribution

### Creating Bootable USB
```bash
# Using dd (Linux/macOS)
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

## Security Considerations

### Physical Security
- Store bootable media securely
- Limit access to authorized personnel
- Document all wipe operations
- Maintain audit trails

### Operational Security
- Verify device selection before wiping
- Use appropriate wipe methods
- Generate certificates for all operations
- Maintain proper documentation

### Legal Compliance
- Follow organizational policies
- Comply with data protection regulations
- Maintain proper authorization
- Document all procedures

## Support

### Common Issues
1. **Boot fails**: Check BIOS settings and media integrity
2. **No devices found**: Verify hardware detection
3. **Wipe fails**: Check permissions and device status
4. **Certificate errors**: Verify file system permissions

### Getting Help
1. Check logs in `/live/datawipe/logs/`
2. Review system information at `/api/system`
3. Test with mock mode first
4. Contact support with error details

## Changelog

### Version 1.0.0
- Initial bootable system
- Complete offline operation
- Minimal web interface
- Multiple wipe standards
- Certificate generation
- Bootable ISO creation
