from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import os
import logging

from database import get_db, SessionLocal
from models.wipe_log import WipeLog, WipeMethod, VerificationStatus
from models.user import User
from services.wipe_service import WipeService, WipeMethod as WipeMethodEnum
from services.certificate_service import certificate_service
from services.certificate_db_service import CertificateDBService
from services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for request/response
class WipeJobRequest(BaseModel):
    user_id: int = Field(..., description="User ID performing the wipe")
    target_path: str = Field(..., description="Path to wipe (file, folder, or device)")
    wipe_method: str = Field(..., description="Wipe method to use (supports app values)")
    generate_certificate: bool = Field(True, description="Generate certificate after wipe")
    mock_mode: bool = Field(False, description="Run in mock mode for testing")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class WipeJobResponse(BaseModel):
    job_id: int
    user_id: int
    user_name: str
    user_org: str
    device_serial: str
    target_path: str
    wipe_method: str
    status: str
    verification_status: str
    certificate_path: Optional[str]
    notes: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    verification_status: str
    progress: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    certificate_id: Optional[str]

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[WipeJobResponse]
    total: int
    page: int
    limit: int
    has_more: bool


# Job status tracking
job_status = {}


def _map_incoming_wipe_method(method_value: str) -> WipeMethod:
    """Map incoming method strings from the app to internal enum."""
    value = (method_value or "").strip().lower()
    mapping = {
        # App method values → internal simplified methods
        "dod_5220_22_m": WipeMethod.OVERWRITE,
        "nist_800_88": WipeMethod.SECURE_DELETE,
        "gutmann": WipeMethod.SHRED,
        "single_pass": WipeMethod.OVERWRITE,
        "random_data": WipeMethod.OVERWRITE,
        "zero_overwrite": WipeMethod.OVERWRITE,
        # Allow direct internal names too
        "secure_delete": WipeMethod.SECURE_DELETE,
        "overwrite": WipeMethod.OVERWRITE,
        "shred": WipeMethod.SHRED,
        "crypto_wipe": WipeMethod.CRYPTO_WIPE,
        "physical_destruction": WipeMethod.PHYSICAL_DESTRUCTION,
    }
    return mapping.get(value, WipeMethod.OVERWRITE)


