"""
RAG Query & Citation Pydantic Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: int
    section: str
    snippet: str
    score: float


class LatencyMetrics(BaseModel):
    intent_ms: float = 0.0
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    llm_ms: float = 0.0
    grounding_ms: float = 0.0
    tts_ms: Optional[float] = 0.0
    total_ms: float = 0.0


class RAGQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    kb_id: Optional[str] = None
    conversation_id: Optional[str] = None
    audio_requested: bool = False
    language: Optional[str] = "en"


class RAGQueryResponse(BaseModel):
    answer: str
    conversation_id: str
    message_id: str
    intent: str
    retrieval_strategy: str
    grounding_score: float
    grounding_status: str  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED
    citations: List[CitationItem]
    latency: LatencyMetrics
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None


class FeedbackCreateRequest(BaseModel):
    message_id: str
    rating: int = Field(ge=-1, le=1)  # 1 or -1
    feedback_type: str = "HELPFUL"
    comment: Optional[str] = None
