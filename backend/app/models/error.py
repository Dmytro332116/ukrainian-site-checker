from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ErrorType(str, enum.Enum):
    SPELLING = "spelling"
    ADDRESS = "address"
    BROKEN_LINK = "broken_link"
    SEO = "seo"
    PHONE = "phone"


class ErrorSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Error(Base):
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False)
    
    error_type = Column(SQLEnum(ErrorType), nullable=False, index=True)
    severity = Column(SQLEnum(ErrorSeverity), default=ErrorSeverity.WARNING, nullable=False)
    
    # Error details
    message = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # Surrounding text for context
    suggestion = Column(Text, nullable=True)  # Suggested fix
    
    # Location in page
    line_number = Column(Integer, nullable=True)
    column_number = Column(Integer, nullable=True)
    
    # For links
    link_url = Column(String(1000), nullable=True)
    link_status_code = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    page = relationship("Page", back_populates="errors")
    
    # Polymorphic identity
    __mapper_args__ = {
        "polymorphic_identity": "error",
        "polymorphic_on": error_type,
    }
    
    def __repr__(self):
        return f"<Error(id={self.id}, type='{self.error_type}')>"


class SpellingError(Error):
    """Spelling and grammar errors."""
    __mapper_args__ = {
        "polymorphic_identity": ErrorType.SPELLING,
    }


class AddressError(Error):
    """Ukrainian address format errors."""
    __mapper_args__ = {
        "polymorphic_identity": ErrorType.ADDRESS,
    }


class BrokenLink(Error):
    """Broken or invalid links."""
    __mapper_args__ = {
        "polymorphic_identity": ErrorType.BROKEN_LINK,
    }


class SEOIssue(Error):
    """SEO-related issues (missing favicon, robots.txt, etc.)."""
    __mapper_args__ = {
        "polymorphic_identity": ErrorType.SEO,
    }


class PhoneError(Error):
    """Phone number validation errors."""
    __mapper_args__ = {
        "polymorphic_identity": ErrorType.PHONE,
    }

