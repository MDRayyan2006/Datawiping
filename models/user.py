from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    org = Column(String(100), nullable=False, index=True)
    device_serial = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    wipe_logs = relationship("WipeLog", back_populates="user")
    certificates = relationship("WipeCertificate", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', org='{self.org}', device_serial='{self.device_serial}')>"
