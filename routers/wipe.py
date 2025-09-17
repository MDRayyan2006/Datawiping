from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database import get_db
from services.wipe import WipeService, WipeMethod, WipeStatus, WipeResult

router = APIRouter()


# Pydantic models for request/response
class WipeRequest(BaseModel):
    path: str = Field(..., description="Path to file, folder, or device to wipe")
    method: WipeMethod = Field(..., description="Wipe method to use")
    mock_mode: bool = Field(False, description="Enable mock mode for testing")


class WipeResponse(BaseModel):
    success: bool
    method: str
    target: str
    size_bytes: int
    size_human: str
    passes_completed: int
    total_passes: int
    duration_seconds: float
    error_message: Optional[str] = None
    verification_hash: Optional[str] = None
    mock_mode: bool
    completed_at: str

    class Config:
        from_attributes = True


class WipeStatusResponse(BaseModel):
    operation_id: str
    status: str
    target: str
    method: str
    started_at: str


class WipeSummaryResponse(BaseModel):
    total_operations: int
    active_operations: int
    completed_operations: int
    failed_operations: int
    mock_mode_enabled: bool
    supported_methods: List[str]


# Global wipe service instance
wipe_service = WipeService(mock_mode=False)


@router.post("/file", response_model=WipeResponse)
async def wipe_file(
    request: WipeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Securely wipe a single file using the specified method.
    
    Supported methods:
    - dod_5220_22_m: DoD 5220.22-M (3 passes)
    - nist_800_88: NIST 800-88 (1 pass)
    - single_pass: Single pass overwrite
    - gutmann: Gutmann method (35 passes)
    - random: Random data overwrite
    - zero: Zero overwrite
    """
    try:
        # Set mock mode if requested
        if request.mock_mode:
            wipe_service.set_mock_mode(True)
        
        result = await wipe_service.wipe_file(request.path, request.method)
        
        # Reset mock mode
        if request.mock_mode:
            wipe_service.set_mock_mode(False)
        
        return WipeResponse(
            success=result.success,
            method=result.method.value,
            target=result.target,
            size_bytes=result.size_bytes,
            size_human=_format_size(result.size_bytes),
            passes_completed=result.passes_completed,
            total_passes=result.total_passes,
            duration_seconds=result.duration_seconds,
            error_message=result.error_message,
            verification_hash=result.verification_hash,
            mock_mode=result.mock_mode,
            completed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to wipe file: {str(e)}"
        )


@router.post("/folder", response_model=WipeResponse)
async def wipe_folder(
    request: WipeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Securely wipe all files in a folder and remove the folder.
    
    This will recursively wipe all files in the specified folder
    using the chosen wipe method, then remove the folder structure.
    """
    try:
        # Set mock mode if requested
        if request.mock_mode:
            wipe_service.set_mock_mode(True)
        
        result = await wipe_service.wipe_folder(request.path, request.method)
        
        # Reset mock mode
        if request.mock_mode:
            wipe_service.set_mock_mode(False)
        
        return WipeResponse(
            success=result.success,
            method=result.method.value,
            target=result.target,
            size_bytes=result.size_bytes,
            size_human=_format_size(result.size_bytes),
            passes_completed=result.passes_completed,
            total_passes=result.total_passes,
            duration_seconds=result.duration_seconds,
            error_message=result.error_message,
            verification_hash=result.verification_hash,
            mock_mode=result.mock_mode,
            completed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to wipe folder: {str(e)}"
        )


@router.post("/drive", response_model=WipeResponse)
async def wipe_drive(
    request: WipeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Securely wipe an entire drive.
    
    WARNING: This will permanently destroy all data on the specified drive.
    Use with extreme caution and ensure you have the correct device path.
    
    Examples:
    - Linux: /dev/sda, /dev/nvme0n1
    - Windows: \\\\.\\PhysicalDrive0, \\\\.\\PhysicalDrive1
    """
    try:
        # Set mock mode if requested
        if request.mock_mode:
            wipe_service.set_mock_mode(True)
        
        result = await wipe_service.wipe_drive(request.path, request.method)
        
        # Reset mock mode
        if request.mock_mode:
            wipe_service.set_mock_mode(False)
        
        return WipeResponse(
            success=result.success,
            method=result.method.value,
            target=result.target,
            size_bytes=result.size_bytes,
            size_human=_format_size(result.size_bytes),
            passes_completed=result.passes_completed,
            total_passes=result.total_passes,
            duration_seconds=result.duration_seconds,
            error_message=result.error_message,
            verification_hash=result.verification_hash,
            mock_mode=result.mock_mode,
            completed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to wipe drive: {str(e)}"
        )


@router.get("/methods", response_model=List[Dict[str, Any]])
async def get_wipe_methods():
    """Get information about all supported wipe methods"""
    methods = [
        {
            "name": "dod_5220_22_m",
            "display_name": "DoD 5220.22-M",
            "description": "Department of Defense standard (3 passes: 0x00, 0xFF, 0x00)",
            "passes": 3,
            "standard": "DoD 5220.22-M",
            "recommended_for": "Sensitive government data"
        },
        {
            "name": "nist_800_88",
            "display_name": "NIST 800-88",
            "description": "National Institute of Standards and Technology standard (1 pass with zeros)",
            "passes": 1,
            "standard": "NIST 800-88",
            "recommended_for": "General business data"
        },
        {
            "name": "single_pass",
            "display_name": "Single Pass",
            "description": "Single pass overwrite with zeros",
            "passes": 1,
            "standard": "Custom",
            "recommended_for": "Quick deletion"
        },
        {
            "name": "gutmann",
            "display_name": "Gutmann Method",
            "description": "35-pass secure deletion method",
            "passes": 35,
            "standard": "Gutmann",
            "recommended_for": "Highly sensitive data"
        },
        {
            "name": "random",
            "display_name": "Random Data",
            "description": "Single pass with random data",
            "passes": 1,
            "standard": "Custom",
            "recommended_for": "General purpose"
        },
        {
            "name": "zero",
            "display_name": "Zero Overwrite",
            "description": "Single pass with zeros",
            "passes": 1,
            "standard": "Custom",
            "recommended_for": "Basic deletion"
        }
    ]
    return methods


@router.get("/status", response_model=WipeSummaryResponse)
async def get_wipe_status():
    """Get current status of wipe operations"""
    active_ops = wipe_service.get_active_operations()
    
    return WipeSummaryResponse(
        total_operations=len(active_ops),
        active_operations=len([op for op in active_ops.values() if op == WipeStatus.IN_PROGRESS]),
        completed_operations=len([op for op in active_ops.values() if op == WipeStatus.COMPLETED]),
        failed_operations=len([op for op in active_ops.values() if op == WipeStatus.FAILED]),
        mock_mode_enabled=wipe_service.mock_mode,
        supported_methods=[method.value for method in WipeMethod]
    )


@router.get("/operations", response_model=List[WipeStatusResponse])
async def get_active_operations():
    """Get list of currently active wipe operations"""
    active_ops = wipe_service.get_active_operations()
    
    operations = []
    for op_id, status in active_ops.items():
        operations.append(WipeStatusResponse(
            operation_id=op_id,
            status=status.value,
            target="Unknown",  # Would need to track this in real implementation
            method="Unknown",  # Would need to track this in real implementation
            started_at=datetime.now().isoformat()
        ))
    
    return operations


@router.post("/operations/{operation_id}/cancel")
async def cancel_operation(operation_id: str):
    """Cancel an active wipe operation"""
    success = wipe_service.cancel_operation(operation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operation not found or already completed"
        )
    
    return {"message": f"Operation {operation_id} cancelled successfully"}


@router.post("/mock-mode")
async def set_mock_mode(enabled: bool):
    """Enable or disable mock mode for testing"""
    wipe_service.set_mock_mode(enabled)
    return {"message": f"Mock mode {'enabled' if enabled else 'disabled'}"}


@router.get("/mock-mode")
async def get_mock_mode():
    """Get current mock mode status"""
    return {"mock_mode_enabled": wipe_service.mock_mode}


@router.post("/test")
async def test_wipe_operation(
    method: WipeMethod = WipeMethod.SINGLE_PASS,
    mock_mode: bool = True
):
    """Test wipe operation with a temporary file"""
    import tempfile
    import os
    
    try:
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".test") as temp_file:
            temp_file.write(b"Test data for wiping")
            temp_path = temp_file.name
        
        # Set mock mode
        if mock_mode:
            wipe_service.set_mock_mode(True)
        
        # Perform wipe
        result = await wipe_service.wipe_file(temp_path, method)
        
        # Reset mock mode
        if mock_mode:
            wipe_service.set_mock_mode(False)
        
        # Clean up if not in mock mode
        if not mock_mode and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return WipeResponse(
            success=result.success,
            method=result.method.value,
            target=result.target,
            size_bytes=result.size_bytes,
            size_human=_format_size(result.size_bytes),
            passes_completed=result.passes_completed,
            total_passes=result.total_passes,
            duration_seconds=result.duration_seconds,
            error_message=result.error_message,
            verification_hash=result.verification_hash,
            mock_mode=result.mock_mode,
            completed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test operation failed: {str(e)}"
        )


def _format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
