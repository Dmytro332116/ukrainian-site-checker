from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models import Error
from app.models.error import ErrorType, ErrorSeverity
from app.schemas.error import ErrorResponse

router = APIRouter()


@router.get("/scan/{scan_id}", response_model=List[ErrorResponse])
async def list_errors_by_scan(
    scan_id: int,
    error_type: Optional[ErrorType] = Query(None),
    severity: Optional[ErrorSeverity] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List all errors for a scan session, optionally filtered by type and severity."""
    # Join with Page to filter by scan_id
    query = select(Error).join(Error.page).where(Error.page.has(scan_session_id=scan_id))
    
    if error_type:
        query = query.where(Error.error_type == error_type)
    
    if severity:
        query = query.where(Error.severity == severity)
    
    result = await db.execute(query)
    errors = result.scalars().all()
    return errors


@router.get("/page/{page_id}", response_model=List[ErrorResponse])
async def list_errors_by_page(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all errors for a specific page."""
    result = await db.execute(
        select(Error).where(Error.page_id == page_id)
    )
    errors = result.scalars().all()
    return errors


@router.get("/{error_id}", response_model=ErrorResponse)
async def get_error(
    error_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get error details."""
    result = await db.execute(
        select(Error).where(Error.id == error_id)
    )
    error = result.scalar_one_or_none()
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    return error

