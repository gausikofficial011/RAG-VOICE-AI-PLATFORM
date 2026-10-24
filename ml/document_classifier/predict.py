"""
Inference Module for Document Classifier
"""

import os
import joblib
from typing import Dict, Any


class DocumentClassifier:
    def __init__(self, artifact_path: str = "ml/artifacts/document_classifier.joblib"):
        self.artifact_path = artifact_path
        self.model = None
        self._load()

    def _load(self):
        if os.path.exists(self.artifact_path):
            self.model = joblib.load(self.artifact_path)

    def predict(self, text: str) -> Dict[str, Any]:
        """Classify document text."""
        if self.model is None:
            self._load()

        if self.model is None:
            # Fallback heuristic
            t = text.lower()
            if "abstract" in t and "paper" in t:
                return {"category": "RESEARCH_PAPER", "confidence": 0.9}
            elif "policy" in t:
                return {"category": "POLICY", "confidence": 0.9}
            elif "report" in t:
                return {"category": "REPORT", "confidence": 0.85}
            elif "contract" in t or "agreement" in t:
                return {"category": "CONTRACT", "confidence": 0.9}
            elif "faq" in t:
                return {"category": "FAQ", "confidence": 0.9}
            return {"category": "OTHER", "confidence": 0.75}

        # Take first 2000 characters for classification
        sample = text[:2000]
        pred = self.model.predict([sample])[0]
        probs = self.model.predict_proba([sample])[0]
        conf = float(max(probs))

        return {
            "category": pred,
            "confidence": round(conf, 4),
        }


document_classifier = DocumentClassifier()
