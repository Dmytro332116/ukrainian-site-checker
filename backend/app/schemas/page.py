from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PageResponse(BaseModel):
    id: int
    scan_session_id: int
    url: str
    title: Optional[str] = None
    status_code: Optional[int] = None
    meta_description: Optional[str] = None
    has_favicon: bool = False
    depth: int
    scanned_at: datetime
    errors: List["ErrorResponse"] = []

    class Config:
        from_attributes = True


# Avoid circular imports
from app.schemas.error import ErrorResponse
PageResponse.model_rebuild()

