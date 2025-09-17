from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.certificate import WipeCertificate
from services.certificate_service import certificate_service
from services.certificate_db_service import CertificateDBService

router = APIRouter()


# Pydantic models for request/response
class CertificateResponse(BaseModel):
    id: int
    certificate_id: str
    user_id: int
    user_name: str
    user_org: str
    device_serial: str
    device_model: str
    device_type: str
    wipe_method: str
    wipe_status: str
    target_path: str
    size_bytes: int
    size_human: str
    passes_completed: int
    total_passes: int
    duration_seconds: int
    verification_hash: Optional[str]
    certificate_path: str
    json_path: str
    pdf_path: str
    signature_path: str
    is_valid: bool
    is_verified: bool
    verified_at: Optional[datetime]
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class CertificateVerificationResponse(BaseModel):
    valid: bool
    certificate_id: Optional[str] = None
    verified_at: Optional[str] = None
    algorithm: Optional[str] = None
    key_size: Optional[int] = None
    error: Optional[str] = None


class CertificateStatsResponse(BaseModel):
    total_certificates: int
    valid_certificates: int
    verified_certificates: int
    expired_certificates: int
    invalid_certificates: int


class CertificateSearchRequest(BaseModel):
    query: Optional[str] = None
    user_id: Optional[int] = None
    device_serial: Optional[str] = None
    org: Optional[str] = None
    wipe_method: Optional[str] = None
    is_valid: Optional[bool] = None
    is_verified: Optional[bool] = None
    skip: int = 0
    limit: int = 100


@router.get("/", response_model=List[CertificateResponse])
async def get_certificates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all certificates with pagination"""
    cert_db_service = CertificateDBService(db)
    certificates = await cert_db_service.get_all_certificates(skip=skip, limit=limit)
    
    return [_format_certificate_response(cert) for cert in certificates]


@router.get("/{certificate_id}", response_model=CertificateResponse)
async def get_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """Get a specific certificate by ID"""
    cert_db_service = CertificateDBService(db)
    certificate = await cert_db_service.get_certificate(certificate_id)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return _format_certificate_response(certificate)


@router.get("/user/{user_id}", response_model=List[CertificateResponse])
async def get_certificates_by_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get certificates for a specific user"""
    cert_db_service = CertificateDBService(db)
    certificates = await cert_db_service.get_certificates_by_user(
        user_id=user_id, skip=skip, limit=limit
    )
    
    return [_format_certificate_response(cert) for cert in certificates]


@router.get("/device/{device_serial}", response_model=List[CertificateResponse])
async def get_certificates_by_device(device_serial: str, db: Session = Depends(get_db)):
    """Get certificates for a specific device"""
    cert_db_service = CertificateDBService(db)
    certificates = await cert_db_service.get_certificates_by_device(device_serial)
    
    return [_format_certificate_response(cert) for cert in certificates]


