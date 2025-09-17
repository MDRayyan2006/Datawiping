from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from services.storage_service import StorageDetectionService, StorageDevice

router = APIRouter()


# Pydantic models for request/response
class StorageDeviceResponse(BaseModel):
    device: str
    model: str
    size: int
    size_human: str
    partitions: List[Dict[str, Any]]
    device_type: str
    serial: Optional[str]
    hpa_present: bool
    dco_present: bool
    sector_size: int
    rotation_rate: Optional[int]
    temperature: Optional[float]
    health_status: Optional[str]
    raw_capacity: int
    raw_capacity_human: str
    detected_at: str

    class Config:
        from_attributes = True


class StorageSummaryResponse(BaseModel):
    total_devices: int
    total_capacity: int
    total_capacity_human: str
    device_types: Dict[str, int]
    hpa_devices: int
    dco_devices: int
    detected_at: str


@router.get("/devices", response_model=List[StorageDeviceResponse])
async def get_storage_devices(db: Session = Depends(get_db)):
    """
    Get information about all connected storage devices.
    
    Returns detailed information including:
    - Device model, size, and type (HDD/SSD/USB/NVMe)
    - Partition information
    - HPA/DCO presence
    - Health status and temperature
    - Serial numbers and sector sizes
    """
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        return [storage_service.to_dict(device) for device in devices]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect storage devices: {str(e)}"
        )


@router.get("/devices/{device_path:path}", response_model=StorageDeviceResponse)
async def get_storage_device(device_path: str, db: Session = Depends(get_db)):
    """
    Get information about a specific storage device.
    
    Args:
        device_path: Path to the device (e.g., /dev/sda, \\\\.\\PhysicalDrive0)
    """
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        # Find the specific device
        device = None
        for d in devices:
            if d.device == device_path or device_path in d.device:
                device = d
                break
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Storage device '{device_path}' not found"
            )
        
        return storage_service.to_dict(device)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device information: {str(e)}"
        )


@router.get("/summary", response_model=StorageSummaryResponse)
async def get_storage_summary(db: Session = Depends(get_db)):
    """
    Get a summary of all connected storage devices.
    
    Returns:
    - Total number of devices
    - Total capacity across all devices
    - Count by device type
    - Number of devices with HPA/DCO
    """
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        total_devices = len(devices)
        total_capacity = sum(device.size for device in devices)
        
        device_types = {}
        hpa_devices = 0
        dco_devices = 0
        
        for device in devices:
            # Count device types
            device_type = device.device_type
            device_types[device_type] = device_types.get(device_type, 0) + 1
            
            # Count HPA/DCO devices
            if device.hpa_present:
                hpa_devices += 1
            if device.dco_present:
                dco_devices += 1
        
        return StorageSummaryResponse(
            total_devices=total_devices,
            total_capacity=total_capacity,
            total_capacity_human=storage_service._format_size(total_capacity),
            device_types=device_types,
            hpa_devices=hpa_devices,
            dco_devices=dco_devices,
            detected_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate storage summary: {str(e)}"
        )


@router.get("/devices/by-type/{device_type}", response_model=List[StorageDeviceResponse])
async def get_devices_by_type(device_type: str, db: Session = Depends(get_db)):
    """
    Get storage devices filtered by type.
    
    Args:
        device_type: Type of device to filter by (HDD, SSD, USB, NVMe, etc.)
    """
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        filtered_devices = [
            device for device in devices 
            if device.device_type.lower() == device_type.lower()
        ]
        
        return [storage_service.to_dict(device) for device in filtered_devices]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter devices by type: {str(e)}"
        )


@router.get("/devices/with-hpa", response_model=List[StorageDeviceResponse])
async def get_devices_with_hpa(db: Session = Depends(get_db)):
    """Get all storage devices that have HPA (Host Protected Area) enabled."""
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        hpa_devices = [device for device in devices if device.hpa_present]
        
        return [storage_service.to_dict(device) for device in hpa_devices]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get devices with HPA: {str(e)}"
        )


@router.get("/devices/with-dco", response_model=List[StorageDeviceResponse])
async def get_devices_with_dco(db: Session = Depends(get_db)):
    """Get all storage devices that have DCO (Device Configuration Overlay) enabled."""
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        dco_devices = [device for device in devices if device.dco_present]
        
        return [storage_service.to_dict(device) for device in dco_devices]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get devices with DCO: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_storage_health(db: Session = Depends(get_db)):
    """
    Get health status of all storage devices.
    
    Returns devices grouped by health status and any warnings.
    """
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        health_groups = {}
        warnings = []
        
        for device in devices:
            health_status = device.health_status or "unknown"
            
            if health_status not in health_groups:
                health_groups[health_status] = []
            
            health_groups[health_status].append({
                'device': device.device,
                'model': device.model,
                'device_type': device.device_type
            })
            
            # Check for potential issues
            if device.hpa_present:
                warnings.append(f"Device {device.device} has HPA enabled")
            if device.dco_present:
                warnings.append(f"Device {device.device} has DCO enabled")
            if device.temperature and device.temperature > 60:
                warnings.append(f"Device {device.device} temperature is high: {device.temperature}°C")
        
        return {
            'health_groups': health_groups,
            'warnings': warnings,
            'total_devices': len(devices),
            'checked_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage health: {str(e)}"
        )


@router.post("/devices/{device_path:path}/refresh", response_model=StorageDeviceResponse)
async def refresh_device_info(device_path: str, db: Session = Depends(get_db)):
    """
    Refresh information for a specific storage device.
    
    This endpoint can be used to get updated information about a device
    without refreshing all devices.
    """
    try:
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        # Find the specific device
        device = None
        for d in devices:
            if d.device == device_path or device_path in d.device:
                device = d
                break
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Storage device '{device_path}' not found"
            )
        
        return storage_service.to_dict(device)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh device information: {str(e)}"
        )

