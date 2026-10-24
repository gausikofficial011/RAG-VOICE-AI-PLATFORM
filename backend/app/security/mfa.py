"""
Multi-Factor Authentication (MFA)
Provides RFC 6238 TOTP generation, QR code rendering, and secure recovery codes.
"""

import base64
import hashlib
import io
import secrets
from typing import List, Tuple
import pyotp
import qrcode
from backend.app.core.config import settings


def generate_mfa_secret() -> str:
    """Generate a random Base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, user_email: str) -> str:
    """Generate the standard otpauth URI for authenticator applications."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name=settings.APP_NAME)


def generate_qr_code_data_uri(otpauth_uri: str) -> str:
    """Generate a Base64-encoded PNG Data URI for display in the frontend."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=3,
    )
    qr.add_data(otpauth_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_b64}"


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verify the 6-digit TOTP code with a valid time window of +- 1 step (30s tolerance).
    """
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)


def generate_recovery_codes(count: int = 8) -> Tuple[List[str], List[str]]:
    """
    Generate plaintext backup recovery codes and their SHA-256 hashes for storage.
    Returns: (plaintext_codes, hashed_codes)
    """
    plaintext_codes = []
    hashed_codes = []
    for _ in range(count):
        code = f"{secrets.token_hex(3).upper()}-{secrets.token_hex(3).upper()}"
        plaintext_codes.append(code)
        hashed_code = hashlib.sha256(code.encode("utf-8")).hexdigest()
        hashed_codes.append(hashed_code)
    return plaintext_codes, hashed_codes


def verify_and_consume_recovery_code(code: str, hashed_codes: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify a single-use recovery code.
    If valid, returns (True, updated_hashed_codes_with_used_code_removed).
    Otherwise returns (False, hashed_codes).
    """
    normalized_code = code.strip().upper()
    hashed_input = hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()

    if hashed_input in hashed_codes:
        new_list = [h for h in hashed_codes if h != hashed_input]
        return True, new_list
    return False, hashed_codes
