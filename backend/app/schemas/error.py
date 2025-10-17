from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.error import ErrorType, ErrorSeverity


class ErrorResponse(BaseModel):
    id: int
    page_id: int
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: Optional[str] = None
    suggestion: Optional[str] = None
    link_url: Optional[str] = None
    link_status_code: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

