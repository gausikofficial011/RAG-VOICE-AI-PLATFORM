"""
Organization Administration API Router
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.schemas.organization import OrganizationResponse, OrganizationUpdate
from backend.app.security.rbac import Permission
from backend.app.auth.dependencies import get_current_user, require_permission

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/current", response_model=OrganizationResponse)
async def get_current_org(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current tenant organization."""
    stmt = select(Organization).where(Organization.id == current_user.tenant_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        settings=org.settings,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


@router.get("/users")
async def list_org_users(
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """List all users within the current organization."""
    stmt = select(User).where(User.tenant_id == current_user.tenant_id).order_by(User.created_at)
    res = await db.execute(stmt)
    users = res.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "mfa_enabled": u.mfa_enabled,
            "created_at": u.created_at,
        }
        for u in users
    ]
