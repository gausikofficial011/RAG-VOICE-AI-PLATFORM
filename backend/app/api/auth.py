"""
Authentication & Session Management API Router
Enterprise-grade: Argon2id, Refresh Token Rotation, TOTP MFA, Account Lockout, Audit Trails.
"""

from datetime import datetime, timezone, timedelta
from typing import List
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.models.session import UserSession
from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    MfaRecoveryCodesResponse,
    SessionResponse,
    ChangePasswordRequest,
    UserProfileResponse,
)
from backend.app.security.password import hash_password, verify_password
from backend.app.security.jwt import create_access_token, create_refresh_token, decode_token, revoke_jti
from backend.app.security.mfa import (
    generate_mfa_secret,
    get_totp_uri,
    generate_qr_code_data_uri,
    verify_totp_code,
    generate_recovery_codes,
    verify_and_consume_recovery_code,
)
from backend.app.security.rbac import get_permissions_for_role
from backend.app.auth.dependencies import get_current_user
from backend.app.audit.service import audit_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user and assign/create tenant organization."""
    # Check if email already registered
    stmt = select(User).where(User.email == data.email.lower())
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Resolve or create organization
    org_name = data.organization_name or f"{data.full_name}'s Org"
    slug = org_name.lower().replace(" ", "-")

    stmt_org = select(Organization).where(Organization.slug == slug)
    res_org = await db.execute(stmt_org)
    org = res_org.scalar_one_or_none()

    if not org:
        org = Organization(name=org_name, slug=slug)
        db.add(org)
        await db.flush()

    # Create User with Argon2id hash
    user = User(
        tenant_id=org.id,
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role if data.role in ["USER", "ORGANIZATION_ADMIN", "SUPER_ADMIN"] else "USER",
    )
    db.add(user)
    await db.flush()

    permissions = get_permissions_for_role(user.role)
    access_token, a_jti, a_exp = create_access_token(user.id, user.tenant_id, user.role, permissions)
    refresh_token, r_jti, r_exp = create_refresh_token(user.id, user.tenant_id)

    # Register initial session
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown Browser")
    session = UserSession(
        user_id=user.id,
        tenant_id=user.tenant_id,
        jti=r_jti,
        refresh_token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
        device_info="Primary Device",
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=r_exp,
    )
    db.add(session)
    await db.commit()

    # Audit logging
    await audit_service.log_event(
        db=db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="REGISTER",
        action="User registration",
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        permissions=permissions,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with Argon2id, lockout check, and optional MFA."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "Unknown Browser")

    clean_email = data.email.strip().lower()
    clean_password = data.password.strip()

    stmt = select(User).where(User.email == clean_email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Account Lockout Check
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        remaining = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked due to failed attempts. Try again in {remaining} minutes.",
        )

    # Verify Password
    if not verify_password(clean_password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
            await audit_service.log_event(
                db=db,
                tenant_id=user.tenant_id,
                user_id=user.id,
                event_type="ACCOUNT_LOCKED",
                action="Account locked due to consecutive failed logins",
                ip_address=client_ip,
                status="FAILURE",
            )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Check Multi-Factor Authentication
    if user.mfa_enabled:
        if not data.mfa_code:
            return TokenResponse(
                access_token="",
                refresh_token="",
                expires_in=0,
                user_id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                permissions=[],
                mfa_required=True,
            )
        # Verify 6-digit TOTP or backup code
        is_totp_valid = verify_totp_code(user.mfa_secret or "", data.mfa_code)
        if not is_totp_valid:
            # Check recovery codes
            consumed, updated_codes = verify_and_consume_recovery_code(data.mfa_code, user.mfa_recovery_codes)
            if consumed:
                user.mfa_recovery_codes = updated_codes
                await db.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA verification code.",
                )

    # Reset failed attempts and update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now

    permissions = get_permissions_for_role(user.role)
    access_token, a_jti, a_exp = create_access_token(user.id, user.tenant_id, user.role, permissions)
    refresh_token, r_jti, r_exp = create_refresh_token(user.id, user.tenant_id)

    session = UserSession(
        user_id=user.id,
        tenant_id=user.tenant_id,
        jti=r_jti,
        refresh_token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
        device_info=data.device_info or "Web Session",
        ip_address=client_ip,
        user_agent=user_agent,
        expires_at=r_exp,
    )
    db.add(session)
    await db.commit()

    await audit_service.log_event(
        db=db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        event_type="LOGIN",
        action="User logged in",
        ip_address=client_ip,
        user_agent=user_agent,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        permissions=permissions,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue new token pair."""
    try:
        payload = decode_token(data.refresh_token, is_refresh=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {str(e)}",
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")

    # Locate and invalidate old session
    stmt = select(UserSession).where(UserSession.jti == jti)
    res = await db.execute(stmt)
    old_session = res.scalar_one_or_none()

    if not old_session or old_session.is_revoked:
        revoke_jti(jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or expired.",
        )

    # Invalidate previous token
    old_session.is_revoked = True
    revoke_jti(jti)

    # Fetch User
    stmt_user = select(User).where(User.id == user_id)
    res_user = await db.execute(stmt_user)
    user = res_user.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account inactive.")

    # Issue new rotated token pair
    permissions = get_permissions_for_role(user.role)
    new_access_token, _, _ = create_access_token(user.id, user.tenant_id, user.role, permissions)
    new_refresh_token, new_r_jti, new_r_exp = create_refresh_token(user.id, user.tenant_id)

    new_session = UserSession(
        user_id=user.id,
        tenant_id=user.tenant_id,
        jti=new_r_jti,
        refresh_token_hash=hashlib.sha256(new_refresh_token.encode()).hexdigest(),
        device_info=old_session.device_info,
        ip_address=old_session.ip_address,
        user_agent=old_session.user_agent,
        expires_at=new_r_exp,
    )
    db.add(new_session)
    await db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        permissions=permissions,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log out current user and revoke active session."""
    stmt = (
        update(UserSession)
        .where(UserSession.user_id == current_user.id, UserSession.is_revoked == False)
        .values(is_revoked=True)
    )
    await db.execute(stmt)
    await db.commit()

    await audit_service.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        event_type="LOGOUT",
        action="User logged out",
    )
    return {"success": True, "message": "Successfully logged out."}


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve currently authenticated user profile."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        is_active=current_user.is_active,
        mfa_enabled=current_user.mfa_enabled,
        preferences=current_user.preferences,
        created_at=current_user.created_at,
    )


# =============================================================================
# MULTI-FACTOR AUTHENTICATION (MFA / TOTP)
# =============================================================================

@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate TOTP secret, provisioning URI, and QR Code Data URI."""
    secret = generate_mfa_secret()
    current_user.mfa_secret = secret
    await db.commit()

    otpauth_uri = get_totp_uri(secret, current_user.email)
    qr_data_uri = generate_qr_code_data_uri(otpauth_uri)

    return MfaSetupResponse(
        secret=secret,
        otpauth_uri=otpauth_uri,
        qr_code_data_uri=qr_data_uri,
    )


@router.post("/mfa/verify", response_model=MfaRecoveryCodesResponse)
async def mfa_verify(
    data: MfaVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify 6-digit TOTP code, enable MFA, and generate backup recovery codes."""
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA setup has not been initiated.")

    if not verify_totp_code(current_user.mfa_secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid 6-digit code. Please check your authenticator app.")

    # Generate 8 single-use recovery codes
    plaintext_codes, hashed_codes = generate_recovery_codes(8)
    current_user.mfa_enabled = True
    current_user.mfa_recovery_codes = hashed_codes
    await db.commit()

    await audit_service.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        event_type="MFA_ENABLED",
        action="MFA enabled with TOTP",
    )

    return MfaRecoveryCodesResponse(recovery_codes=plaintext_codes)


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active sessions for the current user."""
    stmt = select(UserSession).where(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False,
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    return [
        SessionResponse(
            id=s.id,
            device_info=s.device_info,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            last_active_at=s.last_active_at,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.post("/revoke-session/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a specific session."""
    stmt = select(UserSession).where(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")

    s.is_revoked = True
    revoke_jti(s.jti)
    await db.commit()
    return {"success": True, "message": "Session revoked."}
