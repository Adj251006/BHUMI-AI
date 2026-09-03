"""Pydantic schemas for authentication request/response validation.

These schemas handle:
- Input validation (email format, password strength, role validity)
- Response serialization (excluding sensitive fields like password_hash)
- OpenAPI documentation generation via FastAPI
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    """POST /auth/login request body."""

    email: EmailStr = Field(
        ...,
        description="User's registered email address",
        examples=["admin@mord.gov.in"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password (min 8 characters)",
    )


class RegisterRequest(BaseModel):
    """POST /auth/register request body.

    Only accessible by central_ministry users (admin-only registration).
    """

    email: EmailStr = Field(
        ...,
        description="New user's email (must be unique)",
        examples=["officer@karnataka.gov.in"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Initial password (min 8 characters)",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the official",
        examples=["Dr. Meena Kumari"],
    )
    role: UserRole = Field(
        ...,
        description="Role to assign to the new user",
    )
    state: str | None = Field(
        default=None,
        max_length=100,
        description="Jurisdiction state (required for state_govt and below)",
        examples=["Karnataka"],
    )
    district: str | None = Field(
        default=None,
        max_length=100,
        description="Jurisdiction district (required for district_authority)",
        examples=["Bengaluru Urban"],
    )


class RefreshRequest(BaseModel):
    """POST /auth/refresh request body."""

    refresh_token: str = Field(
        ...,
        description="A valid refresh token obtained from login",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TokenResponse(BaseModel):
    """Response returned on successful login or token refresh."""

    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")


class UserResponse(BaseModel):
    """Public user profile — excludes password_hash and internal fields."""

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    state: str | None
    district: str | None
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,  # Allow ORM model → Pydantic conversion
    }


class MessageResponse(BaseModel):
    """Generic message response for error details."""

    detail: str
