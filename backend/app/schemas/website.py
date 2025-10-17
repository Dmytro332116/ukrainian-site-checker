from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class WebsiteBase(BaseModel):
    url: str
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = Field(default_factory=lambda: {
        "check_spelling": True,
        "check_addresses": True,
        "check_links": True,
        "check_phones": True,
        "check_seo": True,
        "max_pages": 100,
        "max_depth": 5,
        "exclude_paths": [],
        "whitelist_words": [],
    })


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class WebsiteResponse(WebsiteBase):
    id: int
    domain: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

