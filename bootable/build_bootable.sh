#!/bin/bash

echo "DataWipe Bootable Builder"
echo "========================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script requires root privileges for ISO creation."
    echo "Please run with sudo: sudo ./build_bootable.sh"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found"
    echo "Please run this script from the DataWipe project directory"
    exit 1
fi

echo "Project files found"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    grub-pc-bin \
    grub-efi-amd64-bin \
    xorriso \
    genisoimage \
    squashfs-tools \
    live-build \
    debootstrap

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install system dependencies"
    exit 1
fi

echo "System dependencies installed"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements-build.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies"
    exit 1
fi

echo "Python dependencies installed"
echo ""

# Create bootable ISO
echo "Creating bootable DataWipe ISO..."
python3 bootable/create_bootable.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create bootable ISO"
    exit 1
fi

echo ""
echo "Bootable DataWipe created successfully!"
echo ""
echo "Files created:"
ls -la bootable/
echo ""
echo "To create a bootable USB:"
echo "sudo dd if=bootable/DataWipe-Bootable.iso of=/dev/sdX bs=4M status=progress"
echo ""
echo "To burn to CD/DVD:"
echo "growisofs -dvd-compat -Z /dev/dvd=bootable/DataWipe-Bootable.iso"
echo ""
