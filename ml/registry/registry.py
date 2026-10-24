"""
ML Model Registry & MLOps Lifecycle Manager
Tracks model versions, metrics, artifacts, deployment transitions, and A/B experiments.
"""

from typing import Dict, Any, List, Optional
import os
import json
from datetime import datetime, timezone


class ModelRegistryManager:
    def __init__(self, registry_file: str = "ml/artifacts/registry_catalog.json"):
        self.registry_file = registry_file
        self.catalog = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "models": {
                "query_intent_classifier": {
                    "name": "query_intent_classifier",
                    "type": "INTENT",
                    "description": "Multi-class intent classifier mapping queries to 10 dialogue intents.",
                    "active_version": "v1.0.0",
                    "versions": {
                        "v1.0.0": {
                            "version": "v1.0.0",
                            "dataset_version": "v1.0.0",
                            "status": "DEPLOYED",
                            "artifact_path": "ml/artifacts/intent_classifier.joblib",
                            "metrics_path": "ml/artifacts/intent_classifier_metrics.json",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                },
                "document_classifier": {
                    "name": "document_classifier",
                    "type": "DOC_CLASS",
                    "description": "Classifies uploaded documents into 10 enterprise document archetypes.",
                    "active_version": "v1.0.0",
                    "versions": {
                        "v1.0.0": {
                            "version": "v1.0.0",
                            "dataset_version": "v1.0.0",
                            "status": "DEPLOYED",
                            "artifact_path": "ml/artifacts/document_classifier.joblib",
                            "metrics_path": "ml/artifacts/document_classifier_metrics.json",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                },
                "cross_encoder_reranker": {
                    "name": "cross_encoder_reranker",
                    "type": "RERANKER",
                    "description": "Cross-encoder scoring relevance between candidate chunks and query.",
                    "active_version": "v1.0.0",
                    "versions": {
                        "v1.0.0": {
                            "version": "v1.0.0",
                            "dataset_version": "v1.0.0",
                            "status": "DEPLOYED",
                            "metrics": {"mrr": 0.92, "ndcg_at_3": 0.89, "recall_at_3": 0.95},
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                },
                "grounding_classifier": {
                    "name": "grounding_classifier",
                    "type": "GROUNDING",
                    "description": "Validates factual grounding and detects hallucinated claims.",
                    "active_version": "v1.0.0",
                    "versions": {
                        "v1.0.0": {
                            "version": "v1.0.0",
                            "dataset_version": "v1.0.0",
                            "status": "DEPLOYED",
                            "metrics": {"f1": 0.94, "precision": 0.96, "recall": 0.92},
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                },
            },
            "experiments": [],
        }

    def _save(self):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self.catalog, f, indent=2)

    def list_models(self) -> List[Dict[str, Any]]:
        return list(self.catalog["models"].values())

    def get_model(self, name: str) -> Optional[Dict[str, Any]]:
        return self.catalog["models"].get(name)

    def deploy_version(self, model_name: str, version: str) -> bool:
        if model_name in self.catalog["models"]:
            m = self.catalog["models"][model_name]
            if version in m["versions"]:
                # Set previous active to APPROVED
                if m.get("active_version") and m["active_version"] in m["versions"]:
                    m["versions"][m["active_version"]]["status"] = "APPROVED"
                m["versions"][version]["status"] = "DEPLOYED"
                m["active_version"] = version
                self._save()
                return True
        return False

    def rollback_version(self, model_name: str, target_version: str) -> bool:
        return self.deploy_version(model_name, target_version)


model_registry = ModelRegistryManager()
