"""
Authentication & RBAC Dependencies
Extracts user identity, validates JWT tokens, and enforces granular permission checks.
"""

from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.security.jwt import decode_token, is_jti_revoked
from backend.app.security.rbac import Permission, Role, has_permission, resolve_role

security_scheme = HTTPBearer(auto_error=True)
optional_security_scheme = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Retrieve user if token provided, otherwise return None without raising 401."""
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials, is_refresh=False)
        user_id = payload.get("sub")
        if not user_id:
            return None
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
    except Exception:
        pass
    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate access token and retrieve current active user.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token, is_refresh=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if jti and is_jti_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def require_permission(perm: Permission) -> Callable:
    """
    Dependency factory to check if current user has the specified permission.
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        resolved = resolve_role(current_user.role)
        if resolved == Role.SUPER_ADMIN:
            return current_user
        if not has_permission(current_user.role, perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {perm.value}",
            )
        return current_user

    return permission_checker


def require_role(roles: List[str]) -> Callable:
    """
    Dependency factory to check if current user belongs to one of the specified roles.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        resolved = resolve_role(current_user.role)
        if resolved == Role.SUPER_ADMIN:
            return current_user
        allowed_roles = [resolve_role(r) for r in roles]
        if resolved not in allowed_roles and current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(roles)}",
            )
        return current_user

    return role_checker
