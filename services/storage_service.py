import psutil
import subprocess
import platform
import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import os


@dataclass
class PartitionInfo:
    """Information about a disk partition"""
    device: str
    mountpoint: str
    fstype: str
    size: int
    used: int
    free: int


@dataclass
class StorageDevice:
    """Information about a storage device"""
    device: str
    model: str
    size: int
    partitions: List[PartitionInfo]
    device_type: str  # HDD, SSD, USB, NVMe, etc.
    serial: Optional[str]
    hpa_present: bool
    dco_present: bool
    sector_size: int
    rotation_rate: Optional[int]  # RPM for HDDs, None for SSDs
    temperature: Optional[float]  # Celsius
    health_status: Optional[str]
    raw_capacity: int  # Raw capacity before HPA/DCO adjustments


class StorageDetectionService:
    """Service for detecting and analyzing storage devices"""
    
    def __init__(self):
        self.system = platform.system().lower()
    
    async def get_all_storage_devices(self) -> List[StorageDevice]:
        """Get information about all connected storage devices"""
        devices = []
        
        try:
            # Get basic disk information from psutil
            disk_partitions = psutil.disk_partitions()
            disk_usage = {p.mountpoint: psutil.disk_usage(p.mountpoint) for p in disk_partitions}
            
            # Get physical disk information
            if self.system == "windows":
                devices = await self._detect_windows_devices(disk_partitions, disk_usage)
            elif self.system == "linux":
                devices = await self._detect_linux_devices(disk_partitions, disk_usage)
            else:
                devices = await self._detect_generic_devices(disk_partitions, disk_usage)
                
        except Exception as e:
            print(f"Error detecting storage devices: {e}")
            
        return devices
    
    async def _detect_windows_devices(self, disk_partitions: List, disk_usage: Dict) -> List[StorageDevice]:
        """Detect storage devices on Windows using PowerShell"""
        devices = []
        
        try:
            # Use PowerShell to get physical disk information
            wmi_info = await self._get_wmi_disk_info()
            
            # Use PowerShell to get additional information
            diskpart_info = await self._get_diskpart_info()
            
            # If we have physical disk info, create devices based on that
            if wmi_info:
                for disk_letter, wmi_data in wmi_info.items():
                    diskpart_data = diskpart_info.get(disk_letter, {})
                    
                    # Get partitions for this physical disk
                    partitions = []
                    for partition in disk_partitions:
                        # For now, associate all partitions with the first physical disk
                        # In a more sophisticated implementation, you'd map partitions to physical disks
                        if not partitions:  # Only add partitions to the first disk for now
                            partition_info = PartitionInfo(
                                device=partition.device,
                                mountpoint=partition.mountpoint,
                                fstype=partition.fstype or "unknown",
                                size=disk_usage.get(partition.mountpoint, (0, 0, 0))[2],  # total
                                used=disk_usage.get(partition.mountpoint, (0, 0, 0))[1],  # used
                                free=disk_usage.get(partition.mountpoint, (0, 0, 0))[0]   # free
                            )
                            partitions.append(partition_info)
                    
                    device = StorageDevice(
                        device=f"\\\\.\\PhysicalDrive{disk_letter}",
                        model=wmi_data.get('model', 'Unknown'),
                        size=wmi_data.get('size', 0),
                        partitions=partitions,
                        device_type=self._determine_device_type(wmi_data.get('model', ''), wmi_data.get('interface', '')),
                        serial=wmi_data.get('serial', None),
                        hpa_present=diskpart_data.get('hpa_present', False),
                        dco_present=diskpart_data.get('dco_present', False),
                        sector_size=wmi_data.get('sector_size', 512),
                        rotation_rate=wmi_data.get('rotation_rate', None),
                        temperature=wmi_data.get('temperature', None),
                        health_status=wmi_data.get('health_status', None),
                        raw_capacity=diskpart_data.get('raw_capacity', wmi_data.get('size', 0))
                    )
                    devices.append(device)
            else:
                # Fallback: create devices from partitions if no physical disk info
                disk_groups = {}
                for partition in disk_partitions:
                    disk_letter = partition.device[0]  # e.g., 'C' from 'C:\\'
                    if disk_letter not in disk_groups:
                        disk_groups[disk_letter] = []
                    
                    partition_info = PartitionInfo(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        fstype=partition.fstype or "unknown",
                        size=disk_usage.get(partition.mountpoint, (0, 0, 0))[2],  # total
                        used=disk_usage.get(partition.mountpoint, (0, 0, 0))[1],  # used
                        free=disk_usage.get(partition.mountpoint, (0, 0, 0))[0]   # free
                    )
                    disk_groups[disk_letter].append(partition_info)
                
                # Create StorageDevice objects from partition groups
                for disk_letter, partitions in disk_groups.items():
                    device = StorageDevice(
                        device=f"\\\\.\\PhysicalDrive{disk_letter}",
                        model="Unknown",
                        size=sum(p.size for p in partitions),
                        partitions=partitions,
                        device_type="Unknown",
                        serial=None,
                        hpa_present=False,
                        dco_present=False,
                        sector_size=512,
                        rotation_rate=None,
                        temperature=None,
                        health_status=None,
                        raw_capacity=sum(p.size for p in partitions)
                    )
                    devices.append(device)
                
        except Exception as e:
            print(f"Error in Windows device detection: {e}")
            
        return devices
    
    async def _detect_linux_devices(self, disk_partitions: List, disk_usage: Dict) -> List[StorageDevice]:
        """Detect storage devices on Linux using lsblk and hdparm"""
        devices = []
        
        try:
            # Get block device information using lsblk
            lsblk_info = await self._get_lsblk_info()
            
            # Get HPA/DCO information using hdparm
            hdparm_info = await self._get_hdparm_info()
            
            # Group partitions by physical disk
            disk_groups = {}
            for partition in disk_partitions:
                # Extract device name (e.g., /dev/sda1 -> /dev/sda)
                device_path = partition.device
                if '/dev/' in device_path:
                    base_device = re.sub(r'\d+$', '', device_path)  # Remove partition number
                    if base_device not in disk_groups:
                        disk_groups[base_device] = []
                    
                    partition_info = PartitionInfo(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        fstype=partition.fstype or "unknown",
                        size=disk_usage.get(partition.mountpoint, (0, 0, 0))[2],
                        used=disk_usage.get(partition.mountpoint, (0, 0, 0))[1],
                        free=disk_usage.get(partition.mountpoint, (0, 0, 0))[0]
                    )
                    disk_groups[base_device].append(partition_info)
            
            # Create StorageDevice objects
            for device_path, partitions in disk_groups.items():
                lsblk_data = lsblk_info.get(device_path, {})
                hdparm_data = hdparm_info.get(device_path, {})
                
                device = StorageDevice(
                    device=device_path,
                    model=lsblk_data.get('model', 'Unknown'),
                    size=lsblk_data.get('size', 0),
                    partitions=partitions,
                    device_type=self._determine_device_type(lsblk_data.get('model', ''), lsblk_data.get('tran', '')),
                    serial=lsblk_data.get('serial', None),
                    hpa_present=hdparm_data.get('hpa_present', False),
                    dco_present=hdparm_data.get('dco_present', False),
                    sector_size=lsblk_data.get('sector_size', 512),
                    rotation_rate=lsblk_data.get('rotation_rate', None),
                    temperature=lsblk_data.get('temperature', None),
                    health_status=lsblk_data.get('health_status', None),
                    raw_capacity=hdparm_data.get('raw_capacity', lsblk_data.get('size', 0))
                )
                devices.append(device)
                
        except Exception as e:
            print(f"Error in Linux device detection: {e}")
            
        return devices
    
    async def _detect_generic_devices(self, disk_partitions: List, disk_usage: Dict) -> List[StorageDevice]:
        """Generic device detection for unsupported platforms"""
        devices = []
        
        for partition in disk_partitions:
            device = StorageDevice(
                device=partition.device,
                model="Unknown",
                size=disk_usage.get(partition.mountpoint, (0, 0, 0))[2],
                partitions=[PartitionInfo(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    fstype=partition.fstype or "unknown",
                    size=disk_usage.get(partition.mountpoint, (0, 0, 0))[2],
                    used=disk_usage.get(partition.mountpoint, (0, 0, 0))[1],
                    free=disk_usage.get(partition.mountpoint, (0, 0, 0))[0]
                )],
                device_type="Unknown",
                serial=None,
                hpa_present=False,
                dco_present=False,
                sector_size=512,
                rotation_rate=None,
                temperature=None,
                health_status=None,
                raw_capacity=disk_usage.get(partition.mountpoint, (0, 0, 0))[2]
            )
            devices.append(device)
            
        return devices
    
    async def _get_wmi_disk_info(self) -> Dict[str, Dict]:
        """Get disk information using PowerShell on Windows"""
        wmi_info = {}
        
        try:
            # Use a simpler approach with direct PowerShell command
            cmd = 'powershell -Command "Get-CimInstance -ClassName Win32_DiskDrive | Select-Object Model, Size, SerialNumber, InterfaceType, BytesPerSector, Status | ConvertTo-Json"'
            result = await self._run_command(cmd)
            
            print(f"PowerShell disk info - Return code: {result.returncode}")
            print(f"PowerShell disk info - Stdout length: {len(result.stdout)}")
            print(f"PowerShell disk info - Stderr: {result.stderr}")
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    # Parse JSON output
                    data = json.loads(result.stdout.strip())
                    
                    # Handle both single object and array
                    if isinstance(data, dict):
                        data = [data]
                    
                    for i, disk in enumerate(data):
                        disk_letter = chr(ord('A') + i)  # Assign letters A, B, C, etc.
                        wmi_info[disk_letter] = {
                            'model': disk.get('Model', 'Unknown').strip(),
                            'size': int(disk.get('Size', 0)) if disk.get('Size') else 0,
                            'serial': disk.get('SerialNumber', '').strip() if disk.get('SerialNumber') else None,
                            'interface': disk.get('InterfaceType', 'Unknown').strip(),
                            'sector_size': int(disk.get('BytesPerSector', 512)) if disk.get('BytesPerSector') else 512,
                            'health_status': disk.get('Status', 'Unknown').strip()
                        }
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing PowerShell JSON output: {e}")
                    print(f"Raw output: {result.stdout}")
                    
        except Exception as e:
            print(f"Error getting WMI disk info: {e}")
            
        return wmi_info
    
    async def _get_diskpart_info(self) -> Dict[str, Dict]:
        """Get HPA/DCO information using PowerShell on Windows"""
        diskpart_info = {}
        
        try:
            # Use a simpler approach with direct PowerShell command
            cmd = 'powershell -Command "Get-Disk | Select-Object Number, FriendlyName, Size, PartitionStyle | ConvertTo-Json"'
            result = await self._run_command(cmd)
            
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    # Parse JSON output
                    data = json.loads(result.stdout.strip())
                    
                    # Handle both single object and array
                    if isinstance(data, dict):
                        data = [data]
                    
                    for i, disk in enumerate(data):
                        disk_letter = chr(ord('A') + i)
                        
                        # For now, assume no HPA/DCO (this would need more sophisticated detection)
                        # In a real implementation, you'd use tools like hdparm or specific Windows APIs
                        diskpart_info[disk_letter] = {
                            'hpa_present': False,  # Would need specific detection
                            'dco_present': False,  # Would need specific detection
                            'raw_capacity': int(disk.get('Size', 0)) if disk.get('Size') else 0
                        }
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing PowerShell disk info: {e}")
                    print(f"Raw output: {result.stdout}")
                    
        except Exception as e:
            print(f"Error getting diskpart info: {e}")
            
        return diskpart_info
    
    async def _get_lsblk_info(self) -> Dict[str, Dict]:
        """Get block device information using lsblk on Linux"""
        lsblk_info = {}
        
        try:
            # Get detailed block device information
            result = await self._run_command("lsblk -J -o NAME,MODEL,SIZE,SERIAL,TRAN,ROTA,PHY-SEC,STATE")
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for device in data.get('blockdevices', []):
                    device_path = f"/dev/{device['name']}"
                    lsblk_info[device_path] = {
                        'model': device.get('model', 'Unknown'),
                        'size': self._parse_size(device.get('size', '0')),
                        'serial': device.get('serial', None),
                        'tran': device.get('tran', ''),
                        'rotation_rate': int(device.get('rota', 0)) if device.get('rota') else None,
                        'sector_size': int(device.get('phy-sec', 512)),
                        'health_status': device.get('state', 'unknown')
                    }
        except Exception as e:
            print(f"Error getting lsblk info: {e}")
            
        return lsblk_info
    
    async def _get_hdparm_info(self) -> Dict[str, Dict]:
        """Get HPA/DCO information using hdparm on Linux"""
        hdparm_info = {}
        
        try:
            # Get list of block devices
            result = await self._run_command("lsblk -d -n -o NAME")
            
            if result.returncode == 0:
                devices = result.stdout.strip().split('\n')
                
                for device_name in devices:
                    if device_name.strip():
                        device_path = f"/dev/{device_name.strip()}"
                        
                        # Check for HPA
                        hpa_result = await self._run_command(f"hdparm -N {device_path}")
                        hpa_present = "HPA is enabled" in hpa_result.stdout
                        
                        # Check for DCO
                        dco_result = await self._run_command(f"hdparm -d {device_path}")
                        dco_present = "DCO" in dco_result.stdout
                        
                        # Get raw capacity
                        raw_capacity = 0
                        if hpa_present:
                            # Extract HPA capacity
                            hpa_match = re.search(r'max sectors = (\d+)', hpa_result.stdout)
                            if hpa_match:
                                raw_capacity = int(hpa_match.group(1)) * 512  # Assuming 512-byte sectors
                        
                        hdparm_info[device_path] = {
                            'hpa_present': hpa_present,
                            'dco_present': dco_present,
                            'raw_capacity': raw_capacity
                        }
                        
        except Exception as e:
            print(f"Error getting hdparm info: {e}")
            
        return hdparm_info
    
    def _determine_device_type(self, model: str, interface: str) -> str:
        """Determine device type based on model and interface"""
        model_lower = model.lower()
        interface_lower = interface.lower()
        
        if 'nvme' in model_lower or 'nvme' in interface_lower:
            return 'NVMe'
        elif 'ssd' in model_lower:
            return 'SSD'
        elif 'usb' in model_lower or 'usb' in interface_lower:
            return 'USB'
        elif 'hdd' in model_lower or 'hard' in model_lower:
            return 'HDD'
        elif 'sata' in interface_lower:
            return 'SATA'
        elif 'scsi' in interface_lower:
            return 'SCSI'
        else:
            return 'Unknown'
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '500G', '1T') to bytes"""
        if not size_str:
            return 0
            
        size_str = size_str.upper().strip()
        multipliers = {
            'K': 1024,
            'M': 1024 * 1024,
            'G': 1024 * 1024 * 1024,
            'T': 1024 * 1024 * 1024 * 1024
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    return int(float(size_str[:-1]) * multiplier)
                except ValueError:
                    pass
                    
        try:
            return int(size_str)
        except ValueError:
            return 0
    
    async def _run_command(self, command: str) -> subprocess.CompletedProcess:
        """Run a system command asynchronously"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout.decode('utf-8', errors='ignore'),
                stderr=stderr.decode('utf-8', errors='ignore')
            )
        except Exception as e:
            print(f"Error running command '{command}': {e}")
            return subprocess.CompletedProcess(
                args=command,
                returncode=1,
                stdout="",
                stderr=str(e)
            )
    
    def to_dict(self, device: StorageDevice) -> Dict[str, Any]:
        """Convert StorageDevice to dictionary for JSON serialization"""
        return {
            'device': device.device,
            'model': device.model,
            'size': device.size,
            'size_human': self._format_size(device.size),
            'partitions': [
                {
                    'device': p.device,
                    'mountpoint': p.mountpoint,
                    'fstype': p.fstype,
                    'size': p.size,
                    'size_human': self._format_size(p.size),
                    'used': p.used,
                    'used_human': self._format_size(p.used),
                    'free': p.free,
                    'free_human': self._format_size(p.free)
                }
                for p in device.partitions
            ],
            'device_type': device.device_type,
            'serial': device.serial,
            'hpa_present': device.hpa_present,
            'dco_present': device.dco_present,
            'sector_size': device.sector_size,
            'rotation_rate': device.rotation_rate,
            'temperature': device.temperature,
            'health_status': device.health_status,
            'raw_capacity': device.raw_capacity,
            'raw_capacity_human': self._format_size(device.raw_capacity),
            'detected_at': datetime.now().isoformat()
        }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}"

