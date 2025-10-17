from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False, unique=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    
    # Settings for scanning
    preferences = Column(JSON, nullable=False, default={
        "check_spelling": True,
        "check_addresses": True,
        "check_links": True,
        "check_phones": True,
        "check_seo": True,
        "max_pages": 100,
        "max_depth": 5,
        "exclude_paths": [],
        "whitelist_words": [],
    })
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    scan_sessions = relationship("ScanSession", back_populates="website", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Website(id={self.id}, domain='{self.domain}')>"

