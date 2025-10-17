from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from urllib.parse import urlparse

from app.core.database import get_db
from app.models import Website
from app.schemas.website import WebsiteCreate, WebsiteUpdate, WebsiteResponse

router = APIRouter()


@router.post("/", response_model=WebsiteResponse, status_code=201)
async def create_website(
    website_in: WebsiteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new website to monitor."""
    # Extract domain from URL
    parsed = urlparse(website_in.url)
    domain = parsed.netloc
    
    # Check if website already exists
    result = await db.execute(
        select(Website).where(Website.url == website_in.url)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Website already exists")
    
    # Create website
    website = Website(
        url=website_in.url,
        domain=domain,
        name=website_in.name or domain,
        preferences=website_in.preferences,
    )
    
    db.add(website)
    await db.commit()
    await db.refresh(website)
    
    return website


@router.get("/", response_model=List[WebsiteResponse])
async def list_websites(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all websites."""
    result = await db.execute(
        select(Website).offset(skip).limit(limit)
    )
    websites = result.scalars().all()
    return websites


@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get website by ID."""
    result = await db.execute(
        select(Website).where(Website.id == website_id)
    )
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    return website


@router.patch("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: int,
    website_in: WebsiteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update website settings."""
    result = await db.execute(
        select(Website).where(Website.id == website_id)
    )
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    # Update fields
    if website_in.name is not None:
        website.name = website_in.name
    if website_in.preferences is not None:
        website.preferences = website_in.preferences
    
    await db.commit()
    await db.refresh(website)
    
    return website


@router.delete("/{website_id}", status_code=204)
async def delete_website(
    website_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a website and all its scan sessions."""
    result = await db.execute(
        select(Website).where(Website.id == website_id)
    )
    website = result.scalar_one_or_none()
    
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    
    await db.delete(website)
    await db.commit()
    
    return None

