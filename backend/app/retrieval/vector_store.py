"""
Qdrant Vector Store Service
Handles collection management, point indexing, filtered vector queries, and point deletion.
Enforces multi-tenant payload filtering (tenant_id, kb_id).
Resiliently connects to Qdrant server with automatic local storage fallback.
"""

import logging
from typing import Any, Dict, List, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_chunks"


class VectorStoreService:
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self._init_client()

    def _init_client(self):
        import socket
        try:
            # Fast socket check to verify if port 6333 is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(('127.0.0.1', 6333))
            sock.close()
            if result == 0:
                client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=1.0,
                    check_compatibility=False,
                )
                client.get_collections()
                self.client = client
                logger.info(f"Connected to remote Qdrant at {settings.QDRANT_URL}")
            else:
                raise ConnectionError("Qdrant port 6333 not listening")
        except Exception:
            try:
                self.client = QdrantClient(path=settings.QDRANT_STORAGE_PATH)
            except Exception:
                self.client = QdrantClient(location=":memory:")

        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the vector collection exists with cosine distance metric."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == COLLECTION_NAME for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error checking/creating Qdrant collection: {e}")

    def index_chunks(
        self,
        tenant_id: str,
        kb_id: str,
        doc_id: str,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> bool:
        """
        Index chunk vectors with metadata payload in Qdrant.
        """
        points = []
        for chunk, vector in zip(chunks, vectors):
            point_id = chunk.get("chunk_id") or str(uuid.uuid4())
            payload = {
                "tenant_id": tenant_id,
                "kb_id": kb_id,
                "doc_id": doc_id,
                "chunk_id": point_id,
                "chunk_index": chunk.get("chunk_index", 0),
                "content": chunk.get("content", ""),
                "page_number": chunk.get("page_number", 1),
                "section": chunk.get("section", "General"),
                "token_count": chunk.get("token_count", 0),
                "filename": chunk.get("filename", ""),
            }
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        if points:
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
            )
        return True

    def search(
        self,
        tenant_id: str,
        kb_id: Optional[str],
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for nearest neighbor vectors enforcing tenant and kb filters.
        """
        filter_conditions = [
            qmodels.FieldCondition(
                key="tenant_id",
                match=qmodels.MatchValue(value=tenant_id),
            )
        ]
        if kb_id:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="kb_id",
                    match=qmodels.MatchValue(value=kb_id),
                )
            )

        query_filter = qmodels.Filter(must=filter_conditions)

        # Execute search across modern query_points API or fallback search API
        formatted = []
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold if score_threshold > 0 else None,
                with_payload=True,
            )
            for res in response.points:
                formatted.append({
                    "chunk_id": res.id,
                    "score": float(res.score),
                    "payload": res.payload,
                })
        else:
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold if score_threshold > 0 else None,
            )
            for res in results:
                formatted.append({
                    "chunk_id": res.id,
                    "score": float(res.score),
                    "payload": res.payload,
                })
        return formatted

    def delete_by_document(self, tenant_id: str, doc_id: str) -> bool:
        """
        Delete all vector points associated with a specific document.
        Prevents orphaned vectors.
        """
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(key="tenant_id", match=qmodels.MatchValue(value=tenant_id)),
                        qmodels.FieldCondition(key="doc_id", match=qmodels.MatchValue(value=doc_id)),
                    ]
                )
            ),
        )
        return True


vector_store = VectorStoreService()
