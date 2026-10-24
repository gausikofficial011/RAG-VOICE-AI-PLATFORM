"""
Authentication & User Pydantic Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=100)
    organization_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[str] = Field(default="USER")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None
    device_info: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    tenant_id: str
    email: str
    full_name: str
    role: str
    permissions: List[str]
    mfa_required: bool = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str
    qr_code_data_uri: str


class MfaVerifyRequest(BaseModel):
    code: str


class MfaRecoveryCodesResponse(BaseModel):
    recovery_codes: List[str]
    warning: str = "Store these recovery codes securely. Each code can only be used once."


class SessionResponse(BaseModel):
    id: str
    device_info: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    last_active_at: datetime
    created_at: datetime
    is_current: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    is_active: bool
    mfa_enabled: bool
    preferences: dict
    created_at: datetime
