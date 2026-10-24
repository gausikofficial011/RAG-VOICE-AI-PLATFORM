"""
Password Hashing and Verification
Uses Argon2id (via passlib / argon2-cffi) for state-of-the-art cryptographic strength.
"""

from passlib.context import CryptContext

# Use Argon2 as primary scheme with bcrypt fallback for legacy verification if needed
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MiB
    argon2__time_cost=3,        # 3 iterations
    argon2__parallelism=4,     # 4 parallel threads
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plaintext password matches the hashed password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Check if the hash needs to be upgraded to newer security parameters."""
    return pwd_context.needs_update(hashed_password)
