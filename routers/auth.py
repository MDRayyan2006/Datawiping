from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from database import get_db
from models.user import User
from services.user_service import UserService, UserCreate, UserUpdate

router = APIRouter()


# Pydantic models for request/response
class UserRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full name of the user")
    org: str = Field(..., min_length=1, max_length=100, description="Organization name")
    device_serial: str = Field(..., min_length=1, max_length=50, description="Device serial number")
    email: Optional[EmailStr] = Field(None, description="Email address (optional)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")


class UserRegistrationResponse(BaseModel):
    id: int
    name: str
    org: str
    device_serial: str
    email: Optional[str]
    notes: Optional[str]
    created_at: datetime
    message: str

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: int
    name: str
    org: str
    device_serial: str
    email: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    total_wipe_operations: int
    total_certificates: int

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    org: Optional[str] = Field(None, min_length=1, max_length=100)
    device_serial: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    notes: Optional[str] = Field(None, max_length=500)


@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with device information.
    
    This endpoint creates a new user account and associates it with a specific device.
    The device serial number must be unique across all users.
    """
    try:
        user_service = UserService(db)
        
        # Check if device serial already exists
        existing_user = await user_service.get_user_by_device_serial(request.device_serial)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device serial '{request.device_serial}' is already registered to user '{existing_user.name}'"
            )
        
        # Create user
        user_data = UserCreate(
            name=request.name,
            org=request.org,
            device_serial=request.device_serial
        )
        
        user = await user_service.create_user(user_data)
        
        return UserRegistrationResponse(
            id=user.id,
            name=user.name,
            org=user.org,
            device_serial=user.device_serial,
            email=request.email,
            notes=request.notes,
            created_at=user.created_at,
            message=f"User '{user.name}' registered successfully with device '{user.device_serial}'"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get detailed user profile with statistics"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get statistics
        total_wipe_operations = len(user.wipe_logs) if user.wipe_logs else 0
        total_certificates = len(user.certificates) if user.certificates else 0
        
        return UserProfileResponse(
            id=user.id,
            name=user.name,
            org=user.org,
            device_serial=user.device_serial,
            email=None,  # Would be added to User model if needed
            notes=None,  # Would be added to User model if needed
            created_at=user.created_at,
            updated_at=user.updated_at,
            total_wipe_operations=total_wipe_operations,
            total_certificates=total_certificates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.put("/profile/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    try:
        user_service = UserService(db)
        
        # Check if user exists
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user
        user_data = UserUpdate(
            name=request.name,
            org=request.org,
            device_serial=request.device_serial
        )
        
        updated_user = await user_service.update_user(user_id, user_data)
        
        # Get updated statistics
        total_wipe_operations = len(updated_user.wipe_logs) if updated_user.wipe_logs else 0
        total_certificates = len(updated_user.certificates) if updated_user.certificates else 0
        
        return UserProfileResponse(
            id=updated_user.id,
            name=updated_user.name,
            org=updated_user.org,
            device_serial=updated_user.device_serial,
            email=None,
            notes=None,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            total_wipe_operations=total_wipe_operations,
            total_certificates=total_certificates
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )


@router.get("/device/{device_serial}", response_model=UserProfileResponse)
async def get_user_by_device(device_serial: str, db: Session = Depends(get_db)):
    """Get user profile by device serial number"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_device_serial(device_serial)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No user found with device serial '{device_serial}'"
            )
        
        # Get statistics
        total_wipe_operations = len(user.wipe_logs) if user.wipe_logs else 0
        total_certificates = len(user.certificates) if user.certificates else 0
        
        return UserProfileResponse(
            id=user.id,
            name=user.name,
            org=user.org,
            device_serial=user.device_serial,
            email=None,
            notes=None,
            created_at=user.created_at,
            updated_at=user.updated_at,
            total_wipe_operations=total_wipe_operations,
            total_certificates=total_certificates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user by device: {str(e)}"
        )


@router.get("/org/{org}", response_model=List[UserProfileResponse])
async def get_users_by_organization(
    org: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all users in an organization"""
    try:
        user_service = UserService(db)
        users = await user_service.get_users_by_org(org)
        
        # Apply pagination
        paginated_users = users[skip:skip + limit]
        
        result = []
        for user in paginated_users:
            total_wipe_operations = len(user.wipe_logs) if user.wipe_logs else 0
            total_certificates = len(user.certificates) if user.certificates else 0
            
            result.append(UserProfileResponse(
                id=user.id,
                name=user.name,
                org=user.org,
                device_serial=user.device_serial,
                email=None,
                notes=None,
                created_at=user.created_at,
                updated_at=user.updated_at,
                total_wipe_operations=total_wipe_operations,
                total_certificates=total_certificates
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users by organization: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user and all associated data"""
    try:
        user_service = UserService(db)
        success = await user_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
