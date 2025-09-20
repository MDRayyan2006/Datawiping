from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from models.certificate import WipeCertificate
from services.certificate_service import WipeCertificate as WipeCertificateData


class CertificateDBService:
    """Service for managing certificates in the database"""
    
    def __init__(self, db: Session):
        self.db = db

    async def create_certificate(self, cert_data: WipeCertificateData, wipe_log_id: Optional[int] = None) -> WipeCertificate:
        """Create a new certificate record in the database"""
        db_certificate = WipeCertificate(
            certificate_id=cert_data.certificate_id,
            user_id=cert_data.user_id,
            wipe_log_id=wipe_log_id,
            user_name=cert_data.user_name,
            user_org=cert_data.user_org,
            device_serial=cert_data.device_serial,
            device_model=cert_data.device_model,
            device_type=cert_data.device_type,
            wipe_method=cert_data.wipe_method,
            wipe_status=cert_data.wipe_status,
            target_path=cert_data.target_path,
            size_bytes=cert_data.size_bytes,
            passes_completed=cert_data.passes_completed,
            total_passes=cert_data.total_passes,
            duration_seconds=int(cert_data.duration_seconds),
            verification_hash=cert_data.verification_hash,
            certificate_path=cert_data.certificate_path,
            json_path=cert_data.json_path,
            pdf_path=cert_data.pdf_path,
            signature_path=cert_data.signature_path,
            expires_at=cert_data.expires_at
        )
        
        self.db.add(db_certificate)
        self.db.commit()
        self.db.refresh(db_certificate)
        return db_certificate

    async def get_certificate(self, certificate_id: str) -> Optional[WipeCertificate]:
        """Get a certificate by ID"""
        return self.db.query(WipeCertificate).filter(
            WipeCertificate.certificate_id == certificate_id
        ).first()
    
    async def get_certificate_by_id(self, certificate_id: str) -> Optional[WipeCertificate]:
        """Get a certificate by ID (alias for get_certificate)"""
        return await self.get_certificate(certificate_id)

    async def get_certificates_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> List[WipeCertificate]:
        """Get certificates for a specific user"""
        return self.db.query(WipeCertificate).filter(
            WipeCertificate.user_id == user_id
        ).offset(skip).limit(limit).all()

    async def get_certificates_by_device(self, device_serial: str) -> List[WipeCertificate]:
        """Get certificates for a specific device"""
        return self.db.query(WipeCertificate).filter(
            WipeCertificate.device_serial == device_serial
        ).all()

    async def get_certificates_by_org(self, org: str, skip: int = 0, limit: int = 100) -> List[WipeCertificate]:
        """Get certificates for a specific organization"""
        return self.db.query(WipeCertificate).filter(
            WipeCertificate.user_org == org
        ).offset(skip).limit(limit).all()

    async def get_all_certificates(self, skip: int = 0, limit: int = 100) -> List[WipeCertificate]:
        """Get all certificates with pagination"""
        return self.db.query(WipeCertificate).offset(skip).limit(limit).all()

    async def update_certificate_verification(self, certificate_id: str, is_verified: bool = True) -> Optional[WipeCertificate]:
        """Update certificate verification status"""
        db_certificate = self.db.query(WipeCertificate).filter(
            WipeCertificate.certificate_id == certificate_id
        ).first()
        
        if not db_certificate:
            return None

        db_certificate.is_verified = is_verified
        db_certificate.verified_at = datetime.utcnow() if is_verified else None
        db_certificate.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_certificate)
        return db_certificate

    async def invalidate_certificate(self, certificate_id: str) -> Optional[WipeCertificate]:
        """Invalidate a certificate"""
        db_certificate = self.db.query(WipeCertificate).filter(
            WipeCertificate.certificate_id == certificate_id
        ).first()
        
        if not db_certificate:
            return None

        db_certificate.is_valid = False
        db_certificate.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_certificate)
        return db_certificate

    async def get_expired_certificates(self) -> List[WipeCertificate]:
        """Get all expired certificates"""
        return self.db.query(WipeCertificate).filter(
            WipeCertificate.expires_at < datetime.utcnow()
        ).all()

    async def get_certificate_stats(self) -> dict:
        """Get certificate statistics"""
        total_certificates = self.db.query(WipeCertificate).count()
        valid_certificates = self.db.query(WipeCertificate).filter(
            WipeCertificate.is_valid == True
        ).count()
        verified_certificates = self.db.query(WipeCertificate).filter(
            WipeCertificate.is_verified == True
        ).count()
        expired_certificates = self.db.query(WipeCertificate).filter(
            WipeCertificate.expires_at < datetime.utcnow()
        ).count()
        
        return {
            "total_certificates": total_certificates,
            "valid_certificates": valid_certificates,
            "verified_certificates": verified_certificates,
            "expired_certificates": expired_certificates,
            "invalid_certificates": total_certificates - valid_certificates
        }

    async def search_certificates(
        self,
        query: str = None,
        user_id: int = None,
        device_serial: str = None,
        org: str = None,
        wipe_method: str = None,
        is_valid: bool = None,
        is_verified: bool = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WipeCertificate]:
        """Search certificates with various filters"""
        query_obj = self.db.query(WipeCertificate)
        
        if query:
            query_obj = query_obj.filter(
                WipeCertificate.certificate_id.contains(query) |
                WipeCertificate.user_name.contains(query) |
                WipeCertificate.device_serial.contains(query)
            )
        
        if user_id:
            query_obj = query_obj.filter(WipeCertificate.user_id == user_id)
        
        if device_serial:
            query_obj = query_obj.filter(WipeCertificate.device_serial == device_serial)
        
        if org:
            query_obj = query_obj.filter(WipeCertificate.user_org == org)
        
        if wipe_method:
            query_obj = query_obj.filter(WipeCertificate.wipe_method == wipe_method)
        
        if is_valid is not None:
            query_obj = query_obj.filter(WipeCertificate.is_valid == is_valid)
        
        if is_verified is not None:
            query_obj = query_obj.filter(WipeCertificate.is_verified == is_verified)
        
        return query_obj.offset(skip).limit(limit).all()

    async def delete_certificate(self, certificate_id: str) -> bool:
        """Delete a certificate (soft delete by invalidating)"""
        db_certificate = self.db.query(WipeCertificate).filter(
            WipeCertificate.certificate_id == certificate_id
        ).first()
        
        if not db_certificate:
            return False

        # Soft delete by invalidating
        db_certificate.is_valid = False
        db_certificate.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
