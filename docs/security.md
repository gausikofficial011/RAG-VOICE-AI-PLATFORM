# Security & Hardening Guide

## 1. Threat Modeling & Defense-in-Depth

The platform is engineered under the assumption of hostile network environments and malicious internal tenant attempts. The defense-in-depth model spans six security tiers:

```
[Tier 1: Perimeter / Network]  TLS 1.3, Strict CORS, Reverse Proxy, IP Rate Limiter
[Tier 2: HTTP / API Gateway]   OWASP Security Headers, Request ID Tracking, Payload Size Limits
[Tier 3: Identity & Access]    Argon2id, Dual-Token JWT Rotation, TOTP MFA, JTI Blacklist
[Tier 4: Multi-Tenant Boundary]Strict Org Filters in SQL, Qdrant Vector Payload, and Sandboxed FS
[Tier 5: Model & Prompt Safety]Query Safety Classifier, Prompt Injection Stripping, Grounding Gate
[Tier 6: Audit & Compliance]   Immutable Append-Only Audit Trail with SHA-256 Hashing
```

---

## 2. API Security Headers

All HTTP responses emitted by the FastAPI gateway include strict security headers via middleware (`backend/app/middleware/security.py`):

| Header | Value | Purpose |
| :--- | :--- | :--- |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';` | Prevents XSS script execution |
| `X-Content-Type-Options` | `nosniff` | Blocks MIME-sniffing exploits |
| `X-Frame-Options` | `DENY` | Prevents clickjacking in iframes |
| `X-XSS-Protection` | `1; mode=block` | Browser XSS filter enforcement |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Mandates HTTPS transmission |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer data leakage |

---

## 3. Rate Limiting & Denial of Service Protection

The gateway implements a sliding-window rate limiter:
- **Default Limit**: 120 requests per minute per client IP address.
- **Authentication Endpoints (`/api/auth/*`)**: 10 requests per minute to prevent brute-force attacks.
- **Voice Ingestion Endpoints (`/api/voice/*`)**: 30 requests per minute to conserve transcription compute.
- **Response upon breach**: `429 Too Many Requests` with a `Retry-After: <seconds>` header.

---

## 4. Path Traversal & File Upload Hardening

Document uploads undergo multi-stage sanitization in `DocumentService`:
1. **Filename Sanitization**: Strip directory traversals (`../`, `..\\`), null bytes (`\0`), and control characters using `secure_filename`.
2. **UUID Scoping**: Files are never stored under user-supplied names on disk. They are assigned a random UUID `doc_id` and saved in:
   ```
   data/tenants/{organization_id}/documents/{document_id}.bin
   ```
3. **MIME & Extension Whitelist**: Only `.pdf`, `.docx`, `.txt`, `.csv`, `.md`, `.html`, `.json` are accepted. Executables (`.exe`, `.sh`, `.bat`, `.py`) are rejected immediately.
4. **Size Caps**: Maximum upload size is strictly capped at 25MB per document.

---

## 5. Immutable Audit Trail

The platform records all sensitive operations in an append-only audit log table:
- User logins and logout events.
- MFA enablement and challenge results.
- Document uploads and deletions.
- Knowledge base creations and purges.
- ML training executions and model version promotions.

Each record stores the actor ID, organization ID, action, resource, client IP, user agent, timestamp, and metadata payload. The **Auditor Portal** provides real-time filtering for security officers and compliance auditors.
