"""
Inference Interface for Query Intent Classifier
"""

import os
import joblib
from typing import Dict, Any


class IntentClassifier:
    def __init__(self, artifact_path: str = "ml/artifacts/intent_classifier.joblib"):
        self.artifact_path = artifact_path
        self.model = None
        self._load()

    def _load(self):
        if os.path.exists(self.artifact_path):
            self.model = joblib.load(self.artifact_path)

    def predict(self, query: str) -> Dict[str, Any]:
        """
        Classify intent of incoming query.
        Returns intent label, confidence score, and probabilities.
        """
        if self.model is None:
            self._load()

        if self.model is None:
            # Rule-based fallback if artifact not yet built
            q = query.lower()
            if any(w in q for w in ["hi", "hello", "hey", "morning"]):
                return {"intent": "GREETING", "confidence": 0.95}
            elif "summar" in q:
                return {"intent": "SUMMARIZATION", "confidence": 0.90}
            elif "compare" in q:
                return {"intent": "COMPARISON", "confidence": 0.88}
            elif any(w in q for w in ["hack", "bomb", "stolen", "illegal"]):
                return {"intent": "OUT_OF_SCOPE", "confidence": 0.95}
            return {"intent": "DOCUMENT_QUERY", "confidence": 0.85}

        pred = self.model.predict([query])[0]
        probs = self.model.predict_proba([query])[0]
        classes = self.model.classes_
        confidence = float(max(probs))

        return {
            "intent": pred,
            "confidence": round(confidence, 4),
            "probabilities": {cls: round(float(p), 4) for cls, p in zip(classes, probs)},
        }


intent_classifier = IntentClassifier()


if __name__ == "__main__":
    test_queries = [
        "Hello assistant",
        "Summarize the quarterly results",
        "What does section 2 say?",
        "Compare table 1 with table 2",
    ]
    for q in test_queries:
        print(f"Query: {q} -> {intent_classifier.predict(q)}")
