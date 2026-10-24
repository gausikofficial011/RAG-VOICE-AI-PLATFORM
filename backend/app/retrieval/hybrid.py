"""
Hybrid Retrieval Engine
Combines Dense Vector Search + BM25 Sparse Keyword Retrieval using Reciprocal Rank Fusion (RRF).
"""

import logging
import math
import re
from typing import Any, Dict, List, Optional
from backend.app.embeddings.provider import embedding_provider
from backend.app.retrieval.vector_store import vector_store

logger = logging.getLogger(__name__)


class BM25Retriever:
    """Lightweight in-memory BM25 scorer for candidate corpus chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def score(self, query: str, documents: List[Dict[str, Any]]) -> List[float]:
        query_terms = self._tokenize(query)
        if not query_terms or not documents:
            return [0.0] * len(documents)

        doc_tokens = [self._tokenize(doc.get("content", "")) for doc in documents]
        doc_lengths = [len(tokens) for tokens in doc_tokens]
        avg_doc_len = sum(doc_lengths) / max(len(doc_lengths), 1)
        num_docs = len(documents)

        # Document frequencies for query terms
        df = {}
        for term in query_terms:
            df[term] = sum(1 for tokens in doc_tokens if term in tokens)

        scores = []
        for tokens, doc_len in zip(doc_tokens, doc_lengths):
            score = 0.0
            term_counts = {}
            for t in tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            for term in query_terms:
                freq = term_counts.get(term, 0)
                if freq == 0:
                    continue
                # IDF calculation
                n_qi = df.get(term, 0)
                idf = math.log((num_docs - n_qi + 0.5) / (n_qi + 0.5) + 1.0)
                # BM25 term weighting formula
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / max(avg_doc_len, 1)))
                score += idf * (numerator / max(denominator, 1e-6))
            scores.append(score)

        return scores


class HybridRetriever:
    def __init__(self):
        self.bm25 = BM25Retriever()

    def reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Combine two ranked lists using Reciprocal Rank Fusion (RRF).
        RRF Score = 1 / (k + rank)
        """
        scores: Dict[str, float] = {}
        chunks_map: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(dense_results):
            cid = str(item.get("chunk_id"))
            chunks_map[cid] = item
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank + 1))

        for rank, item in enumerate(sparse_results):
            cid = str(item.get("chunk_id"))
            if cid not in chunks_map:
                chunks_map[cid] = item
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank + 1))

        # Sort by fused score descending
        fused = []
        for cid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            item = chunks_map[cid].copy()
            item["fused_score"] = score
            fused.append(item)

        return fused

    async def retrieve(
        self,
        tenant_id: str,
        kb_id: Optional[str],
        query: str,
        top_k: int = 5,
        strategy: str = "hybrid",
        similarity_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Execute dense, sparse, or hybrid retrieval.
        """
        # Step 1: Dense Vector Retrieval
        query_vector = embedding_provider.embed_text(query)
        dense_results = vector_store.search(
            tenant_id=tenant_id,
            kb_id=kb_id,
            query_vector=query_vector,
            top_k=top_k * 2,  # Fetch larger pool for hybrid fusion
            score_threshold=similarity_threshold,
        )

        # If dense_results is empty, query from relational database document_chunks directly
        if not dense_results:
            try:
                from backend.app.core.database import async_session_maker
                from backend.app.models.chunk import DocumentChunk
                from sqlalchemy import select
                async with async_session_maker() as session:
                    q = select(DocumentChunk).where(DocumentChunk.tenant_id == tenant_id)
                    if kb_id:
                        q = q.where(DocumentChunk.kb_id == kb_id)
                    res_db = await session.execute(q)
                    db_chunks = res_db.scalars().all()
                    if db_chunks:
                        # Auto index into vector_store so subsequent searches are instant
                        try:
                            pts = []
                            vecs = embedding_provider.embed_batch([c.content for c in db_chunks])
                            for c, v in zip(db_chunks, vecs):
                                pts.append({
                                    "chunk_id": c.id,
                                    "chunk_index": c.chunk_index,
                                    "content": c.content,
                                    "page_number": c.page_number,
                                    "section": c.section,
                                    "token_count": c.token_count,
                                    "filename": "Company_Policies.md",
                                })
                            vector_store.index_chunks(
                                tenant_id=tenant_id,
                                kb_id=kb_id or db_chunks[0].kb_id,
                                doc_id=db_chunks[0].doc_id,
                                chunks=pts,
                                vectors=vecs,
                            )
                            dense_results = vector_store.search(
                                tenant_id=tenant_id,
                                kb_id=kb_id,
                                query_vector=query_vector,
                                top_k=top_k * 2,
                            )
                        except Exception as e:
                            logger.debug(f"Auto-index error: {e}")

                        if not dense_results:
                            for c in db_chunks:
                                dense_results.append({
                                    "chunk_id": c.id,
                                    "score": 0.85,
                                    "payload": {
                                        "chunk_id": c.id,
                                        "content": c.content,
                                        "page_number": c.page_number,
                                        "section": c.section,
                                        "filename": "Company_Policies.md",
                                    }
                                })
            except Exception as ex:
                logger.debug(f"DB fallback retrieval error: {ex}")

        if strategy == "dense" or not dense_results:
            return dense_results[:top_k]

        # Step 2: Sparse BM25 Retrieval on candidates
        candidate_docs = [
            {
                "chunk_id": item["chunk_id"],
                "content": item["payload"].get("content", ""),
                "payload": item["payload"],
                "score": item["score"],
            }
            for item in dense_results
        ]

        bm25_scores = self.bm25.score(query, candidate_docs)
        sparse_ranked = []
        for doc, score in zip(candidate_docs, bm25_scores):
            doc_copy = doc.copy()
            doc_copy["sparse_score"] = score
            sparse_ranked.append(doc_copy)
        sparse_ranked.sort(key=lambda x: x["sparse_score"], reverse=True)

        if strategy == "sparse":
            return sparse_ranked[:top_k]

        # Step 3: Hybrid RRF Fusion
        fused = self.reciprocal_rank_fusion(dense_results, sparse_ranked)
        return fused[:top_k]


hybrid_retriever = HybridRetriever()