@router.post("/start", response_model=WipeJobResponse, status_code=status.HTTP_201_CREATED)
async def start_wipe_job(
    request: WipeJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a new wipe job.
    
    This endpoint creates a wipe job record and starts the wipe operation
    in the background. The job can be tracked using the job ID.
    """
    try:
        # Validate user exists
        user_service = UserService(db)
        user = await user_service.get_user(request.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Resolve wipe method
        mapped_method = _map_incoming_wipe_method(request.wipe_method)

        # Create wipe log entry
        wipe_log = WipeLog(
            user_id=request.user_id,
            wipe_method=mapped_method,
            verification_status=VerificationStatus.PENDING,
            certificate_path=None
        )
        
        db.add(wipe_log)
        db.commit()
        db.refresh(wipe_log)
        
        # Use mapped method for execution
        wipe_method_enum = mapped_method
        
        # Create wipe service instance (mock mode handled in execute)
        wipe_service = WipeService(db)
        
        # Start wipe operation in background
        background_tasks.add_task(
            execute_wipe_job,
            wipe_log.id,
            request.target_path,
            wipe_method_enum,
            request.generate_certificate,
            request.mock_mode,
            request.notes
        )
        
        # Update job status
        job_status[wipe_log.id] = {
            "status": "pending",
            "progress": {"message": "Job queued for execution", "percentage": 0},
            "started_at": None,
            "completed_at": None,
            "error_message": None
        }
        
        return WipeJobResponse(
            job_id=wipe_log.id,
            user_id=user.id,
            user_name=user.name,
            user_org=user.org,
            device_serial=user.device_serial,
            target_path=request.target_path,
            wipe_method=mapped_method.value,
            status="pending",
            verification_status=wipe_log.verification_status.value,
            certificate_path=wipe_log.certificate_path,
            notes=request.notes,
            created_at=wipe_log.created_at,
            started_at=wipe_log.start_time,
            completed_at=wipe_log.end_time,
            error_message=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start wipe job: {str(e)}"
        )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get the status of a specific wipe job"""
    try:
        # Get wipe log
        wipe_log = db.query(WipeLog).filter(WipeLog.id == job_id).first()
        if not wipe_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Get job status from tracking
        status_info = job_status.get(job_id, {
            "status": "unknown",
            "progress": {"message": "Status unknown", "percentage": 0},
            "started_at": None,
            "completed_at": None,
            "error_message": None
        })
        
        # Calculate progress based on verification status
        progress_percentage = 0
        progress_message = "Status unknown"
        
        if wipe_log.verification_status == VerificationStatus.PENDING:
            progress_percentage = 0
            progress_message = "Job queued for execution"
        elif wipe_log.verification_status == VerificationStatus.VERIFIED:
            progress_percentage = 100
            progress_message = "Wipe operation completed successfully"
        elif wipe_log.verification_status == VerificationStatus.FAILED:
            progress_percentage = 0
            progress_message = "Wipe operation failed"
        elif wipe_log.start_time and not wipe_log.end_time:
            # Job is running
            progress_percentage = 50
            progress_message = "Wipe operation in progress"
        
        # Update progress in status_info
        status_info["progress"] = {
            "message": progress_message,
            "percentage": progress_percentage
        }
        
        # Calculate duration
        duration_seconds = None
        if wipe_log.start_time and wipe_log.end_time:
            duration_seconds = (wipe_log.end_time - wipe_log.start_time).total_seconds()
        elif wipe_log.start_time:
            duration_seconds = (datetime.utcnow() - wipe_log.start_time).total_seconds()
        
        return JobStatusResponse(
            job_id=job_id,
            status=wipe_log.verification_status.value,
            verification_status=wipe_log.verification_status.value,
            progress=status_info.get("progress", {}),
            created_at=wipe_log.created_at,
            started_at=wipe_log.start_time,
            completed_at=wipe_log.end_time,
            duration_seconds=duration_seconds,
            error_message=status_info.get("error_message"),
            certificate_id=wipe_log.certificate_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List wipe jobs with optional filtering"""
    try:
        # Build query
        query = db.query(WipeLog)
        
        if user_id:
            query = query.filter(WipeLog.user_id == user_id)
        
        if status:
            query = query.filter(WipeLog.verification_status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        wipe_logs = query.offset(offset).limit(limit).all()
        
        # Get user information
        user_service = UserService(db)
        jobs = []
        for wipe_log in wipe_logs:
            user = await user_service.get_user(wipe_log.user_id)
            if user:
                jobs.append(WipeJobResponse(
                    job_id=wipe_log.id,
                    user_id=user.id,
                    user_name=user.name,
                    user_org=user.org,
                    device_serial=user.device_serial,
                    target_path="N/A",  # Would need to store this in WipeLog
                    wipe_method=wipe_log.wipe_method.value,
                    status=wipe_log.verification_status.value,
                    verification_status=wipe_log.verification_status.value,
                    certificate_path=wipe_log.certificate_path,
                    notes=None,
                    created_at=wipe_log.created_at,
                    started_at=wipe_log.start_time,
                    completed_at=wipe_log.end_time,
                    error_message=None
                ))
        
        return JobListResponse(
            jobs=jobs,
            total=total,
            page=page,
            limit=limit,
            has_more=offset + limit < total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=JobListResponse)
async def get_user_jobs(
    user_id: int,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all jobs for a specific user"""
    return await list_jobs(user_id=user_id, page=page, limit=limit, db=db)


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """Cancel a running wipe job"""
    try:
        # Get wipe log
        wipe_log = db.query(WipeLog).filter(WipeLog.id == job_id).first()
        if not wipe_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if job can be cancelled
        if wipe_log.verification_status in [VerificationStatus.VERIFIED, VerificationStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is already completed and cannot be cancelled"
            )
        
        # Update status
        wipe_log.verification_status = VerificationStatus.FAILED
        wipe_log.completed_at = datetime.utcnow()
        db.commit()
        
        # Update job status tracking
        if job_id in job_status:
            job_status[job_id]["status"] = "cancelled"
            job_status[job_id]["progress"] = {"message": "Job cancelled by user", "percentage": 0}
            job_status[job_id]["completed_at"] = datetime.utcnow()
            job_status[job_id]["error_message"] = "Job cancelled by user"
        
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_job_stats(db: Session = Depends(get_db)):
    """Get job statistics"""
    try:
        # Get all wipe logs
        all_logs = db.query(WipeLog).all()
        
        # Calculate statistics
        total_jobs = len(all_logs)
        pending_jobs = len([log for log in all_logs if log.verification_status == VerificationStatus.PENDING])
        completed_jobs = len([log for log in all_logs if log.verification_status == VerificationStatus.VERIFIED])
        failed_jobs = len([log for log in all_logs if log.verification_status == VerificationStatus.FAILED])
        
        # Group by wipe method
        method_stats = {}
        for log in all_logs:
            method = log.wipe_method.value
            method_stats[method] = method_stats.get(method, 0) + 1
        
        # Group by user
        user_stats = {}
        for log in all_logs:
            user_id = log.user_id
            user_stats[user_id] = user_stats.get(user_id, 0) + 1
        
        return {
            "total_jobs": total_jobs,
            "pending_jobs": pending_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "method_stats": method_stats,
            "user_stats": user_stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job stats: {str(e)}"
        )


async def execute_wipe_job(
    job_id: int,
    target_path: str,
    wipe_method: WipeMethodEnum,
    generate_certificate: bool,
    mock_mode: bool,
    notes: Optional[str]
):
    """Execute a wipe job in the background"""
    try:
        # Update job status
        job_status[job_id] = {
            "status": "running",
            "progress": {"message": "Starting wipe operation", "percentage": 10},
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }
        
        # Import the actual wipe service that handles file operations
        from services.wipe import WipeService as FileWipeService, WipeMethod as FileWipeMethod
        
        # Map the wipe method to the file wipe service method
        method_mapping = {
            WipeMethod.SECURE_DELETE: FileWipeMethod.DOD_5220_22_M,
            WipeMethod.OVERWRITE: FileWipeMethod.SINGLE_PASS,
            WipeMethod.SHRED: FileWipeMethod.GUTMANN,
            WipeMethod.CRYPTO_WIPE: FileWipeMethod.RANDOM,
            WipeMethod.PHYSICAL_DESTRUCTION: FileWipeMethod.ZERO,
        }
        
        file_wipe_method = method_mapping.get(wipe_method, FileWipeMethod.SINGLE_PASS)
        
        # Create file wipe service instance
        file_wipe_service = FileWipeService(mock_mode=mock_mode, generate_certificates=generate_certificate)
        
        # Determine what type of target we're wiping
        import os
        # Normalize incoming path (remove quotes/whitespace, normalize separators)
        normalized_path = (target_path or "").strip().strip('"').strip("'")
        normalized_path = os.path.normpath(normalized_path) if normalized_path else normalized_path
        success = False
        wipe_result = None
        
        if normalized_path and normalized_path != "N/A":
            if os.path.isfile(normalized_path):
                # Wipe a single file
                wipe_result = await file_wipe_service.wipe_file(normalized_path, file_wipe_method)
                success = wipe_result.success
            elif os.path.isdir(normalized_path):
                # Wipe a directory
                wipe_result = await file_wipe_service.wipe_folder(normalized_path, file_wipe_method)
                success = wipe_result.success
            elif normalized_path.startswith('\\\\.\\') or normalized_path.startswith('/dev/'):
                # Wipe a drive
                wipe_result = await file_wipe_service.wipe_drive(normalized_path, file_wipe_method)
                success = wipe_result.success
            else:
                # Invalid path provided; do not silently succeed
                success = False
                wipe_result = None
        else:
            # No path provided; fail the job
            success = False
        
        # Update database
        db = SessionLocal()
        try:
            wipe_log = db.query(WipeLog).filter(WipeLog.id == job_id).first()
            if wipe_log:
                # Update wipe log with actual start/end times if we have a result
                if wipe_result and success:
                    wipe_log.start_time = datetime.utcnow() - timedelta(seconds=wipe_result.duration_seconds)
                    wipe_log.end_time = datetime.utcnow()
                    wipe_log.verification_status = VerificationStatus.VERIFIED
                    db.commit()
                elif success:
                    wipe_log.verification_status = VerificationStatus.VERIFIED
                    db.commit()
                else:
                    wipe_log.verification_status = VerificationStatus.FAILED
                    # If we have a result with an error message, persist a brief message in notes
                    if wipe_result and wipe_result.error_message:
                        # Append error to notes for quick visibility
                        existing = (wipe_log.notes or "")
                        snippet = f"Wipe error: {wipe_result.error_message}"
                        wipe_log.notes = (existing + "\n" + snippet).strip() if existing else snippet
                    db.commit()
                
                # Generate certificate if requested and succeeded
                if success and generate_certificate:
                    user = await UserService(db).get_user(wipe_log.user_id)
                    if user:
                        try:
                            # Use actual wipe result data if available
                            if wipe_result:
                                cert = await certificate_service.generate_certificate(
                                    user_id=user.id,
                                    user_name=user.name,
                                    user_org=user.org,
                                    device_serial=user.device_serial,
                                    device_model="Unknown",
                                    device_type="Unknown",
                                    wipe_method=wipe_method.value,
                                    wipe_status="verified",
                                    target_path=target_path,
                                    size_bytes=wipe_result.size_bytes,
                                    passes_completed=wipe_result.passes_completed,
                                    total_passes=wipe_result.total_passes,
                                    duration_seconds=wipe_result.duration_seconds,
                                    verification_hash=wipe_result.verification_hash,
                                )
                                
                                # Save certificate to database
                                from services.certificate_db_service import CertificateDBService
                                cert_db_service = CertificateDBService(db)
                                await cert_db_service.create_certificate(cert, wipe_log.id)
                                
                                # Update wipe log with certificate path
                                wipe_log.certificate_path = cert.certificate_path
                                db.commit()
                                
                                logger.info(f"Certificate generated and saved: {cert.certificate_id}")
                            else:
                                # No certificate without an actual successful wipe result
                                logger.warning("No wipe result available for certificate generation")
                        except Exception as e:
                            logger.error(f"Failed to generate certificate: {e}")
                            # Continue without certificate - don't fail the entire job

                # Update job status cache from DB
                job_status[job_id] = {
                    "status": "completed" if success else "failed",
                    "progress": {
                        "message": "Wipe operation completed" if success else "Wipe operation failed",
                        "percentage": 100 if success else 0
                    },
                    "started_at": wipe_log.start_time,
                    "completed_at": wipe_log.end_time,
                    "error_message": None if success else (wipe_result.error_message if wipe_result and wipe_result.error_message else "Wipe failed"),
                }
        finally:
            db.close()
        
        # Mock mode is handled per operation
            
    except Exception as e:
        # Update job status with error
        job_status[job_id] = {
            "status": "failed",
            "progress": {"message": "Wipe operation failed", "percentage": 0},
            "started_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "error_message": str(e)
        }
        
        # Update database
        db = SessionLocal()
        try:
            wipe_log = db.query(WipeLog).filter(WipeLog.id == job_id).first()
            if wipe_log:
                wipe_log.verification_status = VerificationStatus.FAILED
                wipe_log.end_time = datetime.utcnow()
                db.commit()
        finally:
            db.close()
