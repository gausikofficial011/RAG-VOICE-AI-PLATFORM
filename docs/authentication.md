# Authentication Guide

## 1. Overview

The platform uses a defense-in-depth authentication system designed to meet enterprise zero-trust standards:
- **Argon2id** password hashing resistant to GPU/ASIC cracking.
- **Dual-Token Asymmetric JWT Architecture**: Short-lived Access Tokens (15 minutes) and long-lived Refresh Tokens (7 days) with strict rotation.
- **JTI-Based Session Tracking & Immediate Revocation**: Every issued token has a cryptographically unique `jti` UUID stored in the database. When a user logs out or terminates a session, the `jti` is immediately invalidated.
- **Time-Based One-Time Password (TOTP) MFA**: RFC 6238-compliant two-factor authentication with QR code provisioning and SHA-256 hashed single-use recovery codes.

---

## 2. Password Security: Argon2id

Passwords are never stored in plaintext or weak hashes (MD5, SHA1, plain SHA-256). The system uses the industry-standard Argon2id algorithm:

```python
# Parameters used:
Type: Argon2id
Time Cost (Iterations): 3
Memory Cost: 65,536 KiB (64 MiB)
Parallelism: 4 threads
Salt: Cryptographically secure 16-byte random salt
```

### Password Complexity Requirements:
- Minimum length: 8 characters (12+ recommended)
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special symbol (`!@#$%^&*()_+-=[]{}|;:,.<>?`)

---

## 3. JWT Token Flow & Session Management

### 3.1 Token Payloads
```json
// Access Token (Expires in 15 minutes)
{
  "sub": "user_12345678",
  "org_id": "org_87654321",
  "email": "sarah.chen@enterprise.io",
  "role": "TENANT_ADMIN",
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "type": "access",
  "exp": 1712554500,
  "iat": 1712553600
}

// Refresh Token (Expires in 7 days)
{
  "sub": "user_12345678",
  "jti": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "type": "refresh",
  "exp": 1713158400,
  "iat": 1712553600
}
```

### 3.2 Token Refresh & Rotation Flow
1. Client sends `POST /api/auth/refresh` with `{ "refresh_token": "..." }`.
2. The server verifies the token signature and expiration.
3. The server checks if the refresh token's `jti` is revoked in the active session registry.
4. If valid, the old refresh token `jti` is **revoked immediately** (one-time use rotation), and a **new access token + new refresh token pair** is returned.
5. If an old refresh token is reused after rotation, an alert is logged, and all sessions for that user are revoked (replay attack mitigation).

### 3.3 Session Revocation
When `POST /api/auth/logout` is called:
- The caller's current `access_token` JTI is marked `is_revoked = True` in the database and added to the fast in-memory blacklist.
- Active refresh tokens are revoked.
- Subsequent calls with that token receive `401 Unauthorized: Session revoked`.

---

## 4. Multi-Factor Authentication (MFA / TOTP)

### 4.1 Setup Workflow
1. User calls `POST /api/auth/mfa/setup` (requires active Bearer token).
2. The server generates a random 32-character base32 secret using `pyotp.random_base32()`.
3. The server generates an `otpauth://` URI and renders a high-resolution QR code PNG encoded in Base64:
   ```
   otpauth://totp/RAGVoicePlatform:sarah.chen?secret=JBSWY3DPEHPK3PXP&issuer=RAGVoicePlatform
   ```
4. Ten cryptographically random single-use recovery codes are generated (e.g., `A4F9-82E1-K990`).
5. The SHA-256 hashes of the recovery codes and the encrypted TOTP secret are stored in the user profile.
6. The user enters a valid 6-digit TOTP code via `POST /api/auth/mfa/enable` to confirm synchronization.

### 4.2 Login Challenge
- When MFA is enabled for an account, `POST /api/auth/login` returns:
  ```json
  {
    "mfa_required": true,
    "user_id": "usr_9921",
    "message": "Enter 6-digit TOTP code or recovery code"
  }
  ```
- The client then submits `POST /api/auth/mfa/verify` with `{ "user_id": "usr_9921", "code": "123456" }`.
- Upon successful verification, the full access token and refresh token are issued.
