"""
Conversation and Message Database Models
Stores chat history, voice audio references, citations, grounding scores, and latency metrics.
"""

from datetime import datetime, timezone
from typing import Optional, List
import uuid
from sqlalchemy import String, Text, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    kb_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("knowledge_bases.id", ondelete="SET NULL"), index=True, nullable=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(200), default="New Conversation", nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="conversations")
    knowledge_base = relationship("KnowledgeBase", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Observability & Trace Provenance
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retrieval_strategy: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    grounding_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grounding_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED

    # Citations list: [{"document_id": "...", "filename": "...", "page": 1, "section": "...", "snippet": "...", "score": 0.89}]
    citations: Mapped[List[dict]] = mapped_column(JSON, default=list, nullable=False)

    # Detailed Latency Waterfall: {"vad_ms": 12, "stt_ms": 140, "retrieval_ms": 45, "rerank_ms": 30, "llm_ms": 620, "tts_ms": 180, "total_ms": 1027}
    latency_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship("UserFeedback", back_populates="message", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_msg_conv_created", "conversation_id", "created_at"),
    )
