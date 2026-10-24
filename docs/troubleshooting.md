# Troubleshooting & Diagnostics Guide

## 1. Quick Diagnostics Checklist

If you encounter unexpected behavior during setup or runtime, follow this prioritized checklist:

```
[ ] 1. Check Backend Health: GET http://localhost:8000/api/health
[ ] 2. Check Database Connectivity: inspect data/rag_platform.db or PostgreSQL connection string.
[ ] 3. Verify ML Artifacts: verify ml/artifacts/intent_classifier.joblib exists.
[ ] 4. Check Qdrant Mode: vector_store falls back to embedded ./data/qdrant if Docker is absent.
[ ] 5. Check Token Validity: verify Authorization header format and token expiration.
```

---

## 2. Common Issues & Solutions

### 2.1 Qdrant Vector Store Connection Timed Out
- **Symptom**: Startup hangs or vector queries throw `ConnectionRefusedError` or timeout on port 6333.
- **Cause**: Qdrant Docker container is not running, but `QDRANT_URL=http://localhost:6333` is configured.
- **Solution**: The platform includes an automatic 100ms socket pre-check in `backend/app/retrieval/vector_store.py`. If port 6333 does not respond immediately, it gracefully falls back to local embedded storage (`./data/qdrant`). To force embedded mode permanently, set in `.env`:
  ```ini
  QDRANT_URL=
  QDRANT_PATH=./data/qdrant
  ```

### 2.2 `401 Unauthorized: Session revoked`
- **Symptom**: User receives 401 error even though token expiration is in the future.
- **Cause**: The user logged out or the refresh token rotation superseded the current access session.
- **Solution**: Perform a fresh login via `POST /api/auth/login` to obtain an active token pair.

### 2.3 Audio Query Returns Silence or "Vocal energy too low"
- **Symptom**: Voice query fails with RMS energy rejection.
- **Cause**: The microphone input was muted, audio clipping was detected, or recording duration was under 0.2s.
- **Solution**: Check microphone permissions in the browser. Speak clearly into the microphone. Inspect browser console for audio blob duration.

### 2.4 Grounding Score Low / "Insufficient Evidence" Response
- **Symptom**: Query returns: *"The provided documents do not contain sufficient evidence to answer this question."*
- **Cause**: The grounding validator computed an overlap score below 0.70.
- **Solution**:
  1. Inspect the **Trace Viewer** in the User Portal to view the retrieved chunks and grounding score.
  2. Verify that documents containing the required information are uploaded and indexed into the active knowledge base.
  3. Increase `top_k` in Knowledge Base settings (e.g., from 3 to 7) to provide broader evidence context to the generator.

### 2.5 ML Model Missing Artifact Error
- **Symptom**: `FileNotFoundError: ml/artifacts/intent_classifier.joblib not found`.
- **Cause**: Models were not trained after a clean repository checkout.
- **Solution**: Execute the training script to generate fresh serialized artifacts:
  ```bash
  python ml/intent_classifier/train.py
  python ml/document_classifier/train.py
  ```

---

## 3. Log Inspection & Telemetry

- **Backend Application Logs**: Written to standard error / standard output with timestamps and request correlation IDs (`X-Request-ID`).
- **Security Audit Logs**: Stored in the `audit_logs` SQL table. View via the **Auditor Portal** or query directly:
  ```bash
  curl -H "Authorization: Bearer <AUDITOR_TOKEN>" http://localhost:8000/api/audit/logs
  ```
