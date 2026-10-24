"""
Knowledge Base Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = None
    embedding_model: Optional[str] = "all-MiniLM-L6-v2"
    retrieval_strategy: Optional[str] = "hybrid"  # hybrid, dense, sparse
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 80
    similarity_threshold: Optional[float] = 0.3
    top_k: Optional[int] = 5
    rerank_k: Optional[int] = 3


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    retrieval_strategy: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    similarity_threshold: Optional[float] = None
    top_k: Optional[int] = None
    rerank_k: Optional[int] = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    embedding_model: str
    retrieval_strategy: str
    chunk_size: int
    chunk_overlap: int
    similarity_threshold: float
    top_k: int
    rerank_k: int
    document_count: Optional[int] = 0
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
