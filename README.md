# RAG Voice Intelligence Platform

> **"Voice-first, evidence-grounded AI for private knowledge."**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.13-red.svg)](https://qdrant.tech/)
[![Security](https://img.shields.io/badge/Security-Argon2id%20%7C%20TOTP%20MFA-green.svg)](https://cheatsheetseries.owasp.org/)
[![Tests](https://img.shields.io/badge/Tests-28%2F28%20E2E%20Passed-success.svg)](./tests/)

---

## Architecture Overview

The **RAG Voice Intelligence Platform** is an enterprise-grade conversational voice + text RAG system built on a **Two-Layer AI Architecture** with strict cryptographic multi-tenancy, sub-second voice synthesis, and immutable compliance auditing.

```
+---------------------------------------------------------------------------------------------------+
|                                          CLIENT PORTALS                                           |
|   [User Portal]    [Org Admin]    [AI/ML MLOps Admin]    [System Admin]    [Compliance Auditor]   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                   HTTPS / WSS / REST API
                                                  |
+---------------------------------------------------------------------------------------------------+
|                                      API GATEWAY & SECURITY                                       |
|  - Security Headers (HSTS, CSP, X-Frame)          - Sliding-Window Rate Limiting (Redis / Memory) |
|  - Correlation ID Injection (X-Request-ID)        - JWT JTI Session Revocation Gatekeeper         |
|  - Path Traversal & File Sanitizer                - Multi-Tenant RBAC Context Resolver           |
+---------------------------------------------------------------------------------------------------+
                                                  |
                 +--------------------------------+--------------------------------+
                 |                                                                 |
                 v                                                                 v
+----------------------------------+                             +----------------------------------+
|          VOICE PIPELINE          |                             |           RAG PIPELINE           |
| - WebRTC / Audio Ingestion (WAV) |                             | - Query Intent Classifier        |
| - Energy-Based VAD & SNR Filter  |                             | - Safety & Route Arbitrator      |
| - Faster-Whisper / STT Engine    |                             | - Dense + Sparse BM25 Retrieval  |
| - Multilingual Edge-TTS Streaming|                             | - Reciprocal Rank Fusion (RRF)   |
| - Audio Cache & Fallback Chimes  |                             | - Cross-Encoder Reranker         |
+----------------------------------+                             | - Table RAG Engine (CSV Query)   |
                 |                                               | - LLM Evidence Generation        |
                 +--------------------------------+              | - Strict Claim Grounding Checker |
                                                  |              +----------------------------------+
                                                  v                                |
+----------------------------------------------------------------------------------+----------------+
|                                         PERSISTENCE & ISOLATION                                   |
|   +-----------------------+   +-----------------------+   +-----------------------+              |
|   |   Relational DB       |   |   Vector Store        |   |   Multi-Tenant FS     |              |
|   |   PostgreSQL / SQLite |   |   Qdrant Engine       |   |   Filesystem / S3     |              |
|   |   (Tenancy, Audits)   |   |   (tenant_id payload) |   |   (data/tenants/{org})|              |
|   +-----------------------+   +-----------------------+   +-----------------------+              |
+---------------------------------------------------------------------------------------------------+
```

---

## Key Features

1. **Two-Layer AI Topology**:
   - **Foundation Layer**: High-parameter LLM generation, Faster-Whisper STT, Microsoft Edge Neural TTS.
   - **Trained ML Layer**: Project-specific models for Intent Classification (10 classes), Document Classification (10 classes), Query Safety Routing, Multilingual Detection, and Speaker Verification.
2. **Strict Multi-Tenancy**:
   - Cryptographic tenant boundaries across DB queries, Qdrant vector payload filters, and sandboxed storage paths (`data/tenants/{org_id}`).
3. **Evidence-Grounded RAG**:
   - Hybrid retrieval (Dense vectors + Sparse BM25) fused via Reciprocal Rank Fusion (RRF).
   - Cross-encoder reranking with MRR, NDCG@K, Recall@K, and Precision@K metrics.
   - Strict sentence-level claim grounding validation (Score $\ge 0.70$).
4. **Voice Interface & AI Voice Orb**:
   - Interactive dynamic Voice Orb in the User Portal with 5 states: `IDLE`, `LISTENING`, `PROCESSING`, `THINKING`, `SPEAKING`.
   - Voice Activity Detection (RMS energy, SNR, and clipping distortion guards).
5. **Zero-Trust Security**:
   - Argon2id password hashing, Dual-token JWT rotation (Access 15m, Refresh 7d).
   - Time-based One-Time Password (TOTP) MFA with QR code provisioning and 10 single-use recovery codes.
   - Immediate JTI token revocation upon logout.
   - 9-tier Role-Based Access Control (RBAC).
   - Immutable append-only audit trail.
6. **5 Enterprise Web Portals**:
   - **User Portal**: Conversational AI Chat, interactive Voice Orb, Document list & upload, Citation jumping modal, and Execution Trace Viewer.
   - **Organization Admin Portal**: Knowledge base management, user role assignments, tenant storage quotas, and analytics KPIs.
   - **AI/ML Admin Portal**: Model registry governance, training pipeline triggers, performance metrics, and instant rollback.
   - **System Admin Portal**: Infrastructure health, database status, Qdrant vector engine status, and microservices telemetry.
   - **Auditor Portal**: Filterable, immutable security event audit log for SOC2 / HIPAA compliance.

---

## Quickstart Guide

### 1. Backend Setup

```bash
# Clone the repository
git clone <repository_url>
cd "RAG VOICE AI PLATFORM"

# Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.  
Interactive API Documentation:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Or build for production
npm run build
```

The frontend will run at `http://localhost:5173`.

### 3. Docker Services (Optional)

To run Qdrant and PostgreSQL via Docker:

```bash
docker compose up -d
```

*(Note: If Docker is not running, the platform automatically falls back to local embedded Qdrant storage at `./data/qdrant` and SQLite at `./data/rag_platform.db` without crashing).*

---

## Running the Automated Test Suites

The test suite validates functional correctness, security barriers, machine learning models, and the mandatory 28-step end-to-end acceptance scenario:

```bash
# Run the complete test suite
pytest tests/ -v

# Run the Section 65 28-Step Acceptance Test specifically
pytest tests/test_end_to_end_28_steps.py -v

# Run Security & RBAC tests
pytest tests/test_security_rbac.py -v

# Run ML components & registry tests
pytest tests/test_ml_components.py -v
```

**Verification Result**: All 28 steps passed (100% pass rate).

---

## Documentation Index

Comprehensive guides are available in the [`docs/`](./docs) directory:

- [System Architecture Guide](./docs/architecture.md)
- [Authentication & Sessions](./docs/authentication.md)
- [Authorization & RBAC Matrix](./docs/authorization.md)
- [RAG Pipeline & Grounding](./docs/rag.md)
- [Voice AI Pipeline & Orb UX](./docs/voice.md)
- [ML Training & Datasets](./docs/ml-training.md)
- [MLOps Model Registry](./docs/model-registry.md)
- [Security & Hardening](./docs/security.md)
- [Deployment & Operations](./docs/deployment.md)
- [Testing & Quality Assurance](./docs/testing.md)
- [REST API Reference](./docs/api.md)
- [Troubleshooting & Diagnostics](./docs/troubleshooting.md)
- [Full Engineering Project Report](./PROJECT_REPORT.md)
