"""
Grounding & Hallucination Classifier
Verifies whether generated claims in the LLM answer are supported by retrieved context.
Computes token-level and n-gram lexical entailment, grounding score, and unsupported claims.
"""

from typing import Any, Dict, List, Tuple
import re


class GroundingValidator:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def _extract_claims(self, answer: str) -> List[str]:
        # Split answer into individual claim propositions / sentences
        sentences = re.split(r"(?<=[.!?])\s+", answer)
        return [s.strip() for s in sentences if len(s.strip().split()) > 3]

    def validate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        generated_answer: str,
    ) -> Dict[str, Any]:
        """
        Validate grounding of generated answer against evidence chunks.
        """
        # If model explicitly says it could not find information
        if "couldn't find enough information" in generated_answer.lower():
            return {
                "grounding_score": 1.0,
                "status": "SUPPORTED",
                "unsupported_claims": [],
                "claim_evaluations": [],
            }

        if not retrieved_chunks:
            return {
                "grounding_score": 0.0,
                "status": "UNSUPPORTED",
                "unsupported_claims": [generated_answer],
                "claim_evaluations": [],
            }

        # Aggregate evidence context
        context_corpus = " ".join([
            (c.get("payload", {}).get("content") or c.get("content", "")).lower()
            for c in retrieved_chunks
        ])
        context_words = set(re.findall(r"\w+", context_corpus))

        claims = self._extract_claims(generated_answer)
        if not claims:
            return {
                "grounding_score": 0.9,
                "status": "SUPPORTED",
                "unsupported_claims": [],
                "claim_evaluations": [],
            }

        claim_evals = []
        unsupported = []
        supported_count = 0

        for claim in claims:
            # Stop words to ignore
            claim_words = [w for w in re.findall(r"\w+", claim.lower()) if len(w) > 2]
            if not claim_words:
                continue

            matches = sum(1 for w in claim_words if w in context_words)
            overlap_ratio = matches / max(len(claim_words), 1)

            # Check for exact 3-gram matches in context
            claim_tokens = claim.lower().split()
            trigram_hits = 0
            total_trigrams = max(len(claim_tokens) - 2, 1)
            for i in range(len(claim_tokens) - 2):
                tri = " ".join(claim_tokens[i : i + 3])
                if tri in context_corpus:
                    trigram_hits += 1

            claim_score = (0.6 * overlap_ratio) + (0.4 * (trigram_hits / total_trigrams))

            is_supported = claim_score >= self.threshold
            if is_supported:
                supported_count += 1
            else:
                unsupported.append(claim)

            claim_evals.append({
                "claim": claim,
                "score": round(claim_score, 3),
                "is_supported": is_supported,
            })

        total_claims = max(len(claim_evals), 1)
        grounding_score = round(supported_count / total_claims, 3)

        if grounding_score >= 0.8:
            status = "SUPPORTED"
        elif grounding_score >= 0.4:
            status = "PARTIALLY_SUPPORTED"
        else:
            status = "UNSUPPORTED"

        return {
            "grounding_score": grounding_score,
            "status": status,
            "unsupported_claims": unsupported,
            "claim_evaluations": claim_evals,
        }


grounding_validator = GroundingValidator()
