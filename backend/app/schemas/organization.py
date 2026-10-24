"""
Organization Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool
    settings: dict
    created_at: datetime
    updated_at: datetime
