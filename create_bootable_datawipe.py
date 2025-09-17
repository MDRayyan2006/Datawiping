#!/usr/bin/env python3
"""
Complete Bootable DataWipe Creator
Creates a bootable ISO with DataWipe for offline system wipes.
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import argparse
import json
from datetime import datetime


class BootableDataWipeCreator:
    """Creates complete bootable DataWipe ISO"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.bootable_dir = self.project_root / "bootable"
        self.iso_dir = self.bootable_dir / "iso_build"
        self.temp_dir = None
        
    def check_requirements(self):
        """Check if all required tools are available"""
        print("🔍 Checking requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            return False
        
        print(f"✅ Python {sys.version.split()[0]} detected")
        
        # Check if main.py exists
        if not (self.project_root / "main.py").exists():
            print("❌ main.py not found")
            return False
        
        print("✅ Project files found")
        
        # Check for ISO creation tools
        tools = ['grub-mkrescue', 'xorriso', 'genisoimage']
        available_tools = [t for t in tools if shutil.which(t)]
        
        if not available_tools:
            print("⚠️  No ISO creation tools found")
            print("   Install one of: grub-mkrescue, xorriso, or genisoimage")
            return False
        
        print(f"✅ ISO creation tool found: {available_tools[0]}")
        return True
    
    def create_bootable_structure(self):
        """Create bootable ISO structure"""
        print("📁 Creating bootable ISO structure...")
        
        # Clean and create directories
        if self.iso_dir.exists():
            shutil.rmtree(self.iso_dir)
        
        directories = [
            "boot",
            "boot/grub",
            "live",
            "live/datawipe",
            "live/datawipe/backend",
            "live/datawipe/frontend",
            "live/datawipe/config",
            "live/datawipe/certificates",
            "live/datawipe/logs",
            "live/datawipe/scripts",
            "EFI/BOOT",
            "isolinux",
        ]
        
        for dir_path in directories:
            (self.iso_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        print("✅ Directory structure created")
    
    def copy_backend_files(self):
        """Copy backend files to ISO"""
        print("📦 Copying backend files...")
        
        backend_files = [
            "main.py",
            "database.py",
            "requirements.txt",
            "models/",
            "routers/",
            "services/",
            "utils/",
        ]
        
        for file_path in backend_files:
            src = self.project_root / file_path
            dst = self.iso_dir / "live/datawipe/backend" / file_path
            
            if src.is_file():
                shutil.copy2(src, dst)
            elif src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        
        # Copy bootable-specific main.py
        bootable_main = self.bootable_dir / "bootable_main.py"
        if bootable_main.exists():
            shutil.copy2(bootable_main, self.iso_dir / "live/datawipe/backend/main.py")
        
        print("✅ Backend files copied")
    
    def create_minimal_frontend(self):
        """Create minimal HTML frontend"""
        print("🌐 Creating minimal frontend...")
        
        # Create main HTML file
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataWipe - Secure System Wipe</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 2rem;
            max-width: 800px;
            width: 90%;
        }
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .header h1 {
            color: #333;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .header p {
            color: #666;
            font-size: 1.1rem;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 2rem;
            color: #856404;
        }
        .warning h3 {
            margin-bottom: 0.5rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #333;
        }
        select, input, textarea {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        select:focus, input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1.1rem;
            cursor: pointer;
            transition: background 0.3s;
            width: 100%;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .status {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 8px;
            display: none;
        }
        .status.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .status.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .status.info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }
        .progress {
            width: 100%;
            height: 20px;
            background: #e1e5e9;
            border-radius: 10px;
            overflow: hidden;
            margin: 1rem 0;
        }
        .progress-bar {
            height: 100%;
            background: #667eea;
            width: 0%;
            transition: width 0.3s;
        }
        .device-list {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 0.5rem;
        }
        .device-item {
            padding: 0.5rem;
            border-bottom: 1px solid #e1e5e9;
            cursor: pointer;
            transition: background 0.2s;
        }
        .device-item:hover {
            background: #f8f9fa;
        }
        .device-item.selected {
            background: #e3f2fd;
            border-color: #667eea;
        }
        .footer {
            text-align: center;
            margin-top: 2rem;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 DataWipe</h1>
            <p>Secure System Wipe Tool - Bootable Version</p>
        </div>
        
        <div class="warning">
            <h3>⚠️ WARNING</h3>
            <p>This tool will permanently destroy all data on selected drives. This action cannot be undone. Ensure you have backed up any important data before proceeding.</p>
        </div>
        
        <form id="wipeForm">
            <div class="form-group">
                <label for="userName">User Name:</label>
                <input type="text" id="userName" name="userName" required>
            </div>
            
            <div class="form-group">
                <label for="organization">Organization:</label>
                <input type="text" id="organization" name="organization" required>
            </div>
            
            <div class="form-group">
                <label for="deviceSerial">Device Serial:</label>
                <input type="text" id="deviceSerial" name="deviceSerial" required>
            </div>
            
            <div class="form-group">
                <label for="targetDevice">Target Device:</label>
                <div class="device-list" id="deviceList">
                    <div class="device-item">Loading devices...</div>
                </div>
            </div>
            
            <div class="form-group">
                <label for="wipeMethod">Wipe Method:</label>
                <select id="wipeMethod" name="wipeMethod" required>
                    <option value="dod_5220_22_m">DoD 5220.22-M (3 passes)</option>
                    <option value="nist_800_88">NIST 800-88 (1-3 passes)</option>
                    <option value="gutmann">Gutmann Method (35 passes)</option>
                    <option value="single_pass">Single Pass</option>
                    <option value="random_data">Random Data (3 passes)</option>
                    <option value="zero_overwrite">Zero Overwrite</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="generateCertificate" checked>
                    Generate Certificate
                </label>
            </div>
            
            <div class="form-group">
                <label for="notes">Notes (Optional):</label>
                <textarea id="notes" name="notes" rows="3"></textarea>
            </div>
            
            <button type="submit" class="btn" id="startBtn">Start Secure Wipe</button>
        </form>
        
        <div class="progress" id="progressContainer" style="display: none;">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        
        <div class="status" id="status"></div>
        
        <div class="footer">
            <p>DataWipe v1.0.0 - Secure Data Destruction Tool</p>
        </div>
    </div>
    
    <script>
        const API_BASE = 'http://localhost:8000/api/v1';
        let selectedDevice = null;
        
        // Load devices on page load
        document.addEventListener('DOMContentLoaded', loadDevices);
        
        async function loadDevices() {
            try {
                const response = await fetch(`${API_BASE}/devices/`);
                const devices = await response.json();
                
                const deviceList = document.getElementById('deviceList');
                deviceList.innerHTML = '';
                
                if (devices.length === 0) {
                    deviceList.innerHTML = '<div class="device-item">No devices found</div>';
                    return;
                }
                
                devices.forEach(device => {
                    const deviceItem = document.createElement('div');
                    deviceItem.className = 'device-item';
                    deviceItem.innerHTML = `
                        <strong>${device.model || device.device}</strong><br>
                        <small>${device.device_type} • ${device.size_human} • ${device.device}</small>
                    `;
                    deviceItem.onclick = () => selectDevice(device, deviceItem);
                    deviceList.appendChild(deviceItem);
                });
            } catch (error) {
                document.getElementById('deviceList').innerHTML = 
                    '<div class="device-item">Error loading devices</div>';
                showStatus('Error loading devices: ' + error.message, 'error');
            }
        }
        
        function selectDevice(device, element) {
            // Remove previous selection
            document.querySelectorAll('.device-item').forEach(item => {
                item.classList.remove('selected');
            });
            
            // Select new device
            element.classList.add('selected');
            selectedDevice = device;
        }
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }
        
        function updateProgress(percent) {
            const progressContainer = document.getElementById('progressContainer');
            const progressBar = document.getElementById('progressBar');
            
            progressContainer.style.display = 'block';
            progressBar.style.width = percent + '%';
        }
        
        document.getElementById('wipeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!selectedDevice) {
                showStatus('Please select a target device', 'error');
                return;
            }
            
            const formData = new FormData(e.target);
            const data = {
                user_id: 1, // Default user for bootable version
                target_path: selectedDevice.device,
                wipe_method: formData.get('wipeMethod'),
                generate_certificate: document.getElementById('generateCertificate').checked,
                mock_mode: false,
                notes: formData.get('notes')
            };
            
            // Register user first
            try {
                const userResponse = await fetch(`${API_BASE}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: formData.get('userName'),
                        org: formData.get('organization'),
                        device_serial: formData.get('deviceSerial')
                    })
                });
                
                if (!userResponse.ok) {
                    throw new Error('Failed to register user');
                }
                
                const user = await userResponse.json();
                data.user_id = user.id;
                
                // Start wipe job
                const jobResponse = await fetch(`${API_BASE}/jobs/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (!jobResponse.ok) {
                    throw new Error('Failed to start wipe job');
                }
                
                const job = await jobResponse.json();
                showStatus(`Wipe job started: ${job.job_id}`, 'info');
                
                // Monitor progress
                monitorJob(job.job_id);
                
            } catch (error) {
                showStatus('Error: ' + error.message, 'error');
            }
        });
        
        async function monitorJob(jobId) {
            const startBtn = document.getElementById('startBtn');
            startBtn.disabled = true;
            startBtn.textContent = 'Wipe in Progress...';
            
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`${API_BASE}/jobs/${jobId}/status`);
                    const status = await response.json();
                    
                    if (status.status === 'completed') {
                        clearInterval(interval);
                        updateProgress(100);
                        showStatus('Wipe completed successfully!', 'success');
                        startBtn.textContent = 'Wipe Completed';
                    } else if (status.status === 'failed') {
                        clearInterval(interval);
                        showStatus('Wipe failed: ' + (status.error_message || 'Unknown error'), 'error');
                        startBtn.disabled = false;
                        startBtn.textContent = 'Start Secure Wipe';
                    } else if (status.status === 'running') {
                        const progress = status.progress?.percent || 0;
                        updateProgress(progress);
                        showStatus(`Wipe in progress: ${status.progress_message || 'Processing...'}`, 'info');
                    }
                } catch (error) {
                    clearInterval(interval);
                    showStatus('Error monitoring job: ' + error.message, 'error');
                    startBtn.disabled = false;
                    startBtn.textContent = 'Start Secure Wipe';
                }
            }, 2000);
        }
    </script>
