"""
Document & Chunk Pydantic Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    tenant_id: str
    kb_id: str
    filename: str
    file_size: int
    mime_type: str
    classification: str
    status: str
    error_message: Optional[str]
    token_count: int
    chunk_count: int
    doc_metadata: dict
    uploaded_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class DocumentChunkResponse(BaseModel):
    id: str
    doc_id: str
    chunk_index: int
    content: str
    token_count: int
    page_number: int
    section: str
    chunk_metadata: dict


class IngestDocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_created: int
    classification: str
    message: str
