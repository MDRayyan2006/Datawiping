from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum


class WipeMethod(str, enum.Enum):
    SECURE_DELETE = "secure_delete"
    OVERWRITE = "overwrite"
    SHRED = "shred"
    CRYPTO_WIPE = "crypto_wipe"
    PHYSICAL_DESTRUCTION = "physical_destruction"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    NOT_REQUIRED = "not_required"


class WipeLog(Base):
    __tablename__ = "wipe_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wipe_method = Column(Enum(WipeMethod), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    certificate_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="wipe_logs")
    certificate = relationship("WipeCertificate", back_populates="wipe_log", uselist=False)

    def __repr__(self):
        return f"<WipeLog(id={self.id}, user_id={self.user_id}, wipe_method='{self.wipe_method}', verification_status='{self.verification_status}')>"
