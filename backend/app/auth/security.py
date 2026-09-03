"""Core security utilities: password hashing and JWT token management.

Password hashing:
    Uses passlib with the bcrypt backend. bcrypt automatically handles
    salting and produces hashes in the format $2b$12$<salt><hash>.

JWT tokens:
    - Access tokens: short-lived (default 60 min), carry user ID + role.
    - Refresh tokens: longer-lived (default 7 days), carry user ID only.
    - Both are signed with HMAC-SHA256 using SECRET_KEY from config.
    - Stateless — no DB storage required for the hackathon scope.
"""

import bcrypt
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Args:
        plain_password: The raw password string.

    Returns:
        bcrypt hash string (e.g., $2b$12$...).
    """
    pw_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: The raw password to check.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        pw_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False



# ---------------------------------------------------------------------------
# JWT token creation
# ---------------------------------------------------------------------------


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived JWT access token.

    Claims:
        sub: User UUID (string)
        role: User role (e.g., "central_ministry")
        type: "access"
        exp: Expiration timestamp

    Args:
        user_id: The user's UUID as a string.
        role: The user's role value (e.g., UserRole.CENTRAL_MINISTRY.value).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    """Create a longer-lived JWT refresh token.

    Refresh tokens carry minimal claims (just user ID) and are used
    only at POST /auth/refresh to obtain a new access token.

    Claims:
        sub: User UUID (string)
        type: "refresh"
        exp: Expiration timestamp

    Args:
        user_id: The user's UUID as a string.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


# ---------------------------------------------------------------------------
# JWT token decoding
# ---------------------------------------------------------------------------


class TokenError(Exception):
    """Raised when a JWT token is invalid, expired, or malformed."""

    def __init__(self, detail: str = "Invalid or expired token"):
        self.detail = detail
        super().__init__(self.detail)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Validates:
        - Signature (HMAC-SHA256 with SECRET_KEY)
        - Expiration (exp claim)
        - Required claims (sub, type)

    Args:
        token: The encoded JWT string.

    Returns:
        Decoded payload dict with keys: sub, type, role (if access), exp, iat.

    Raises:
        TokenError: If the token is invalid, expired, or missing required claims.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        raise TokenError(f"Token verification failed: {e}") from e

    # Validate required claims
    if "sub" not in payload:
        raise TokenError("Token missing 'sub' claim")
    if "type" not in payload:
        raise TokenError("Token missing 'type' claim")

    return payload
