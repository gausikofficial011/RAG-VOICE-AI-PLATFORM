"""
Auditor & Security Trail API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.audit_log import AuditLog
from backend.app.security.rbac import Permission
from backend.app.auth.dependencies import require_permission

router = APIRouter(prefix="/audit", tags=["Security & Audit"])


@router.get("/logs")
async def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve immutable audit events for the organization."""
    stmt = select(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id)
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit)

    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        {
            "id": l.id,
            "event_type": l.event_type,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "user_id": l.user_id,
            "ip_address": l.ip_address,
            "status": l.status,
            "details": l.details,
            "timestamp": l.timestamp,
        }
        for l in logs
    ]
