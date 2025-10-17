from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.scan_session import ScanStatus


class ScanSessionCreate(BaseModel):
    website_id: int


class ScanSessionResponse(BaseModel):
    id: int
    website_id: int
    status: ScanStatus
    pages_found: int
    pages_processed: int
    errors_found: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanSessionDetail(ScanSessionResponse):
    """Extended response with pages and errors."""
    pages: List["PageResponse"] = []

    class Config:
        from_attributes = True


# Avoid circular imports
from app.schemas.page import PageResponse
ScanSessionDetail.model_rebuild()

