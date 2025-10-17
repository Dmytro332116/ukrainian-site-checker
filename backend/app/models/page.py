from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    scan_session_id = Column(Integer, ForeignKey("scan_sessions.id", ondelete="CASCADE"), nullable=False)
    
    url = Column(String(1000), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # Content
    html_content = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)
    
    # Meta information
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(Text, nullable=True)
    has_favicon = Column(Boolean, default=False)
    
    # Depth in site structure
    depth = Column(Integer, default=0)
    
    # Timestamps
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scan_session = relationship("ScanSession", back_populates="pages")
    errors = relationship("Error", back_populates="page", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Page(id={self.id}, url='{self.url}')>"

