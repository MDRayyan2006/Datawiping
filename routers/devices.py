from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database import get_db
from services.storage_service import StorageDetectionService
from models.user import User
from services.user_service import UserService, UserUpdate

router = APIRouter()


# Pydantic models for request/response
class DeviceInfo(BaseModel):
    device: str
    model: str
    size: int
    size_human: str
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
    is_registered: bool
    registered_user: Optional[str]
    registered_org: Optional[str]
    detected_at: str

    class Config:
        from_attributes = True


class DeviceSummary(BaseModel):
    total_devices: int
    registered_devices: int
    unregistered_devices: int
    device_types: Dict[str, int]
    hpa_devices: int
    dco_devices: int
    total_capacity: int
    total_capacity_human: str
    detected_at: str


class DeviceRegistrationRequest(BaseModel):
    device_serial: str = Field(..., description="Device serial number to register")
    user_id: int = Field(..., description="User ID to associate with device")


@router.get("/", response_model=List[DeviceInfo])
async def list_devices(
    include_registered: bool = Query(True, description="Include registered devices"),
    include_unregistered: bool = Query(True, description="Include unregistered devices"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    db: Session = Depends(get_db)
):
    """
    List all detected storage devices with registration status.
    
    This endpoint combines storage detection with user registration information
    to provide a comprehensive view of all devices and their ownership status.
    """
    try:
        # Get storage devices
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        # Get registered devices
        user_service = UserService(db)
        all_users = await user_service.get_users()
        registered_serials = {user.device_serial: user for user in all_users}
        
        result = []
        for device in devices:
            # Check if device is registered
            is_registered = False
            registered_user = None
            registered_org = None
            
            if device.serial and device.serial in registered_serials:
                is_registered = True
                user = registered_serials[device.serial]
                registered_user = user.name
                registered_org = user.org
            
            # Apply filters
            if not include_registered and is_registered:
                continue
            if not include_unregistered and not is_registered:
                continue
            if device_type and device.device_type.lower() != device_type.lower():
                continue
            
            device_info = DeviceInfo(
                device=device.device,
                model=device.model,
                size=device.size,
                size_human=storage_service._format_size(device.size),
                device_type=device.device_type,
                serial=device.serial,
                hpa_present=device.hpa_present,
                dco_present=device.dco_present,
                sector_size=device.sector_size,
                rotation_rate=device.rotation_rate,
                temperature=device.temperature,
                health_status=device.health_status,
                raw_capacity=device.raw_capacity,
                raw_capacity_human=storage_service._format_size(device.raw_capacity),
                is_registered=is_registered,
                registered_user=registered_user,
                registered_org=registered_org,
                detected_at=datetime.now().isoformat()
            )
            result.append(device_info)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list devices: {str(e)}"
        )


@router.get("/summary", response_model=DeviceSummary)
async def get_device_summary(db: Session = Depends(get_db)):
    """Get summary statistics of all detected devices"""
    try:
        # Get storage devices
        storage_service = StorageDetectionService()
        devices = await storage_service.get_all_storage_devices()
        
        # Get registered devices
        user_service = UserService(db)
        all_users = await user_service.get_users()
        registered_serials = {user.device_serial for user in all_users}
        
        total_devices = len(devices)
        registered_devices = 0
        unregistered_devices = 0
        device_types = {}
        hpa_devices = 0
        dco_devices = 0
        total_capacity = 0
        
        for device in devices:
            # Count registered/unregistered
            is_registered = device.serial and device.serial in registered_serials
            if is_registered:
                registered_devices += 1
            else:
                unregistered_devices += 1
            
            # Count device types
            device_type = device.device_type
            device_types[device_type] = device_types.get(device_type, 0) + 1
            
            # Count HPA/DCO devices
            if device.hpa_present:
                hpa_devices += 1
            if device.dco_present:
                dco_devices += 1
            
            # Sum capacity
            total_capacity += device.size
        
        return DeviceSummary(
            total_devices=total_devices,
            registered_devices=registered_devices,
            unregistered_devices=unregistered_devices,
            device_types=device_types,
            hpa_devices=hpa_devices,
            dco_devices=dco_devices,
            total_capacity=total_capacity,
            total_capacity_human=storage_service._format_size(total_capacity),
            detected_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device summary: {str(e)}"
        )


@router.get("/registered", response_model=List[DeviceInfo])
async def get_registered_devices(db: Session = Depends(get_db)):
    """Get only registered devices"""
    return await list_devices(include_registered=True, include_unregistered=False, db=db)


@router.get("/unregistered", response_model=List[DeviceInfo])
async def get_unregistered_devices(db: Session = Depends(get_db)):
    """Get only unregistered devices"""
    return await list_devices(include_registered=False, include_unregistered=True, db=db)


@router.get("/by-type/{device_type}", response_model=List[DeviceInfo])
async def get_devices_by_type(
    device_type: str,
    db: Session = Depends(get_db)
):
    """Get devices filtered by type"""
    return await list_devices(device_type=device_type, db=db)


@router.get("/{device_serial}", response_model=DeviceInfo)
async def get_device_by_serial(device_serial: str, db: Session = Depends(get_db)):
    """Get specific device by serial number"""
    try:
        # Get all devices
        devices = await list_devices(db=db)
        
        # Find device by serial
        for device in devices:
            if device.serial == device_serial:
                return device
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with serial '{device_serial}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device: {str(e)}"
        )


@router.post("/register", response_model=Dict[str, Any])
async def register_device(
    request: DeviceRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a device with a user"""
    try:
        # Check if device exists
        devices = await list_devices(db=db)
        device_found = False
        device_info = None
        
        for device in devices:
            if device.serial == request.device_serial:
                device_found = True
                device_info = device
                break
        
        if not device_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device with serial '{request.device_serial}' not found"
            )
        
        if device_info.is_registered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device '{request.device_serial}' is already registered"
            )
        
        # Check if user exists
        user_service = UserService(db)
        user = await user_service.get_user(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user's device serial
        user_data = UserUpdate(device_serial=request.device_serial)
        updated_user = await user_service.update_user(request.user_id, user_data)
        
        return {
            "message": f"Device '{request.device_serial}' registered successfully",
            "user_id": updated_user.id,
            "user_name": updated_user.name,
            "device_serial": updated_user.device_serial,
            "device_model": device_info.model,
            "device_type": device_info.device_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register device: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_device_health(db: Session = Depends(get_db)):
    """Get health status of all devices"""
    try:
        devices = await list_devices(db=db)
        
        health_groups = {}
        warnings = []
        
        for device in devices:
            health_status = device.health_status or "unknown"
            
            if health_status not in health_groups:
                health_groups[health_status] = []
            
            health_groups[health_status].append({
                "device": device.device,
                "model": device.model,
                "device_type": device.device_type,
                "serial": device.serial,
                "is_registered": device.is_registered,
                "registered_user": device.registered_user
            })
            
            # Check for potential issues
            if device.hpa_present:
                warnings.append(f"Device {device.device} has HPA enabled")
            if device.dco_present:
                warnings.append(f"Device {device.device} has DCO enabled")
            if device.temperature and device.temperature > 60:
                warnings.append(f"Device {device.device} temperature is high: {device.temperature}°C")
        
        return {
            "health_groups": health_groups,
            "warnings": warnings,
            "total_devices": len(devices),
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device health: {str(e)}"
        )
