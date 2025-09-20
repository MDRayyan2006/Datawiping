from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import os
import json
from datetime import datetime

from database import get_db
from models.certificate import WipeCertificate
from models.wipe_log import WipeLog
from services.certificate_service import certificate_service
from services.certificate_db_service import CertificateDBService

router = APIRouter()


@router.get("/certificate/{certificate_id}/pdf")
async def download_certificate_pdf(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """
    Download a certificate PDF file.
    
    Returns the PDF certificate file for the specified certificate ID.
    """
    try:
        # Get certificate from database
        cert_db_service = CertificateDBService(db)
        certificate = await cert_db_service.get_certificate(certificate_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        # Check if PDF file exists
        pdf_path = certificate.pdf_path
        if not os.path.exists(pdf_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PDF file not found"
            )
        
        # Return file
        return FileResponse(
            path=pdf_path,
            filename=f"certificate_{certificate_id}.pdf",
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{certificate_id}.pdf",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download PDF: {str(e)}"
        )


@router.get("/certificate/{certificate_id}/json")
async def download_certificate_json(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """
    Download a certificate JSON file.
    
    Returns the JSON certificate data for the specified certificate ID.
    """
    try:
        # Get certificate from database
        cert_db_service = CertificateDBService(db)
        certificate = await cert_db_service.get_certificate(certificate_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        # Check if JSON file exists
        json_path = certificate.json_path
        if not os.path.exists(json_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JSON file not found"
            )
        
        # Read and return JSON content
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        return JSONResponse(
            content=json_data,
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{certificate_id}.json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download JSON: {str(e)}"
        )


@router.get("/certificate/{certificate_id}/signature")
async def download_certificate_signature(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """
    Download a certificate signature file.
    
    Returns the digital signature file for the specified certificate ID.
    """
    try:
        # Get certificate from database
        cert_db_service = CertificateDBService(db)
        certificate = await cert_db_service.get_certificate(certificate_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        # Check if signature file exists
        signature_path = certificate.signature_path
        if not os.path.exists(signature_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signature file not found"
            )
        
        # Read and return signature content
        with open(signature_path, 'r', encoding='utf-8') as f:
            signature_data = json.load(f)
        
        return JSONResponse(
            content=signature_data,
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{certificate_id}_signature.json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download signature: {str(e)}"
        )


@router.get("/certificate/{certificate_id}/zip")
async def download_certificate_package(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """
    Download a complete certificate package (ZIP file).
    
    Returns a ZIP file containing the PDF, JSON, and signature files.
    """
    try:
        import zipfile
        import tempfile
        
        # Get certificate from database
        cert_db_service = CertificateDBService(db)
        certificate = await cert_db_service.get_certificate(certificate_id)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        # Check if all files exist
        files_to_zip = {
            "pdf": certificate.pdf_path,
            "json": certificate.json_path,
            "signature": certificate.signature_path
        }
        
        missing_files = [name for name, path in files_to_zip.items() if not os.path.exists(path)]
        if missing_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Missing files: {', '.join(missing_files)}"
            )
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add files to ZIP
                for file_type, file_path in files_to_zip.items():
                    filename = f"certificate_{certificate_id}.{file_type}"
                    if file_type == "signature":
                        filename = f"certificate_{certificate_id}_signature.json"
                    zipf.write(file_path, filename)
                
                # Add a README file
                readme_content = f"""Certificate Package: {certificate_id}

This package contains:
- certificate_{certificate_id}.pdf: Human-readable certificate
- certificate_{certificate_id}.json: Machine-readable certificate data
- certificate_{certificate_id}_signature.json: Digital signature for verification

Generated: {certificate.created_at}
Expires: {certificate.expires_at}
User: {certificate.user_name} ({certificate.user_org})
Device: {certificate.device_serial} ({certificate.device_model})
Wipe Method: {certificate.wipe_method}
"""
                zipf.writestr("README.txt", readme_content)
        
        # Return ZIP file
        return FileResponse(
            path=temp_zip.name,
            filename=f"certificate_{certificate_id}_package.zip",
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{certificate_id}_package.zip",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create certificate package: {str(e)}"
        )


@router.get("/job/{job_id}/certificate")
async def get_job_certificate(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get certificate information for a specific job.
    
    Returns certificate details if the job has an associated certificate.
    """
    try:
        # Get wipe log
        wipe_log = db.query(WipeLog).filter(WipeLog.id == job_id).first()
        if not wipe_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if not wipe_log.certificate_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No certificate associated with this job"
            )
        
        # Get certificate
        cert_db_service = CertificateDBService(db)
        certificate = await cert_db_service.get_certificate(wipe_log.certificate_path)
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        return {
            "job_id": job_id,
            "certificate_id": certificate.certificate_id,
            "download_urls": {
                "pdf": f"/api/v1/downloads/certificate/{certificate.certificate_id}/pdf",
                "json": f"/api/v1/downloads/certificate/{certificate.certificate_id}/json",
                "signature": f"/api/v1/downloads/certificate/{certificate.certificate_id}/signature",
                "package": f"/api/v1/downloads/certificate/{certificate.certificate_id}/zip"
            },
            "certificate_info": {
                "created_at": certificate.created_at,
                "expires_at": certificate.expires_at,
                "is_valid": certificate.is_valid,
                "is_verified": certificate.is_verified,
                "user_name": certificate.user_name,
                "device_serial": certificate.device_serial,
                "wipe_method": certificate.wipe_method
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job certificate: {str(e)}"
        )


@router.get("/user/{user_id}/certificates")
async def get_user_certificates(
    user_id: int,
    format: str = "list",  # "list" or "download_urls"
    db: Session = Depends(get_db)
):
    """
    Get all certificates for a specific user.
    
    Returns either a list of certificate information or download URLs.
    """
    try:
        # Get user certificates
        cert_db_service = CertificateDBService(db)
        certificates = await cert_db_service.get_certificates_by_user(user_id)
        
        if format == "download_urls":
            # Return download URLs
            return {
                "user_id": user_id,
                "total_certificates": len(certificates),
                "certificates": [
                    {
                        "certificate_id": cert.certificate_id,
                        "created_at": cert.created_at,
                        "expires_at": cert.expires_at,
                        "wipe_method": cert.wipe_method,
                        "download_urls": {
                            "pdf": f"/api/v1/downloads/certificate/{cert.certificate_id}/pdf",
                            "json": f"/api/v1/downloads/certificate/{cert.certificate_id}/json",
                            "signature": f"/api/v1/downloads/certificate/{cert.certificate_id}/signature",
                            "package": f"/api/v1/downloads/certificate/{cert.certificate_id}/zip"
                        }
                    }
                    for cert in certificates
                ]
            }
        else:
            # Return certificate list
            return {
                "user_id": user_id,
                "total_certificates": len(certificates),
                "certificates": [
                    {
                        "certificate_id": cert.certificate_id,
                        "created_at": cert.created_at,
                        "expires_at": cert.expires_at,
                        "wipe_method": cert.wipe_method,
                        "is_valid": cert.is_valid,
                        "is_verified": cert.is_verified,
                        "device_serial": cert.device_serial,
                        "device_model": cert.device_model
                    }
                    for cert in certificates
                ]
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user certificates: {str(e)}"
        )


@router.get("/verify/{certificate_id}")
async def verify_certificate_online(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    """
    Verify a certificate's digital signature online.
    
    Returns verification results without downloading files.
    """
    try:
        # Verify certificate
        verification_result = await certificate_service.verify_certificate(certificate_id)
        
        # Update database if verification is successful
        if verification_result.get("valid"):
            cert_db_service = CertificateDBService(db)
            await cert_db_service.update_certificate_verification(
                certificate_id, is_verified=True
            )
        
        return {
            "certificate_id": certificate_id,
            "verification_result": verification_result,
            "verified_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify certificate: {str(e)}"
        )
