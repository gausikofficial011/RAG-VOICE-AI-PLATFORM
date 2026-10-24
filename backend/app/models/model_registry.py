"""
ML Model Registry & Training Run Database Models
"""

from datetime import datetime, timezone
from typing import Optional, List
import uuid
from sqlalchemy import String, Text, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # INTENT, ROUTER, DOC_CLASS, GROUNDING, RERANKER, AUDIO
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    active_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_models.id", ondelete="CASCADE"), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)

    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Status: TRAINING, EVALUATING, CANDIDATE, APPROVED, DEPLOYED, RETIRED, FAILED
    status: Mapped[str] = mapped_column(String(30), default="CANDIDATE", nullable=False, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    model = relationship("MLModel", back_populates="versions")

    __table_args__ = (
        Index("idx_model_ver", "model_id", "version", unique=True),
    )


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(50), default="v1.0.0", nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="QUEUED", nullable=False)  # QUEUED, RUNNING, COMPLETED, FAILED
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    logs: Mapped[str] = mapped_column(Text, default="", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