</body>
</html>'''
        
        # Write HTML file
        html_file = self.iso_dir / "live/datawipe/frontend/index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ Minimal frontend created")
    
    def create_boot_scripts(self):
        """Create boot and startup scripts"""
        print("📜 Creating boot scripts...")
        
        # Create GRUB configuration
        grub_cfg = '''set timeout=10
set default=0

menuentry "DataWipe - Secure System Wipe" {
    linux /live/vmlinuz boot=live quiet splash
    initrd /live/initrd.img
}

menuentry "DataWipe - Safe Mode" {
    linux /live/vmlinuz boot=live quiet splash acpi=off noapic
    initrd /live/initrd.img
}

menuentry "DataWipe - Memory Test" {
    linux /live/memtest86+ quiet
}'''
        
        grub_file = self.iso_dir / "boot/grub/grub.cfg"
        with open(grub_file, 'w') as f:
            f.write(grub_cfg)
        
        # Create startup script
        startup_script = '''#!/bin/bash
# DataWipe Bootable Startup Script

echo "Starting DataWipe Bootable System..."
echo "====================================="

# Mount the live filesystem
mount -t tmpfs tmpfs /tmp
mount -t proc proc /proc
mount -t sysfs sysfs /sys

# Set up networking
dhclient eth0 2>/dev/null || dhclient wlan0 2>/dev/null || echo "No network connection"

