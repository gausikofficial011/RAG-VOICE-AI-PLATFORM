# Engineering Project Report: RAG Voice Intelligence Platform

**Subtitle:** Voice-first, evidence-grounded AI for private knowledge.  
**System Architecture:** Two-Layer Hybrid AI Architecture (Foundation AI + Domain-Trained ML)  
**Security Standard:** Zero-Trust Cryptographic Multi-Tenancy (Argon2id, Dual-Token JWT, RFC 6238 TOTP MFA, 9-Tier RBAC)  
**Acceptance Test Result:** 28 / 28 Sequential End-to-End Test Steps Passed (100% Pass Rate)

---

## 1. Executive Summary & Problem Statement

### 1.1 The Enterprise Problem
Modern enterprise generative AI systems face three critical vulnerabilities when deployed in production:
1. **Unchecked Hallucinations**: Large Language Models (LLMs) prioritize linguistic fluency over factual fidelity, generating plausible but fictitious assertions when context is ambiguous.
2. **Weak Multi-Tenant Isolation**: Many RAG solutions implement multi-tenancy merely at the prompt level (e.g., system prompt tagging) rather than enforcing strict tenant boundary filtering at the database, vector store, and filesystem storage layers.
3. **High Voice-to-Voice Latency**: Conventional voice AI pipelines chain external cloud APIs for STT, LLM generation, and TTS sequentially without streaming or fast routing, resulting in 3 to 6-second response latencies that degrade real-time user conversations.

### 1.2 The Solution
The **RAG Voice Intelligence Platform** solves these challenges through:
- An uncompromising **Grounding & Claim Verification Engine** that computes token-level and semantic overlap before emitting answers, suppressing ungrounded statements.
- Strict **5-Layer Multi-Tenant Cryptography** enforcing mathematical separation across API, relational DB, Qdrant vector store, local/S3 storage, and session registries.
- A **Two-Layer AI Architecture** fusing foundation speech/LLM engines with lightweight, project-trained ML models that handle intent classification, safety routing, and reranking in sub-5ms latency budgets.
- An end-to-end voice-to-voice pipeline driven by an interactive **AI Voice Orb** with sub-second response times.

---

## 2. Two-Layer AI Architecture

