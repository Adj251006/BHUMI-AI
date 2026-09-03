"""Authentication API endpoints.

Endpoints:
    POST /auth/login    — Authenticate with email + password, get tokens.
    POST /auth/register — Create a new user (admin-only).
    POST /auth/refresh  — Exchange a refresh token for new token pair.
    GET  /auth/me       — Get the current user's profile.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User


router = APIRouter()


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
    description="Validate email and password. Returns access + refresh tokens.",
    responses={
        401: {"description": "Invalid credentials or account deactivated"},
    },
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user and return JWT tokens.

    Security notes:
    - Returns a generic "Invalid credentials" for both wrong email and wrong
      password to prevent email enumeration attacks.
    - Checks is_active and deleted_at before issuing tokens.
    """
    # 1. Look up user by email
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    user = result.scalar_one_or_none()

    # 2. Validate credentials (generic error to prevent enumeration)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Issue tokens
    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ---------------------------------------------------------------------------
# POST /auth/register (admin-only)
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (admin-only)",
    description=(
        "Only central_ministry users can create new accounts. "
        "Validates that state/district are provided for roles that require them."
    ),
    responses={
        201: {"description": "User created successfully"},
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions (not admin)"},
        409: {"description": "Email already registered"},
        422: {"description": "Validation error (missing state/district)"},
    },
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.CENTRAL_MINISTRY)),
) -> UserResponse:
    """Create a new user account.

    Admin-only: requires a valid JWT from a central_ministry user.

    Validation rules:
    - state_govt requires state to be set.
    - district_authority requires both state and district.
    - project_agency requires both state and district.
    - central_ministry requires neither (national scope).
    - Duplicate email returns 409 Conflict.
    """
    # 1. Validate state/district requirements based on role
    _validate_jurisdiction(body.role, body.state, body.district)

    # 2. Check for duplicate email
    existing = await db.execute(
        select(User.id).where(User.email == body.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{body.email}' is already registered",
        )

    # 3. Create user with hashed password
    new_user = User(
        id=uuid.uuid4(),
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        state=body.state,
        district=body.district,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()  # Get generated timestamps before response

    return UserResponse.model_validate(new_user)


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access + refresh token pair.",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a refresh token for a new token pair.

    The old refresh token is not revoked (stateless design).
    The new access token will have up-to-date role/status from the DB.
    """
    # 1. Decode and validate the refresh token
    try:
        payload = decode_token(body.refresh_token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # 2. Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Load user from DB (to get current role/status)
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Issue new token pair with current role
    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
    )
    new_refresh_token = create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user.",
    responses={
        401: {"description": "Not authenticated"},
    },
)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the current user's profile."""
    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_jurisdiction(role: UserRole, state: str | None, district: str | None) -> None:
    """Validate that state/district are provided when required by the role.

    Rules:
    - central_ministry: state and district must be NULL (national scope).
    - state_govt: state is required, district must be NULL.
    - district_authority: state and district are both required.
    - project_agency: state and district are both required.

    Raises:
        HTTPException 422: If the jurisdiction fields don't match the role.
    """
    if role == UserRole.CENTRAL_MINISTRY:
        if state is not None or district is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="central_ministry users must not have state or district set",
            )

    elif role == UserRole.STATE_GOVT:
        if not state:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="state_govt users require 'state' to be set",
            )
        if district is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="state_govt users must not have 'district' set",
            )

    elif role in (UserRole.DISTRICT_AUTHORITY, UserRole.PROJECT_AGENCY):
        if not state:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{role.value} users require 'state' to be set",
            )
        if not district:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{role.value} users require 'district' to be set",
            )