# Start DataWipe backend
cd /live/datawipe/backend
python3 main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start web server for frontend
cd /live/datawipe/frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

# Open browser
sleep 2
xdg-open http://localhost:3000 2>/dev/null || firefox http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"

# Keep system running
wait $BACKEND_PID'''
        
        startup_file = self.iso_dir / "live/datawipe/scripts/startup.sh"
        with open(startup_file, 'w') as f:
            f.write(startup_script)
        
        # Make executable
        os.chmod(startup_file, 0o755)
        
        print("✅ Boot scripts created")
    
    def create_iso(self, output_name="DataWipe-Bootable.iso"):
        """Create bootable ISO"""
        print("💿 Creating bootable ISO...")
        
        # Check if required tools are available
        tools = ['grub-mkrescue', 'xorriso', 'genisoimage']
        tool = None
        
        for t in tools:
            if shutil.which(t):
                tool = t
                break
        
        if not tool:
            print("❌ No ISO creation tool found. Please install grub-mkrescue, xorriso, or genisoimage")
            return False
        
        print(f"Using tool: {tool}")
        
        # Create ISO
        iso_path = self.bootable_dir / output_name
        
        try:
            if tool == 'grub-mkrescue':
                cmd = ['grub-mkrescue', '-o', str(iso_path), str(self.iso_dir)]
            elif tool == 'xorriso':
                cmd = ['xorriso', '-as', 'mkisofs', '-iso-level', '3', '-full-iso9660-filenames',
                       '-volid', 'DATAWIPE', '-appid', 'DataWipe Bootable',
                       '-publisher', 'DataWipe Team', '-preparer', 'DataWipe Creator',
                       '-eltorito-boot', 'boot/grub/stage2_eltorito', '-no-emul-boot',
                       '-boot-load-size', '4', '-boot-info-table', '-eltorito-catalog',
                       'boot/grub/boot.cat', '-output', str(iso_path), str(self.iso_dir)]
            else:  # genisoimage
                cmd = ['genisoimage', '-R', '-J', '-c', 'boot/boot.cat', '-b', 'boot/grub/stage2_eltorito',
                       '-no-emul-boot', '-boot-load-size', '4', '-boot-info-table',
                       '-o', str(iso_path), str(self.iso_dir)]
            
            subprocess.run(cmd, check=True)
            print(f"✅ Bootable ISO created: {iso_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create ISO: {e}")
            return False
    
    def create_build(self, output_name="DataWipe-Bootable.iso"):
        """Create complete bootable build"""
        print("🚀 Creating bootable DataWipe...")
        
        # Check requirements
        if not self.check_requirements():
            return False
        
        # Create structure
        self.create_bootable_structure()
        
        # Copy files
        self.copy_backend_files()
        self.create_minimal_frontend()
        self.create_boot_scripts()
        
        # Create ISO
        success = self.create_iso(output_name)
        
        if success:
            print("🎉 Bootable DataWipe created successfully!")
            print(f"📁 ISO file: {self.bootable_dir / output_name}")
            print("💿 Burn to CD/DVD or create bootable USB")
        
        return success


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Create bootable DataWipe ISO")
    parser.add_argument("--output", "-o", default="DataWipe-Bootable.iso", 
                       help="Output ISO filename")
    
    args = parser.parse_args()
    
    creator = BootableDataWipeCreator()
    success = creator.create_build(args.output)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