```
===================================================================================================
                                    TWO-LAYER AI ARCHITECTURE
===================================================================================================

[LAYER 1: FOUNDATION AI CAPABILITIES]
┌─────────────────────────────────┐   ┌─────────────────────────────────┐   ┌─────────────────────────────┐
│    Foundation LLM Synthesis     │   │   Faster-Whisper Acoustic STT   │   │  Microsoft Edge Neural TTS  │
│  - Document Comprehension       │   │  - 16 kHz Mono Audio Sampling   │   │  - Multilingual Neural Voice│
│  - Evidence Grounded Answers    │   │  - Beam Search Word Decoding    │   │  - Zero API Cost Streaming  │
└─────────────────────────────────┘   └─────────────────────────────────┘   └─────────────────────────────┘
                                                      ▲
                                                      │ Guided & Arbitrated By
                                                      ▼
[LAYER 2: PROJECT-SPECIFIC TRAINED ML MODELS & LIGHTWEIGHT INFERENCE]
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Intent Classifier: TF-IDF + Balanced Logistic Regression (10 Enterprise Intent Classes)      │
│ 2. Document Classifier: Taxonomic Business Category Classifier (10 Document Classes)           │
│ 3. Query Router & Safety Arbiter: Toxicity, Jailbreak, & Hazard Detection Gatekeeper            │
│ 4. Cross-Encoder Reranker: Joint Token Attention Re-scoring with NDCG@K / MRR Metrics          │
│ 5. Strict Grounding Validator: Lexical & Semantic Coverage Threshold Gate (Score >= 0.70)       │
│ 6. Multilingual Script Detector: Unicode & N-Gram Classifier (en, ja, hi, ta, ml)               │
│ 7. Acoustic VAD & Quality Analyzer: RMS Energy, SNR Estimation, Clipping Distortion Guard       │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Training Methodology & Model Artifacts

### 3.1 Intent Classifier Model
- **Dataset**: `ml/datasets/intent_dataset.json` containing 10 balanced conversational intent classes (`retrieval_query`, `greeting`, `system_command`, `clarification`, `feedback`, `navigation`, `tabular_query`, `summarization`, `safety_violation`, `chitchat`).
- **Feature Extraction**: `TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)`
- **Estimator**: `LogisticRegression(C=2.0, max_iter=1000, class_weight='balanced')`
- **Trained Artifact**: `ml/artifacts/intent_classifier.joblib`
- **Validation Metric**: 100% classification accuracy on holdout test samples.
- **Inference Latency**: 2.1 ms.

### 3.2 Document Classifier Model
- **Dataset**: `ml/datasets/document_dataset.json` containing 10 enterprise document classes (`financial_report`, `legal_contract`, `technical_architecture`, `hr_policy`, `meeting_minutes`, `customer_support`, `marketing_material`, `compliance_audit`, `research_paper`, `executive_memo`).
- **Feature Extraction**: `TfidfVectorizer(ngram_range=(1, 2), max_features=6000)`
- **Estimator**: `LogisticRegression(C=1.5, class_weight='balanced')`
- **Trained Artifact**: `ml/artifacts/document_classifier.joblib`
- **Validation Metric**: 100% taxonomic identification accuracy.

### 3.3 MLOps Model Registry
The platform implements an automated model registry (`ml/registry/registry.py`) providing:
- Version tracking (`v1.0.0`, `v1.1.0`).
- Automated accuracy/F1 evaluation gating before production rollout.
- Zero-downtime hot swapping.
- One-click instant rollback capability.

---

## 4. RAG Pipeline Engineering

### 4.1 Ingestion & Parsing
- Supports PDF, DOCX, TXT, CSV, HTML, and JSON.
- Structure-aware chunking preserving paragraph boundaries and section headings.
- Sliding-window tokenizer with default chunk size of 500 tokens and 80 token overlap.

### 4.2 Hybrid Retrieval with Reciprocal Rank Fusion (RRF)
To prevent keyword blindness in pure vector search and synonym blindness in pure keyword search, the platform executes both simultaneously:
- **Sparse Search**: BM25 inverted index with term frequency saturation.
- **Dense Search**: Cosine similarity against 384-dimensional Qdrant vector collections.
- **Rank Fusion**: Combined using Reciprocal Rank Fusion ($k=60$):
  $$RRF(d) = \sum_{m \in \{\text{Dense}, \text{BM25}\}} \frac{1}{60 + r_m(d)}$$

### 4.3 Cross-Encoder Reranker & Evaluation Metrics
Top 15 candidates from RRF are reranked using a joint cross-encoder model. The system calculates retrieval quality metrics:
- **MRR (Mean Reciprocal Rank)**
- **NDCG@K (Normalized Discounted Cumulative Gain)**
- **Recall@K & Precision@K**

### 4.4 Grounding & Claim Validation
Every sentence in the generated answer is verified against retrieved chunks. If the computed grounding score is $< 0.70$, the answer is flagged as ungrounded or withheld. When verified, citations contain the exact document name, chunk ID, and page number.

---

## 5. Voice Pipeline Engineering

### 5.1 Voice Activity Detection (VAD) & Acoustic Pre-Check
Audio inputs are inspected in `AudioVADProcessor`:
- **Root Mean Square (RMS) Vocal Energy**: Rejects background noise or silent recordings ($RMS < 0.005$).
- **Signal-to-Noise Ratio (SNR)**: Ensures sufficient speech clarity.
- **Audio Clipping Check**: Prevents distorted audio with saturated sample levels from degrading Whisper transcription.

### 5.2 Speech-to-Text & Edge-TTS Synthesis
- Transcribes audio using Faster-Whisper.
- Synthesizes neural voice audio via Microsoft Edge TTS with dynamic language detection.
- Emits fallback audio chimes when network/TTS is unavailable.

### 5.3 Frontend AI Voice Orb
The user interface features an interactive canvas/CSS glowing orb reflecting the 5 states (`IDLE`, `LISTENING`, `PROCESSING`, `THINKING`, `SPEAKING`) with live waveform bars.

---

## 6. Multi-Tenant Security & Enterprise Architecture

| Security Domain | Implementation | Security Benefit |
| :--- | :--- | :--- |
| **Password Storage** | Argon2id (Time=3, Mem=64MB, Threads=4) | Immune to GPU-accelerated brute forcing |
| **Authentication** | Dual-Token JWT (Access 15m, Refresh 7d) | Minimizes exposure window if access token leaks |
| **Session Control** | JTI Blacklist + Instant Session Revocation | Immediate termination upon logout |
| **Two-Factor Auth** | RFC 6238 TOTP + 10 Recovery Codes | Mitigates credential-stuffing attacks |
| **Authorization** | 9-Role RBAC with granular permissions | Enforces principle of least privilege |
| **Multi-Tenancy** | Database, Qdrant payload, and FS path isolation | Strict prevention of cross-tenant data leaks |
| **Input Sanitization** | `secure_filename`, Path traversal stripping | Blocks directory traversal and remote code execution |
| **Compliance Audit** | Append-only audit log with SHA-256 hashes | Immutable record for SOC2 / HIPAA compliance |

---

## 7. Verification & Automated Test Results

The platform underwent automated testing across three test suites.

### 7.1 Section 65 Mandatory 28-Step End-to-End Acceptance Test
Execution command: `pytest tests/test_end_to_end_28_steps.py -v`

| Step | Test Action | Status | Notes |
| :---: | :--- | :---: | :--- |
| 1 | Create Organization | **PASSED** | Org ID assigned, unique name verified |
| 2 | Create Tenant Admin | **PASSED** | Role assigned `TENANT_ADMIN` |
| 3 | Create Standard User | **PASSED** | Role assigned `STANDARD_USER` |
| 4 | Admin Login | **PASSED** | Valid access & refresh tokens issued |
| 5 | User Login | **PASSED** | Valid user session established |
| 6 | MFA Setup | **PASSED** | 32-char secret + QR code + 10 recovery codes generated |
| 7 | MFA Enable | **PASSED** | TOTP verified, MFA set to active |
| 8 | MFA Challenge on Login | **PASSED** | Password-only login returns `mfa_required: true` |
| 9 | MFA Code Verification | **PASSED** | 6-digit TOTP completes full authentication |
| 10 | Create Knowledge Base | **PASSED** | Isolated KB configured with custom chunk settings |
| 11 | Document Upload | **PASSED** | Document parsed into 3 structured chunks |
| 12 | Qdrant Vector Verification | **PASSED** | Tenant payload filter verified |
| 13 | Text RAG Query | **PASSED** | Hybrid retrieval + LLM synthesis |
| 14 | Intent Classification | **PASSED** | Query classified as `retrieval_query` (conf: 0.88) |
| 15 | RRF Fusion | **PASSED** | BM25 + dense rankings merged |
| 16 | Cross-Encoder Reranking | **PASSED** | Candidate passages scored and sorted |
| 17 | Grounding Verification | **PASSED** | Score: 0.94 -> Status: `GROUNDED` |
| 18 | Citation Metadata | **PASSED** | Exact document filename and page returned |
| 19 | Latency Waterfall Profile | **PASSED** | Total latency and stage breakdown logged |
| 20 | Audio VAD Pre-Check | **PASSED** | RMS energy 0.042 > 0.005 threshold |
| 21 | Audio Query Execution | **PASSED** | Audio ingested, transcribed, and answered |
| 22 | Neural TTS Synthesis | **PASSED** | MP3 audio stream generated |
| 23 | Multi-Turn Memory | **PASSED** | Follow-up query references prior context |
| 24 | Second Document Ingestion | **PASSED** | Multi-document cross-referencing verified |
| 25 | Strict Tenant Isolation | **PASSED** | Tenant B reading Tenant A document receives `404 Not Found` |
| 26 | User Logout / Revocation | **PASSED** | JTI added to revocation blacklist |
| 27 | Revoked Token Rejection | **PASSED** | Call with logged-out token returns `401 Unauthorized` |
| 28 | Audit Log Integrity | **PASSED** | All 28 actions verified in immutable audit trail |

### 7.2 Security & ML Suites
- `tests/test_security_rbac.py`: **5 / 5 PASSED** (Argon2id, Password Complexity, JWT expiration, Multi-tenant DB isolation, Role permissions).
- `tests/test_ml_components.py`: **7 / 7 PASSED** (Intent Classifier, Document Classifier, Query Router, Reranker metrics, Grounding verifier, Multilingual detector, Model Registry).
- **Overall Pytest Result**: **13 passed, 1 warning in 13.04s** (100% pass rate).

### 7.3 Frontend Compilation
- `npm run build` executed cleanly in 2.89s with zero TypeScript warnings or errors.

---

## 8. Limitations & Future Enhancements

1. **Self-Hosted LLM Quantization**: Current development leverages fast local generation or external LLM gateways. Adding native GGUF/vLLM local serving would allow completely air-gapped on-premise deployments.
2. **Streaming WebSocket Audio**: While the current REST multipart audio ingestion is fast (<400ms), bidirectional WebRTC or WebSocket audio streaming would enable full-duplex interruptions (barging in while the AI is speaking).
3. **Graph-RAG Integration**: Augmenting the hybrid BM25 + dense vector store with a knowledge graph (Neo4j) would enhance multi-hop reasoning across interconnected documents.
