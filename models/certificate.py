from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class WipeCertificate(Base):
    __tablename__ = "wipe_certificates"

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wipe_log_id = Column(Integer, ForeignKey("wipe_logs.id"), nullable=True)
    
    # Certificate details
    user_name = Column(String(100), nullable=False)
    user_org = Column(String(100), nullable=False)
    device_serial = Column(String(50), nullable=False)
    device_model = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)
    
    # Wipe operation details
    wipe_method = Column(String(50), nullable=False)
    wipe_status = Column(String(50), nullable=False)
    target_path = Column(String(500), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    passes_completed = Column(Integer, nullable=False)
    total_passes = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)  # Stored as integer (seconds)
    verification_hash = Column(String(64), nullable=True)
    
    # File paths
    certificate_path = Column(String(500), nullable=False)
    json_path = Column(String(500), nullable=False)
    pdf_path = Column(String(500), nullable=False)
    signature_path = Column(String(500), nullable=False)
    
    # Certificate status
    is_valid = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="certificates")
    wipe_log = relationship("WipeLog", back_populates="certificate")

    def __repr__(self):
        return f"<WipeCertificate(id={self.id}, certificate_id='{self.certificate_id}', user_id={self.user_id})>"
