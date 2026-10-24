"""
Document Management & Upload API Router
Coordinates upload validation, parsing, indexing, and cascade deletion.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.document import Document
from backend.app.models.chunk import DocumentChunk
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.schemas.document import (
    DocumentResponse,
    DocumentChunkResponse,
    IngestDocumentResponse,
)
from backend.app.security.rbac import Permission
from backend.app.auth.dependencies import get_current_user, require_permission
from backend.app.services.document_service import document_service
from backend.app.audit.service import audit_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=IngestDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission(Permission.DOC_UPLOAD)),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process document (PDF, DOCX, TXT, MD, CSV, HTML, JSON)."""
    # Verify Knowledge Base belongs to tenant
    stmt_kb = select(KnowledgeBase).where(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.tenant_id == current_user.tenant_id,
    )
    res_kb = await db.execute(stmt_kb)
    kb = res_kb.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="Target knowledge base not found in your organization.")

    # Validate file size (max 25MB)
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Cannot upload an empty file.")
    if len(file_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds maximum 25MB limit.")

    filename = file.filename or "uploaded_document"
    mime_type = file.content_type or "application/octet-stream"

    # Ingest document
    doc = await document_service.process_and_index_document(
        db=db,
        tenant_id=current_user.tenant_id,
        kb_id=kb.id,
        filename=filename,
        file_bytes=file_bytes,
        mime_type=mime_type,
        user_id=current_user.id,
    )

    await audit_service.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        event_type="DOC_UPLOAD",
        action=f"Uploaded and indexed document '{filename}'",
        resource_type="document",
        resource_id=doc.id,
        details={"chunks": doc.chunk_count, "classification": doc.classification},
    )

    return IngestDocumentResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        chunks_created=doc.chunk_count,
        classification=doc.classification,
        message="Document successfully processed and indexed into vector store.",
    )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: Optional[str] = None,
    current_user: User = Depends(require_permission(Permission.DOC_READ)),
    db: AsyncSession = Depends(get_db),
):
    """List documents in organization, optionally filtered by knowledge base."""
    stmt = select(Document).where(Document.tenant_id == current_user.tenant_id)
    if kb_id:
        stmt = stmt.where(Document.kb_id == kb_id)
    stmt = stmt.order_by(Document.created_at.desc())

    res = await db.execute(stmt)
    docs = res.scalars().all()

    return [
        DocumentResponse(
            id=d.id,
            tenant_id=d.tenant_id,
            kb_id=d.kb_id,
            filename=d.filename,
            file_size=d.file_size,
            mime_type=d.mime_type,
            classification=d.classification,
            status=d.status,
            error_message=d.error_message,
            token_count=d.token_count,
            chunk_count=d.chunk_count,
            doc_metadata=d.doc_metadata,
            uploaded_by=d.uploaded_by,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.get("/{doc_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    doc_id: str,
    current_user: User = Depends(require_permission(Permission.DOC_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve fine-grained chunk provenance and text snippets."""
    stmt_doc = select(Document).where(Document.id == doc_id, Document.tenant_id == current_user.tenant_id)
    res_doc = await db.execute(stmt_doc)
    doc = res_doc.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    stmt_chunks = select(DocumentChunk).where(DocumentChunk.doc_id == doc_id).order_by(DocumentChunk.chunk_index)
    res_chunks = await db.execute(stmt_chunks)
    chunks = res_chunks.scalars().all()

    return [
        DocumentChunkResponse(
            id=c.id,
            doc_id=c.doc_id,
            chunk_index=c.chunk_index,
            content=c.content,
            token_count=c.token_count,
            page_number=c.page_number,
            section=c.section,
            chunk_metadata=c.chunk_metadata,
        )
        for c in chunks
    ]


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(require_permission(Permission.DOC_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    """Delete document, vector embeddings, and storage files."""
    deleted = await document_service.delete_document(
        db=db,
        tenant_id=current_user.tenant_id,
        doc_id=doc_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")

    await audit_service.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        event_type="DOC_DELETE",
        action="Deleted document and vector points",
        resource_type="document",
        resource_id=doc_id,
    )

    return {"success": True, "message": "Document and all vector embeddings deleted."}
