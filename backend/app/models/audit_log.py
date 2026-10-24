"""
Audit Log Database Model (Immutable Security Trail)
"""

from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import String, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    event_type: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="SUCCESS", nullable=False)  # SUCCESS, FAILURE
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_tenant_event_time", "tenant_id", "event_type", "timestamp"),
    )
