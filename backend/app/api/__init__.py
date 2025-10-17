from fastapi import APIRouter
from app.api import websites, scan_sessions, pages, errors, reports

api_router = APIRouter()

api_router.include_router(websites.router, prefix="/websites", tags=["websites"])
api_router.include_router(scan_sessions.router, prefix="/scans", tags=["scans"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(errors.router, prefix="/errors", tags=["errors"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

