from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False)
    
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False, index=True)
    
    # Statistics
    pages_found = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    errors_found = Column(Integer, default=0)
    
    # Error message if failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    website = relationship("Website", back_populates="scan_sessions")
    pages = relationship("Page", back_populates="scan_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScanSession(id={self.id}, status='{self.status}')>"

