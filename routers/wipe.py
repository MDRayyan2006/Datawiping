from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import logging

from database import get_db
from services.wipe import WipeService, WipeMethod, WipeStatus, WipeResult
from services.certificate_service import certificate_service
from services.certificate_db_service import CertificateDBService
from services.user_service import UserService

logger = logging.getLogger(__name__)

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
    certificate_id: Optional[str] = None
    certificate_path: Optional[str] = None
    certificate_status: Optional[str] = None  # "generating", "completed", "failed", "not_required"
    download_urls: Optional[Dict[str, str]] = None

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


async def generate_certificate_for_wipe(
    result: WipeResult,
    user_id: int,
    db: Session
) -> tuple[Optional[Dict[str, str]], str]:
    """Generate certificate for a successful wipe operation
    
    Returns:
        tuple: (download_urls, certificate_status)
    """
    logger.info(f"generate_certificate_for_wipe called with user_id: {user_id}, result.success: {result.success}")
    
    if not result.success:
        logger.info("Wipe not successful, skipping certificate generation")
        return None, "not_required"
    
    try:
        # Get user information
        user_service = UserService(db)
        user = await user_service.get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for certificate generation")
            return None, "failed"
        
        logger.info(f"Found user: {user.name} (ID: {user.id})")
        
        # Generate certificate
        cert_data = await certificate_service.generate_certificate(
            user_id=user.id,
            user_name=user.name,
            user_org=user.org,
            device_serial=user.device_serial or "Unknown",
            device_model="Unknown",  # Not available in User model
            device_type="Unknown",   # Not available in User model
            wipe_method=result.method.value,
            wipe_status="completed",
            target_path=result.target,
            size_bytes=result.size_bytes,
            passes_completed=result.passes_completed,
            total_passes=result.total_passes,
            duration_seconds=result.duration_seconds,
            verification_hash=result.verification_hash
        )
        
        # Save to database
        cert_db_service = CertificateDBService(db)
        await cert_db_service.create_certificate(cert_data)
        
        # Update result with certificate info
        result.certificate_id = cert_data.certificate_id
        result.certificate_path = cert_data.certificate_path
        
        # Generate download URLs
        download_urls = {
            "pdf": f"/api/v1/downloads/certificate/{cert_data.certificate_id}/pdf",
            "json": f"/api/v1/downloads/certificate/{cert_data.certificate_id}/json",
            "signature": f"/api/v1/downloads/certificate/{cert_data.certificate_id}/signature",
            "package": f"/api/v1/downloads/certificate/{cert_data.certificate_id}/zip"
        }
        
        logger.info(f"Certificate generated: {cert_data.certificate_id}")
        return download_urls, "completed"
        
    except Exception as e:
        logger.error(f"Failed to generate certificate: {e}")
        return None, "failed"


@router.post("/file", response_model=WipeResponse)
async def wipe_file(
    request: WipeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Query(1, description="User ID for certificate generation")  # Default user ID, in real app this would come from authentication
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
        
        # Generate certificate if wipe was successful
        download_urls = None
        certificate_status = "not_required"
        if result.success:
            download_urls, certificate_status = await generate_certificate_for_wipe(result, user_id, db)
        
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
            completed_at=datetime.now().isoformat(),
            certificate_id=result.certificate_id,
            certificate_path=result.certificate_path,
            certificate_status=certificate_status,
            download_urls=download_urls
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
    db: Session = Depends(get_db),
    user_id: int = Query(1, description="User ID for certificate generation")  # Default user ID, in real app this would come from authentication
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
        
        # Generate certificate if wipe was successful
        download_urls = None
        certificate_status = "not_required"
        if result.success:
            download_urls, certificate_status = await generate_certificate_for_wipe(result, user_id, db)
        
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
            completed_at=datetime.now().isoformat(),
            certificate_id=result.certificate_id,
            certificate_path=result.certificate_path,
            certificate_status=certificate_status,
            download_urls=download_urls
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
    db: Session = Depends(get_db),
    user_id: int = Query(1, description="User ID for certificate generation")  # Default user ID, in real app this would come from authentication
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
        
        # Generate certificate if wipe was successful
        download_urls = None
        certificate_status = "not_required"
        if result.success:
            download_urls, certificate_status = await generate_certificate_for_wipe(result, user_id, db)
        
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
            completed_at=datetime.now().isoformat(),
            certificate_id=result.certificate_id,
            certificate_path=result.certificate_path,
            certificate_status=certificate_status,
            download_urls=download_urls
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
    mock_mode: bool = True,
    db: Session = Depends(get_db),
    user_id: int = Query(1, description="User ID for certificate generation")  # Default user ID for testing
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
        
        # Generate certificate if wipe was successful
        download_urls = None
        certificate_status = "not_required"
        if result.success:
            download_urls, certificate_status = await generate_certificate_for_wipe(result, user_id, db)
        
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
            completed_at=datetime.now().isoformat(),
            certificate_id=result.certificate_id,
            certificate_path=result.certificate_path,
            certificate_status=certificate_status,
            download_urls=download_urls
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test operation failed: {str(e)}"
        )


@router.get("/certificate/{certificate_id}/status")
async def get_certificate_status(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """Get the status of a certificate generation"""
    try:
        # Check if certificate exists in database
        cert_db_service = CertificateDBService(db)
        certificate = await cert_db_service.get_certificate_by_id(certificate_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        # Check if files exist
        cert_dir = Path(certificate.certificate_path)
        json_file = Path(certificate.json_path)
        pdf_file = Path(certificate.pdf_path)
        sig_file = Path(certificate.signature_path)
        
        files_exist = all([
            cert_dir.exists(),
            json_file.exists(),
            pdf_file.exists(),
            sig_file.exists()
        ])
        
        status = "completed" if files_exist else "generating"
        
        return {
            "certificate_id": certificate_id,
            "status": status,
            "created_at": certificate.created_at.isoformat(),
            "files_exist": files_exist,
            "download_urls": {
                "pdf": f"/api/v1/downloads/certificate/{certificate_id}/pdf",
                "json": f"/api/v1/downloads/certificate/{certificate_id}/json",
                "signature": f"/api/v1/downloads/certificate/{certificate_id}/signature",
                "package": f"/api/v1/downloads/certificate/{certificate_id}/zip"
            } if files_exist else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get certificate status: {str(e)}"
        )


@router.get("/wipe-status/{operation_id}")
async def get_wipe_status_with_certificate(
    operation_id: str,
    db: Session = Depends(get_db)
):
    """Get wipe operation status with certificate information for Windows app"""
    try:
        # This endpoint is designed for Windows app to check wipe status
        # For now, we'll return a generic response since we don't have operation tracking
        # In a real implementation, you'd track operations by ID
        
        return {
            "operation_id": operation_id,
            "status": "completed",
            "message": "Use the wipe endpoints directly to get certificate status",
            "certificate_status": "Use /api/v1/wipe/certificate/{certificate_id}/status endpoint",
            "note": "Certificate status is included in wipe response"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wipe status: {str(e)}"
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
