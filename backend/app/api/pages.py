from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.models import Page
from app.schemas.page import PageResponse

router = APIRouter()


@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get page details with errors."""
    result = await db.execute(
        select(Page)
        .options(selectinload(Page.errors))
        .where(Page.id == page_id)
    )
    page = result.scalar_one_or_none()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return page


@router.get("/scan/{scan_id}", response_model=List[PageResponse])
async def list_pages_by_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all pages for a scan session."""
    result = await db.execute(
        select(Page)
        .options(selectinload(Page.errors))
        .where(Page.scan_session_id == scan_id)
    )
    pages = result.scalars().all()
    return pages

