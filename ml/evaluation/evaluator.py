"""
Model G — Answer Quality & RAG Triad Evaluator
Evaluates:
- Answer Relevance
- Context Relevance
- Faithfulness (Hallucination metric)
- Citation Correctness
"""

from typing import Any, Dict, List
import re
from backend.app.rag.grounding import grounding_validator


class AnswerQualityEvaluator:
    @staticmethod
    def _token_overlap(str1: str, str2: str) -> float:
        w1 = set(re.findall(r"\w+", str1.lower()))
        w2 = set(re.findall(r"\w+", str2.lower()))
        if not w1 or not w2:
            return 0.0
        return len(w1.intersection(w2)) / max(len(w1), 1)

    def evaluate_triad(
        self,
        query: str,
        retrieved_context: str,
        generated_answer: str,
        citations: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate full RAG quality triad metrics.
        """
        citations = citations or []

        # 1. Answer Relevance (does the answer address query terms?)
        answer_rel = self._token_overlap(query, generated_answer)
        answer_relevance_score = round(min(1.0, answer_rel * 1.5 + 0.3), 3)

        # 2. Context Relevance (does retrieved context contain query keywords?)
        context_rel = self._token_overlap(query, retrieved_context)
        context_relevance_score = round(min(1.0, context_rel * 1.8), 3)

        # 3. Faithfulness (Grounding of answer in context)
        grounding_result = grounding_validator.validate(
            query=query,
            retrieved_chunks=[{"content": retrieved_context}],
            generated_answer=generated_answer,
        )
        faithfulness_score = grounding_result["grounding_score"]

        # 4. Citation Correctness (verify citations exist in context)
        citation_correctness = 1.0
        if citations:
            valid_citations = 0
            for cit in citations:
                snippet = cit.get("snippet", "")
                if snippet.lower() in retrieved_context.lower() or self._token_overlap(snippet, retrieved_context) > 0.6:
                    valid_citations += 1
            citation_correctness = round(valid_citations / len(citations), 3)

        # Overall Harmonic Quality Index
        overall_quality = round(
            (0.3 * answer_relevance_score) +
            (0.25 * context_relevance_score) +
            (0.3 * faithfulness_score) +
            (0.15 * citation_correctness),
            3
        )

        return {
            "answer_relevance": answer_relevance_score,
            "context_relevance": context_relevance_score,
            "faithfulness": faithfulness_score,
            "citation_correctness": citation_correctness,
            "overall_quality_score": overall_quality,
            "grounding_status": grounding_result["status"],
            "unsupported_claims": grounding_result["unsupported_claims"],
        }


answer_quality_evaluator = AnswerQualityEvaluator()
