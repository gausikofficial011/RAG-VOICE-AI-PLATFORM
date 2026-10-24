"""
User Feedback Database Model (Human-in-the-loop & Evaluation Data)
"""

from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 for upvote, -1 for downvote
    feedback_type: Mapped[str] = mapped_column(String(50), default="HELPFUL", nullable=False)  # HELPFUL, INCORRECT, IRRELEVANT, MISSING_INFO, WRONG_CITATION, HALLUCINATION
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)  # PENDING, APPROVED_FOR_DATASET, REJECTED

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    message = relationship("Message", back_populates="feedback")

    __table_args__ = (
        Index("idx_feedback_tenant_rating", "tenant_id", "rating"),
    )
