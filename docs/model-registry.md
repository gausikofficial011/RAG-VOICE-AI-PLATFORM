# MLOps Model Registry Guide

## 1. Overview & Purpose

The Model Registry (`backend/app/api/ml.py` & `ml/registry/registry.py`) provides an enterprise governance tier for machine learning models running across the platform. It tracks versions, lifecycle states, lineage, metrics, and deployment policies.

---

## 2. Registry Catalog Structure

Every registered model entry in the platform maintains the following lifecycle schema:

```json
{
  "name": "intent_classifier",
  "type": "nlp_classification",
  "framework": "scikit-learn",
  "active_version": "v1.0.0",
  "versions": {
    "v1.0.0": {
      "version": "v1.0.0",
      "artifact_path": "ml/artifacts/intent_classifier.joblib",
      "status": "production",
      "accuracy": 1.0,
      "f1_score": 1.0,
      "dataset_hash": "e8b2f90a1b",
      "created_at": "2026-10-08T05:43:21Z",
      "parameters": {
        "C": 2.0,
        "max_iter": 1000,
        "vectorizer": "tfidf"
      }
    }
  }
}
```

---

## 3. Model Lifecycle & Promotion Workflows

```
[Training Pipeline]
        │
        ▼ (Automatic Registration)
   [Staging / Candidate]
        │
        ├──> Automated Evaluation Gate (Test Accuracy >= Baseline)
        │
        ▼
   [Production] ───(Drift or Issue Detected)───> [Rollback to Previous Version]
        │
        ├──> A/B Testing Traffic Splitting (e.g., 90% v1.0.0 / 10% v1.1.0)
        │
        ▼
   [Archived]
```

### 3.1 Promotion API
To promote a candidate model version to production:
```bash
POST /api/ml/models/intent_classifier/promote
Authorization: Bearer <AI_ADMIN_TOKEN>
Content-Type: application/json

{
  "version": "v1.1.0"
}
```
The registry verifies artifact integrity, sets the requested version as `active_version`, updates the database state, and broadcasts a reload signal to hot-swap the model in memory with zero downtime.

### 3.2 Instant Rollback API
If an anomaly is detected in production:
```bash
POST /api/ml/models/intent_classifier/rollback
Authorization: Bearer <AI_ADMIN_TOKEN>
```
The previous stable production artifact is immediately restored into the inference pipeline, with an audit log record generated for compliance tracking.

---

## 4. UI Governance in AI/ML Admin Portal

The **AI/ML Admin Portal** renders real-time telemetry for all registered models:
- Active version badges.
- Model type and framework metadata.
- Trigger Training buttons with live execution output streams.
- Metrics cards displaying accuracy, F1-scores, and latency.
