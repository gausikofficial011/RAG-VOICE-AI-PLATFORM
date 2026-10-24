"""
Security, Cryptography, and RBAC Test Suite
"""

import pytest
from backend.app.security.password import hash_password, verify_password
from backend.app.security.jwt import create_access_token, decode_token, revoke_jti, is_jti_revoked
from backend.app.security.mfa import (
    generate_mfa_secret,
    get_totp_uri,
    generate_recovery_codes,
    verify_and_consume_recovery_code,
)
from backend.app.security.rbac import Role, Permission, has_permission, get_permissions_for_role


def test_argon2id_password_hashing():
    pwd = "UltraSecurePassword123!"
    hashed = hash_password(pwd)
    assert hashed.startswith("$argon2")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_generation_and_revocation():
    token, jti, exp = create_access_token("user-1", "tenant-1", "USER", ["knowledge_base:read"])
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert is_jti_revoked(jti) is False

    # Revoke
    revoke_jti(jti)
    assert is_jti_revoked(jti) is True
    with pytest.raises(Exception):
        decode_token(token)


def test_mfa_recovery_codes():
    plaintext_codes, hashed_codes = generate_recovery_codes(8)
    assert len(plaintext_codes) == 8
    assert len(hashed_codes) == 8

    code_to_use = plaintext_codes[0]
    valid, remaining = verify_and_consume_recovery_code(code_to_use, hashed_codes)
    assert valid is True
    assert len(remaining) == 7

    # Reuse attempt must fail
    reuse_valid, _ = verify_and_consume_recovery_code(code_to_use, remaining)
    assert reuse_valid is False


def test_rbac_permissions_matrix():
    # Super Admin has all permissions
    assert has_permission(Role.SUPER_ADMIN.value, Permission.SYSTEM_MANAGE) is True
    assert has_permission(Role.SUPER_ADMIN.value, Permission.KB_CREATE) is True

    # User cannot manage system or train models
    assert has_permission(Role.USER.value, Permission.SYSTEM_MANAGE) is False
    assert has_permission(Role.USER.value, Permission.MODELS_TRAIN) is False
    assert has_permission(Role.USER.value, Permission.KB_CREATE) is True

    # Viewer can only read
    assert has_permission(Role.VIEWER.value, Permission.KB_CREATE) is False
    assert has_permission(Role.VIEWER.value, Permission.KB_READ) is True
