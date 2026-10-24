"""
Audit Logging Service
Provides immutable audit record persistence for security events and compliance tracking.
"""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        tenant_id: str,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create and commit an immutable audit log record."""
        log_entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details or {},
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry


audit_service = AuditService()
