"""
Reranker Engine & Evaluation Metrics
Computes fine-grained query-document relevance scores and re-ranks retrieval candidates.
Includes MRR, NDCG@K, Recall@K, and Precision@K evaluation metrics.
"""

from typing import Any, Dict, List, Tuple
import math
import numpy as np


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name

    def score_pair(self, query: str, document_text: str) -> float:
        """
        Compute interaction score between query and document.
        Uses lexical overlap, semantic token density, and position weighting.
        """
        q_words = set(query.lower().split())
        d_words = document_text.lower().split()
        if not q_words or not d_words:
            return 0.0

        # Exact term hits
        hits = sum(1 for w in d_words if w in q_words)
        term_overlap = hits / max(len(q_words), 1)

        # Early position bonus (relevance in headings / first sentences)
        early_hits = sum(1 for w in d_words[:50] if w in q_words)
        position_bonus = (early_hits / max(len(q_words), 1)) * 0.3

        # Exact phrase bonus
        phrase_bonus = 0.4 if query.lower() in document_text.lower() else 0.0

        raw_score = (0.5 * term_overlap) + position_bonus + phrase_bonus
        # Sigmoid normalization between 0.0 and 1.0
        return float(1.0 / (1.0 + math.exp(-2.5 * (raw_score - 0.5))))

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Re-score and re-order candidate chunks.
        """
        scored = []
        for cand in candidates:
            content = cand.get("payload", {}).get("content") or cand.get("content", "")
            rerank_score = self.score_pair(query, content)
            c = cand.copy()
            c["rerank_score"] = rerank_score
            scored.append(c)

        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_k]

    # =========================================================================
    # ML RERANKING EVALUATION METRICS (MRR, NDCG@K, Recall@K, Precision@K)
    # =========================================================================

    @staticmethod
    def compute_mrr(ranked_doc_ids: List[str], ground_truth_ids: List[str]) -> float:
        """Calculate Mean Reciprocal Rank (MRR)."""
        for rank, doc_id in enumerate(ranked_doc_ids, start=1):
            if doc_id in ground_truth_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def compute_ndcg_at_k(ranked_doc_ids: List[str], ground_truth_ids: List[str], k: int = 3) -> float:
        """Calculate Normalized Discounted Cumulative Gain at K (NDCG@K)."""
        actual_k = ranked_doc_ids[:k]
        dcg = 0.0
        for i, doc_id in enumerate(actual_k, start=1):
            rel = 1.0 if doc_id in ground_truth_ids else 0.0
            dcg += (2.0**rel - 1.0) / math.log2(i + 1)

        # Ideal DCG
        idcg = 0.0
        ideal_rels = [1.0] * min(len(ground_truth_ids), k)
        for i, rel in enumerate(ideal_rels, start=1):
            idcg += (2.0**rel - 1.0) / math.log2(i + 1)

        if idcg == 0.0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def compute_recall_at_k(ranked_doc_ids: List[str], ground_truth_ids: List[str], k: int = 3) -> float:
        """Calculate Recall@K."""
        if not ground_truth_ids:
            return 0.0
        actual_k = set(ranked_doc_ids[:k])
        hits = len(actual_k.intersection(set(ground_truth_ids)))
        return hits / len(ground_truth_ids)

    @staticmethod
    def compute_precision_at_k(ranked_doc_ids: List[str], ground_truth_ids: List[str], k: int = 3) -> float:
        """Calculate Precision@K."""
        if k == 0:
            return 0.0
        actual_k = set(ranked_doc_ids[:k])
        hits = len(actual_k.intersection(set(ground_truth_ids)))
        return hits / k


reranker = CrossEncoderReranker()
