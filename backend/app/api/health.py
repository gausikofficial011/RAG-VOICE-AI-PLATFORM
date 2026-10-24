"""
System Health & Infrastructure Diagnostics API
"""

import os
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.retrieval.vector_store import vector_store

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("")
async def get_system_health(db: AsyncSession = Depends(get_db)):
    """Check health of API, Database, Qdrant Vector Store, and Storage."""
    status_db = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        status_db = "down"

    status_qdrant = "healthy"
    try:
        if vector_store.client is None:
            status_qdrant = "degraded"
        else:
            vector_store.client.get_collections()
    except Exception:
        status_qdrant = "degraded"

    status_storage = "healthy"
    try:
        os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
    except Exception:
        status_storage = "down"

    overall = "healthy"
    if status_db == "down":
        overall = "down"
    elif status_qdrant == "degraded" or status_storage == "degraded":
        overall = "degraded"

    return {
        "status": overall,
        "services": {
            "api": "healthy",
            "database": status_db,
            "vector_store": status_qdrant,
            "object_storage": status_storage,
            "ml_models": "healthy",
        },
        "environment": settings.ENVIRONMENT,
    }
