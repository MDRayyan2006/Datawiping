from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.wipe_log import WipeLog, WipeMethod, VerificationStatus
from services.wipe_service import WipeService, WipeLogCreate, WipeLogUpdate

router = APIRouter()


# Pydantic models for request/response
class WipeLogCreateRequest(BaseModel):
    user_id: int
    wipe_method: WipeMethod
    certificate_path: Optional[str] = None


class WipeLogUpdateRequest(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    verification_status: Optional[VerificationStatus] = None
    certificate_path: Optional[str] = None


class WipeLogResponse(BaseModel):
    id: int
    user_id: int
    wipe_method: WipeMethod
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    verification_status: VerificationStatus
    certificate_path: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.post("/", response_model=WipeLogResponse, status_code=status.HTTP_201_CREATED)
async def create_wipe_log(wipe_log: WipeLogCreateRequest, db: Session = Depends(get_db)):
    """Create a new wipe log entry"""
    wipe_service = WipeService(db)
    wipe_log_data = WipeLogCreate(
        user_id=wipe_log.user_id,
        wipe_method=wipe_log.wipe_method,
        certificate_path=wipe_log.certificate_path
    )
    return await wipe_service.create_wipe_log(wipe_log_data)


@router.get("/", response_model=List[WipeLogResponse])
async def get_wipe_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    verification_status: Optional[VerificationStatus] = None,
    wipe_method: Optional[WipeMethod] = None,
    db: Session = Depends(get_db)
):
    """Get wipe logs with optional filtering"""
    wipe_service = WipeService(db)
    return await wipe_service.get_wipe_logs(
        skip=skip, 
        limit=limit, 
        user_id=user_id, 
        verification_status=verification_status,
        wipe_method=wipe_method
    )


@router.get("/{wipe_log_id}", response_model=WipeLogResponse)
async def get_wipe_log(wipe_log_id: int, db: Session = Depends(get_db)):
    """Get a specific wipe log by ID"""
    wipe_service = WipeService(db)
    wipe_log = await wipe_service.get_wipe_log(wipe_log_id)
    if not wipe_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wipe log not found"
        )
    return wipe_log


@router.put("/{wipe_log_id}", response_model=WipeLogResponse)
async def update_wipe_log(
    wipe_log_id: int,
    wipe_log_update: WipeLogUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update a wipe log"""
    wipe_service = WipeService(db)
    wipe_log_data = WipeLogUpdate(
        start_time=wipe_log_update.start_time,
        end_time=wipe_log_update.end_time,
        verification_status=wipe_log_update.verification_status,
        certificate_path=wipe_log_update.certificate_path
    )
    wipe_log = await wipe_service.update_wipe_log(wipe_log_id, wipe_log_data)
    if not wipe_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wipe log not found"
        )
    return wipe_log


@router.post("/{wipe_log_id}/start", response_model=WipeLogResponse)
async def start_wipe(wipe_log_id: int, db: Session = Depends(get_db)):
    """Start a wipe operation"""
    wipe_service = WipeService(db)
    try:
        wipe_log = await wipe_service.start_wipe(wipe_log_id)
        if not wipe_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wipe log not found"
            )
        return wipe_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{wipe_log_id}/complete", response_model=WipeLogResponse)
async def complete_wipe(
    wipe_log_id: int, 
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
    db: Session = Depends(get_db)
):
    """Mark a wipe operation as completed"""
    wipe_service = WipeService(db)
    try:
        wipe_log = await wipe_service.complete_wipe(wipe_log_id, verification_status)
        if not wipe_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wipe log not found"
            )
        return wipe_log
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{wipe_log_id}/fail", response_model=WipeLogResponse)
async def fail_wipe(wipe_log_id: int, db: Session = Depends(get_db)):
    """Mark a wipe operation as failed"""
    wipe_service = WipeService(db)
    wipe_log = await wipe_service.fail_wipe(wipe_log_id)
    if not wipe_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wipe log not found"
        )
    return wipe_log


@router.post("/{wipe_log_id}/execute", response_model=WipeLogResponse)
async def execute_wipe(wipe_log_id: int, db: Session = Depends(get_db)):
    """Execute a wipe operation"""
    wipe_service = WipeService(db)
    success = await wipe_service.execute_wipe(wipe_log_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Wipe operation failed"
        )
    
    # Return the updated wipe log
    wipe_log = await wipe_service.get_wipe_log(wipe_log_id)
    return wipe_log
