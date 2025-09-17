from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models.user import User
from services.user_service import UserService, UserCreate, UserUpdate

router = APIRouter()


# Pydantic models for request/response
class UserCreateRequest(BaseModel):
    name: str
    org: str
    device_serial: str


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    org: Optional[str] = None
    device_serial: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    org: str
    device_serial: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreateRequest, db: Session = Depends(get_db)):
    """Create a new user"""
    user_service = UserService(db)
    user_data = UserCreate(
        name=user.name,
        org=user.org,
        device_serial=user.device_serial
    )
    try:
        return await user_service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    org: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all users with pagination and optional organization filter"""
    user_service = UserService(db)
    if org:
        return await user_service.get_users_by_org(org)
    return await user_service.get_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user_service = UserService(db)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/device/{device_serial}", response_model=UserResponse)
async def get_user_by_device_serial(device_serial: str, db: Session = Depends(get_db)):
    """Get a user by device serial"""
    user_service = UserService(db)
    user = await user_service.get_user_by_device_serial(device_serial)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update a user"""
    user_service = UserService(db)
    user_data = UserUpdate(
        name=user_update.name,
        org=user_update.org,
        device_serial=user_update.device_serial
    )
    try:
        user = await user_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    user_service = UserService(db)
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