@router.get("/org/{org}", response_model=List[CertificateResponse])
async def get_certificates_by_org(
    org: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get certificates for a specific organization"""
    cert_db_service = CertificateDBService(db)
    certificates = await cert_db_service.get_certificates_by_org(
        org=org, skip=skip, limit=limit
    )
    
    return [_format_certificate_response(cert) for cert in certificates]


@router.post("/search", response_model=List[CertificateResponse])
async def search_certificates(
    request: CertificateSearchRequest,
    db: Session = Depends(get_db)
):
    """Search certificates with various filters"""
    cert_db_service = CertificateDBService(db)
    certificates = await cert_db_service.search_certificates(
        query=request.query,
        user_id=request.user_id,
        device_serial=request.device_serial,
        org=request.org,
        wipe_method=request.wipe_method,
        is_valid=request.is_valid,
        is_verified=request.is_verified,
        skip=request.skip,
        limit=request.limit
    )
    
    return [_format_certificate_response(cert) for cert in certificates]


@router.get("/stats", response_model=CertificateStatsResponse)
async def get_certificate_stats(db: Session = Depends(get_db)):
    """Get certificate statistics"""
    cert_db_service = CertificateDBService(db)
    stats = await cert_db_service.get_certificate_stats()
    
    return CertificateStatsResponse(**stats)


@router.post("/{certificate_id}/verify", response_model=CertificateVerificationResponse)
async def verify_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """Verify a certificate's digital signature"""
    try:
        # Verify the certificate
        verification_result = await certificate_service.verify_certificate(certificate_id)
        
        # Update database if verification is successful
        if verification_result.get("valid"):
            cert_db_service = CertificateDBService(db)
            await cert_db_service.update_certificate_verification(
                certificate_id, is_verified=True
            )
        
        return CertificateVerificationResponse(**verification_result)
        
    except Exception as e:
        return CertificateVerificationResponse(
            valid=False,
            error=f"Verification failed: {str(e)}"
        )


@router.post("/{certificate_id}/invalidate")
async def invalidate_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """Invalidate a certificate"""
    cert_db_service = CertificateDBService(db)
    certificate = await cert_db_service.invalidate_certificate(certificate_id)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return {"message": f"Certificate {certificate_id} invalidated successfully"}


@router.delete("/{certificate_id}")
async def delete_certificate(certificate_id: str, db: Session = Depends(get_db)):
    """Delete a certificate (soft delete)"""
    cert_db_service = CertificateDBService(db)
    success = await cert_db_service.delete_certificate(certificate_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    return {"message": f"Certificate {certificate_id} deleted successfully"}


@router.get("/{certificate_id}/files")
async def get_certificate_files(certificate_id: str, db: Session = Depends(get_db)):
    """Get file paths for a certificate"""
    cert_db_service = CertificateDBService(db)
    certificate = await cert_db_service.get_certificate(certificate_id)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    file_paths = certificate_service.get_certificate_paths(certificate_id)
    
    return {
        "certificate_id": certificate_id,
        "files": file_paths,
        "download_urls": {
            "json": f"/api/v1/certificates/{certificate_id}/download/json",
            "pdf": f"/api/v1/certificates/{certificate_id}/download/pdf",
            "signature": f"/api/v1/certificates/{certificate_id}/download/signature"
        }
    }


@router.get("/{certificate_id}/download/{file_type}")
async def download_certificate_file(
    certificate_id: str,
    file_type: str,
    db: Session = Depends(get_db)
):
    """Download a certificate file (JSON, PDF, or signature)"""
    if file_type not in ["json", "pdf", "signature"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Must be 'json', 'pdf', or 'signature'"
        )
    
    cert_db_service = CertificateDBService(db)
    certificate = await cert_db_service.get_certificate(certificate_id)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found"
        )
    
    file_paths = {
        "json": certificate.json_path,
        "pdf": certificate.pdf_path,
        "signature": certificate.signature_path
    }
    
    file_path = file_paths[file_type]
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{file_type.upper()} file not found"
        )
    
    # In a real implementation, you would return the file content
    # For now, return the file path
    return {
        "file_path": file_path,
        "file_type": file_type,
        "certificate_id": certificate_id
    }


@router.get("/expired", response_model=List[CertificateResponse])
async def get_expired_certificates(db: Session = Depends(get_db)):
    """Get all expired certificates"""
    cert_db_service = CertificateDBService(db)
    certificates = await cert_db_service.get_expired_certificates()
    
    return [_format_certificate_response(cert) for cert in certificates]


def _format_certificate_response(certificate: WipeCertificate) -> CertificateResponse:
    """Format certificate for API response"""
    return CertificateResponse(
        id=certificate.id,
        certificate_id=certificate.certificate_id,
        user_id=certificate.user_id,
        user_name=certificate.user_name,
        user_org=certificate.user_org,
        device_serial=certificate.device_serial,
        device_model=certificate.device_model,
        device_type=certificate.device_type,
        wipe_method=certificate.wipe_method,
        wipe_status=certificate.wipe_status,
        target_path=certificate.target_path,
        size_bytes=certificate.size_bytes,
        size_human=_format_size(certificate.size_bytes),
        passes_completed=certificate.passes_completed,
        total_passes=certificate.total_passes,
        duration_seconds=certificate.duration_seconds,
        verification_hash=certificate.verification_hash,
        certificate_path=certificate.certificate_path,
        json_path=certificate.json_path,
        pdf_path=certificate.pdf_path,
        signature_path=certificate.signature_path,
        is_valid=certificate.is_valid,
        is_verified=certificate.is_verified,
        verified_at=certificate.verified_at,
        created_at=certificate.created_at,
        expires_at=certificate.expires_at
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
