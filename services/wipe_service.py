from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import os
import shutil
import asyncio

from models.wipe_log import WipeLog, WipeMethod, VerificationStatus


class WipeLogCreate:
    def __init__(self, user_id: int, wipe_method: WipeMethod, certificate_path: str = None):
        self.user_id = user_id
        self.wipe_method = wipe_method
        self.certificate_path = certificate_path


class WipeLogUpdate:
    def __init__(self, start_time: datetime = None, end_time: datetime = None, 
                 verification_status: VerificationStatus = None, certificate_path: str = None):
        self.start_time = start_time
        self.end_time = end_time
        self.verification_status = verification_status
        self.certificate_path = certificate_path

    def dict(self, exclude_unset=False):
        data = {}
        if self.start_time is not None:
            data['start_time'] = self.start_time
        if self.end_time is not None:
            data['end_time'] = self.end_time
        if self.verification_status is not None:
            data['verification_status'] = self.verification_status
        if self.certificate_path is not None:
            data['certificate_path'] = self.certificate_path
        return data


class WipeService:
    def __init__(self, db: Session):
        self.db = db

    async def create_wipe_log(self, wipe_log_data: WipeLogCreate) -> WipeLog:
        """Create a new wipe log entry"""
        db_wipe_log = WipeLog(
            user_id=wipe_log_data.user_id,
            wipe_method=wipe_log_data.wipe_method,
            certificate_path=wipe_log_data.certificate_path,
            verification_status=VerificationStatus.PENDING
        )
        
        self.db.add(db_wipe_log)
        self.db.commit()
        self.db.refresh(db_wipe_log)
        return db_wipe_log

    async def get_wipe_log(self, wipe_log_id: int) -> Optional[WipeLog]:
        """Get a wipe log by ID"""
        return self.db.query(WipeLog).filter(WipeLog.id == wipe_log_id).first()

    async def get_wipe_logs(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        user_id: Optional[int] = None,
        verification_status: Optional[VerificationStatus] = None,
        wipe_method: Optional[WipeMethod] = None
    ) -> List[WipeLog]:
        """Get wipe logs with optional filtering"""
        query = self.db.query(WipeLog)
        
        if user_id:
            query = query.filter(WipeLog.user_id == user_id)
        
        if verification_status:
            query = query.filter(WipeLog.verification_status == verification_status)
        
        if wipe_method:
            query = query.filter(WipeLog.wipe_method == wipe_method)
        
        return query.offset(skip).limit(limit).all()

    async def update_wipe_log(self, wipe_log_id: int, wipe_log_data: WipeLogUpdate) -> Optional[WipeLog]:
        """Update a wipe log"""
        db_wipe_log = self.db.query(WipeLog).filter(WipeLog.id == wipe_log_id).first()
        
        if not db_wipe_log:
            return None

        # Update fields
        update_data = wipe_log_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_wipe_log, field, value)

        db_wipe_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_wipe_log)
        return db_wipe_log

    async def start_wipe(self, wipe_log_id: int) -> Optional[WipeLog]:
        """Start a wipe operation"""
        db_wipe_log = self.db.query(WipeLog).filter(WipeLog.id == wipe_log_id).first()
        
        if not db_wipe_log:
            return None

        if db_wipe_log.start_time is not None:
            raise ValueError("Wipe operation has already started")

        db_wipe_log.start_time = datetime.utcnow()
        db_wipe_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_wipe_log)
        return db_wipe_log

    async def complete_wipe(self, wipe_log_id: int, verification_status: VerificationStatus = VerificationStatus.VERIFIED) -> Optional[WipeLog]:
        """Mark a wipe operation as completed"""
        db_wipe_log = self.db.query(WipeLog).filter(WipeLog.id == wipe_log_id).first()
        
        if not db_wipe_log:
            return None

        if db_wipe_log.start_time is None:
            raise ValueError("Wipe operation has not started")

        if db_wipe_log.end_time is not None:
            raise ValueError("Wipe operation is already completed")

        db_wipe_log.end_time = datetime.utcnow()
        db_wipe_log.verification_status = verification_status
        db_wipe_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_wipe_log)
        return db_wipe_log

    async def fail_wipe(self, wipe_log_id: int) -> Optional[WipeLog]:
        """Mark a wipe operation as failed"""
        db_wipe_log = self.db.query(WipeLog).filter(WipeLog.id == wipe_log_id).first()
        
        if not db_wipe_log:
            return None

        db_wipe_log.end_time = datetime.utcnow()
        db_wipe_log.verification_status = VerificationStatus.FAILED
        db_wipe_log.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_wipe_log)
        return db_wipe_log

    async def execute_wipe(self, wipe_log_id: int) -> bool:
        """Execute the actual wipe operation"""
        db_wipe_log = self.db.query(WipeLog).filter(WipeLog.id == wipe_log_id).first()
        
        if not db_wipe_log:
            return False

        try:
            # Start the wipe operation
            await self.start_wipe(wipe_log_id)
            
            # Perform the actual wipe based on the method
            success = await self._perform_wipe(db_wipe_log.wipe_method)
            
            if success:
                await self.complete_wipe(wipe_log_id)
            else:
                await self.fail_wipe(wipe_log_id)
            
            return success
            
        except Exception as e:
            await self.fail_wipe(wipe_log_id)
            return False

    async def _perform_wipe(self, wipe_method: WipeMethod) -> bool:
        """Perform the actual wipe operation"""
        try:
            if wipe_method == WipeMethod.SECURE_DELETE:
                return await self._secure_delete()
            elif wipe_method == WipeMethod.OVERWRITE:
                return await self._overwrite_method()
            elif wipe_method == WipeMethod.SHRED:
                return await self._shred_method()
            elif wipe_method == WipeMethod.CRYPTO_WIPE:
                return await self._crypto_wipe()
            elif wipe_method == WipeMethod.PHYSICAL_DESTRUCTION:
                return await self._physical_destruction()
            else:
                raise ValueError(f"Unknown wipe method: {wipe_method}")
                
        except Exception as e:
            print(f"Wipe operation failed: {e}")
            return False

    async def _secure_delete(self) -> bool:
        """Securely delete using multiple random overwrites"""
        try:
            # Simulate secure delete operation
            print("Performing secure delete operation...")
            # In a real implementation, this would target specific files/directories
            # For now, we'll simulate the operation
            await asyncio.sleep(1)  # Simulate processing time
            return True
        except Exception as e:
            print(f"Secure delete failed: {e}")
            return False

    async def _overwrite_method(self) -> bool:
        """Simple overwrite method"""
        try:
            print("Performing overwrite operation...")
            # Simulate overwrite operation
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            print(f"Overwrite failed: {e}")
            return False

    async def _shred_method(self) -> bool:
        """Shred method with pattern overwriting"""
        try:
            print("Performing shred operation...")
            # Simulate shred operation
            await asyncio.sleep(1.5)
            return True
        except Exception as e:
            print(f"Shred failed: {e}")
            return False

    async def _crypto_wipe(self) -> bool:
        """Cryptographic wipe method"""
        try:
            print("Performing cryptographic wipe...")
            # Simulate crypto wipe operation
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"Crypto wipe failed: {e}")
            return False

    async def _physical_destruction(self) -> bool:
        """Physical destruction method"""
        try:
            print("Performing physical destruction...")
            # Simulate physical destruction
            await asyncio.sleep(3)
            return True
        except Exception as e:
            print(f"Physical destruction failed: {e}")
            return False
