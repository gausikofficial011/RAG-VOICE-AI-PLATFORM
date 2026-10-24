"""
Knowledge Base Management API Router
Enforces strict tenant isolation across all KB operations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.document import Document
from backend.app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
)
from backend.app.security.rbac import Permission
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.retrieval.vector_store import vector_store
from backend.app.audit.service import audit_service

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(require_permission(Permission.KB_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new isolated knowledge base within tenant context."""
    kb = KnowledgeBase(
        tenant_id=current_user.tenant_id,
        name=data.name,
        description=data.description,
        embedding_model=data.embedding_model or "all-MiniLM-L6-v2",
        retrieval_strategy=data.retrieval_strategy or "hybrid",
        chunk_size=data.chunk_size or 500,
        chunk_overlap=data.chunk_overlap or 80,
        similarity_threshold=data.similarity_threshold or 0.3,
        top_k=data.top_k or 5,
        rerank_k=data.rerank_k or 3,
        created_by=current_user.id,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)

    await audit_service.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        event_type="KB_CREATE",
        action=f"Created knowledge base '{kb.name}'",
        resource_type="knowledge_base",
        resource_id=kb.id,
    )

    return KnowledgeBaseResponse(
        id=kb.id,
        tenant_id=kb.tenant_id,
        name=kb.name,
        description=kb.description,
        embedding_model=kb.embedding_model,
        retrieval_strategy=kb.retrieval_strategy,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
        similarity_threshold=kb.similarity_threshold,
        top_k=kb.top_k,
        rerank_k=kb.rerank_k,
        document_count=0,
        created_by=kb.created_by,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: User = Depends(require_permission(Permission.KB_READ)),
    db: AsyncSession = Depends(get_db),
):
    """List all knowledge bases for the current organization tenant."""
    stmt = (
        select(KnowledgeBase, func.count(Document.id).label("doc_count"))
        .outerjoin(Document, Document.kb_id == KnowledgeBase.id)
        .where(KnowledgeBase.tenant_id == current_user.tenant_id)
        .group_by(KnowledgeBase.id)
    )
    res = await db.execute(stmt)
    rows = res.all()

    return [
        KnowledgeBaseResponse(
            id=kb.id,
            tenant_id=kb.tenant_id,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            retrieval_strategy=kb.retrieval_strategy,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            similarity_threshold=kb.similarity_threshold,
            top_k=kb.top_k,
            rerank_k=kb.rerank_k,
            document_count=doc_count,
            created_by=kb.created_by,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        )
        for kb, doc_count in rows
    ]


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(require_permission(Permission.KB_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Get single knowledge base details."""
    stmt = select(KnowledgeBase).where(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id,
    )
    res = await db.execute(stmt)
    kb = res.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    doc_count_stmt = select(func.count(Document.id)).where(Document.kb_id == kb.id)
    doc_count = (await db.execute(doc_count_stmt)).scalar() or 0

    return KnowledgeBaseResponse(
        id=kb.id,
        tenant_id=kb.tenant_id,
        name=kb.name,
        description=kb.description,
        embedding_model=kb.embedding_model,
        retrieval_strategy=kb.retrieval_strategy,
        chunk_size=kb.chunk_size,
        chunk_overlap=kb.chunk_overlap,
        similarity_threshold=kb.similarity_threshold,
        top_k=kb.top_k,
        rerank_k=kb.rerank_k,
        document_count=doc_count,
        created_by=kb.created_by,
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(require_permission(Permission.KB_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    """Delete knowledge base, all its documents, and vector points."""
    stmt = select(KnowledgeBase).where(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id,
    )
    res = await db.execute(stmt)
    kb = res.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")

    # Delete all documents associated
    docs_stmt = select(Document).where(Document.kb_id == kb.id)
    docs_res = await db.execute(docs_stmt)
    for doc in docs_res.scalars().all():
        vector_store.delete_by_document(current_user.tenant_id, doc.id)

    await db.delete(kb)
    await db.commit()

    await audit_service.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        event_type="KB_DELETE",
        action=f"Deleted knowledge base '{kb.name}'",
        resource_type="knowledge_base",
        resource_id=kb_id,
    )

    return {"success": True, "message": "Knowledge base deleted successfully."}
