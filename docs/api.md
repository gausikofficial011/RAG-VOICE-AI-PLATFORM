# REST API Reference Guide

## 1. Gateway Overview

All REST API endpoints are served under the `/api` prefix. Interactive OpenAPI documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

All authenticated requests require the header:
```http
Authorization: Bearer <ACCESS_TOKEN>
```

---

## 2. Authentication Endpoints (`/api/auth`)

### 2.1 Register User
- **POST** `/api/auth/register`
- **Body**:
  ```json
  {
    "email": "user@org.io",
    "password": "Password123!",
    "full_name": "Jane Doe",
    "organization_name": "Acme Corp"
  }
  ```
- **Response**: `201 Created` with User and Organization details.

### 2.2 Login
- **POST** `/api/auth/login`
- **Body**: `{ "email": "user@org.io", "password": "Password123!" }`
- **Response**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": { "id": "...", "email": "...", "role": "TENANT_ADMIN" }
  }
  ```
  *(Or `{ "mfa_required": true, "user_id": "..." }` if MFA is configured).*

### 2.3 MFA Setup & Enable
- **POST** `/api/auth/mfa/setup` -> Returns `{ "secret": "...", "qr_code_base64": "...", "recovery_codes": [...] }`
- **POST** `/api/auth/mfa/enable` -> Body: `{ "code": "123456" }`
- **POST** `/api/auth/mfa/verify` -> Body: `{ "user_id": "...", "code": "123456" }`

### 2.4 Token Refresh & Revocation
- **POST** `/api/auth/refresh` -> Body: `{ "refresh_token": "..." }`
- **POST** `/api/auth/logout` -> Revokes active token JTI immediately.

---

## 3. Knowledge Base & Documents (`/api/knowledge-bases`, `/api/documents`)

### 3.1 Create Knowledge Base
- **POST** `/api/knowledge-bases`
- **Body**:
  ```json
  {
    "name": "Engineering Knowledge",
    "description": "System architecture and guidelines",
    "chunk_size": 500,
    "chunk_overlap": 80,
    "top_k": 5,
    "retrieval_strategy": "hybrid"
  }
  ```

### 3.2 List Knowledge Bases
- **GET** `/api/knowledge-bases` -> Returns array of tenant KBs.

### 3.3 Upload Document
- **POST** `/api/documents/upload`
- **Headers**: `Content-Type: multipart/form-data`
- **Form Data**:
  - `file`: Binary file stream (`.pdf`, `.docx`, `.txt`, `.csv`, `.md`, `.html`, `.json`)
  - `knowledge_base_id`: UUID of target knowledge base
- **Response**: `201 Created` with document metadata, chunk count, and ingestion status.

### 3.4 Delete Document
- **DELETE** `/api/documents/{doc_id}` -> Deletes file, DB metadata, chunks, and Qdrant vectors.

---

## 4. RAG Intelligence & Analytics (`/api/rag`)

### 4.1 Execute RAG Query
- **POST** `/api/rag/query`
- **Body**:
  ```json
  {
    "knowledge_base_id": "kb_uuid",
    "query": "What is our deployment rollback policy?",
    "conversation_id": "conv_uuid"  // optional for multi-turn memory
  }
  ```
- **Response**:
  ```json
  {
    "answer": "Rollback policies require...",
    "grounding_score": 0.94,
    "grounding_status": "GROUNDED",
    "intent": "retrieval_query",
    "route": "rag",
    "citations": [
      {
        "document_id": "doc_123",
        "filename": "operations_manual.pdf",
        "page_number": 12,
        "chunk_index": 3,
        "snippet": "In the event of an outage, execute..."
      }
    ],
    "latency": {
      "total_ms": 142.5,
      "intent_classification_ms": 2.1,
      "retrieval_ms": 18.4,
      "rerank_ms": 12.0,
      "generation_ms": 105.2,
      "grounding_check_ms": 4.8
    }
  }
  ```

---

## 5. Voice Intelligence Endpoints (`/api/voice`)

### 5.1 Voice Query (Audio-in, Answer + Audio-out)
- **POST** `/api/voice/query`
- **Headers**: `Content-Type: multipart/form-data`
- **Form Data**:
  - `audio`: WAV / WebM binary audio file
  - `knowledge_base_id`: Target knowledge base UUID
- **Response**:
  ```json
  {
    "transcript": "What is our customer refund window?",
    "answer": "Customers may request refunds within 30 calendar days...",
    "audio_base64": "UklGRi...",
    "grounding_score": 0.96,
    "citations": [...]
  }
  ```

### 5.2 Direct Text-to-Speech (TTS)
- **POST** `/api/voice/tts`
- **Body**: `{ "text": "Hello, how can I help you today?", "voice": "en-US-GuyNeural" }`
- **Response**: `audio/mpeg` binary stream.

---

## 6. MLOps Model Registry (`/api/ml`)

- **GET** `/api/ml/models` -> Returns list of registered ML models and active versions.
- **POST** `/api/ml/models/{name}/train` -> Triggers background model retraining run.
- **POST** `/api/ml/models/{name}/promote` -> Promotes version to production.
- **POST** `/api/ml/models/{name}/rollback` -> Restores prior production version.

---

## 7. Compliance & Audit Logs (`/api/audit`)

- **GET** `/api/audit/logs?event_type=DOC_UPLOAD&limit=50` -> Returns immutable audit trail.
- **GET** `/api/audit/stats` -> Returns security event frequency metrics.
