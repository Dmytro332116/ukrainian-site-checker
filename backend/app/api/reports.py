from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import ScanSession
from app.services.report_generator import ReportGenerator

router = APIRouter()


@router.get("/{scan_id}/html", response_class=HTMLResponse)
async def generate_html_report(
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate HTML report for scan session."""
    result = await db.execute(
        select(ScanSession)
        .options(
            selectinload(ScanSession.website),
            selectinload(ScanSession.pages).selectinload('errors')
        )
        .where(ScanSession.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan session not found")
    
    generator = ReportGenerator()
    html = generator.generate_html_report(scan)
    
    return HTMLResponse(content=html)


@router.get("/{scan_id}/pdf")
async def generate_pdf_report(
    scan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate PDF report for scan session."""
    result = await db.execute(
        select(ScanSession)
        .options(
            selectinload(ScanSession.website),
            selectinload(ScanSession.pages).selectinload('errors')
        )
        .where(ScanSession.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan session not found")
    
    generator = ReportGenerator()
    pdf = generator.generate_pdf_report(scan)
    
    filename = f"scan_report_{scan_id}.pdf"
    
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

