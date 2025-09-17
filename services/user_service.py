from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from models.user import User


class UserCreate:
    def __init__(self, name: str, org: str, device_serial: str):
        self.name = name
        self.org = org
        self.device_serial = device_serial


class UserUpdate:
    def __init__(self, name: str = None, org: str = None, device_serial: str = None):
        self.name = name
        self.org = org
        self.device_serial = device_serial

    def dict(self, exclude_unset=False):
        data = {}
        if self.name is not None:
            data['name'] = self.name
        if self.org is not None:
            data['org'] = self.org
        if self.device_serial is not None:
            data['device_serial'] = self.device_serial
        return data


class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if device_serial already exists
        existing_user = self.db.query(User).filter(
            User.device_serial == user_data.device_serial
        ).first()
        
        if existing_user:
            raise ValueError("Device serial already exists")

        db_user = User(
            name=user_data.name,
            org=user_data.org,
            device_serial=user_data.device_serial
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update a user"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        
        if not db_user:
            return None

        # Check for device_serial conflicts if it's being updated
        if user_data.device_serial:
            existing_user = self.db.query(User).filter(
                and_(
                    User.id != user_id,
                    User.device_serial == user_data.device_serial
                )
            ).first()
            
            if existing_user:
                raise ValueError("Device serial already exists")

        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db_user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    async def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        db_user = self.db.query(User).filter(User.id == user_id).first()
        
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    async def get_user_by_device_serial(self, device_serial: str) -> Optional[User]:
        """Get a user by device serial"""
        return self.db.query(User).filter(User.device_serial == device_serial).first()

    async def get_users_by_org(self, org: str) -> List[User]:
        """Get all users by organization"""
        return self.db.query(User).filter(User.org == org).all()
