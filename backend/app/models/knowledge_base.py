"""
Knowledge Base Database Model
"""

from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import String, Boolean, DateTime, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Retrieval and RAG Configuration
    embedding_model: Mapped[str] = mapped_column(String(100), default="all-MiniLM-L6-v2", nullable=False)
    retrieval_strategy: Mapped[str] = mapped_column(String(50), default="hybrid", nullable=False)  # hybrid, dense, sparse
    chunk_size: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    rerank_k: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    extra_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="knowledge_bases")
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="knowledge_base", cascade="all, delete-orphan")
