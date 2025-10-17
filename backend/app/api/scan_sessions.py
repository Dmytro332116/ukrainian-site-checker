from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.models import ScanSession, Website, Page
from app.models.scan_session import ScanStatus
from app.schemas.scan_session import ScanSessionCreate, ScanSessionResponse, ScanSessionDetail
from app.tasks.scan_website import scan_website_task

router = APIRouter()


@router.post("/", response_model=ScanSessionResponse, status_code=201)
async def create_scan(
    scan_in: ScanSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scan session and start scanning."""
    # Check if website exists
    result = await db.execute(
        select(Website).where(Website.id == scan_in.website_id)
    )
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Create scan session
    scan_session = ScanSession(
        website_id=website.id,
        status=ScanStatus.PENDING,
    )
    
    db.add(scan_session)
    await db.commit()
    await db.refresh(scan_session)
    
    # Start scan in background (Celery)
    scan_website_task.delay(scan_session.id)
    
    return scan_session


@router.get("/", response_model=List[ScanSessionResponse])
async def list_scans(
    website_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all scan sessions, optionally filtered by website."""
    query = select(ScanSession)
    
    if website_id:
        query = query.where(ScanSession.website_id == website_id)
    
    query = query.order_by(ScanSession.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    scans = result.scalars().all()
    return scans


@router.get("/{scan_id}", response_model=ScanSessionDetail)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get scan session details with all pages and errors."""
    result = await db.execute(
        select(ScanSession)
        .options(
            selectinload(ScanSession.pages).selectinload(Page.errors)
        )
        .where(ScanSession.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan session not found")
    
    return scan


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a scan session and all its data."""
    result = await db.execute(
        select(ScanSession).where(ScanSession.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan session not found")
    
    await db.delete(scan)
    await db.commit()
    
    return None


@router.get("/{scan_id}/status")
async def get_scan_status(
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get current status of scan session."""
    result = await db.execute(
        select(ScanSession).where(ScanSession.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan session not found")
    
    return {
        "id": scan.id,
        "status": scan.status,
        "pages_found": scan.pages_found,
        "pages_processed": scan.pages_processed,
        "errors_found": scan.errors_found,
        "progress": (scan.pages_processed / scan.pages_found * 100) if scan.pages_found > 0 else 0,
    }

