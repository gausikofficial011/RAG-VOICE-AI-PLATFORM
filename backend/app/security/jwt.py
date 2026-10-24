"""
JWT Token Management
Provides generation, verification, and decoding of access tokens and refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid
import jwt
from backend.app.core.config import settings

# In-memory blacklist for revoked token identifiers (JTIs)
# In high-scale clustered deployments, this can be synced to Redis
_revoked_jtis: set[str] = set()


def revoke_jti(jti: str) -> None:
    """Mark a token ID as revoked."""
    if jti:
        _revoked_jtis.add(jti)


def is_jti_revoked(jti: str) -> bool:
    """Check if a token ID has been revoked."""
    return jti in _revoked_jtis


def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    permissions: List[str],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> tuple[str, str, datetime]:
    """
    Generate an access token.
    Returns: (token_str, jti, expire_datetime)
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": role,
        "permissions": permissions,
        "type": "access",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    encoded = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded, jti, expire


def create_refresh_token(
    subject: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str, datetime]:
    """
    Generate a refresh token.
    Returns: (token_str, jti, expire_datetime)
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    encoded = jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded, jti, expire


def decode_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises jwt.PyJWTError on invalid/expired token.
    """
    secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET
    payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])

    jti = payload.get("jti")
    if jti and is_jti_revoked(jti):
        raise jwt.InvalidTokenError("Token has been revoked")

    expected_type = "refresh" if is_refresh else "access"
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type. Expected {expected_type}")

    return payload
