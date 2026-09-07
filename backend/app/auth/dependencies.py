"""FastAPI dependencies for authentication and role-based access control.

Usage in route handlers:

    # Any authenticated user
    @router.get("/profile")
    async def profile(user: User = Depends(get_current_user)):
        return user

    # Only central_ministry users
    @router.get("/admin")
    async def admin_panel(
        user: User = Depends(get_current_user),
        _: None = Depends(require_roles(UserRole.CENTRAL_MINISTRY)),
    ):
        return {"admin": True}

    # Multiple allowed roles
    @router.get("/state-data")
    async def state_data(
        user: User = Depends(get_current_user),
        _: None = Depends(require_roles(
            UserRole.CENTRAL_MINISTRY,
            UserRole.STATE_GOVT,
        )),
    ):
        return {"data": "..."}
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import TokenError, decode_token
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User


# ---------------------------------------------------------------------------
# OAuth2 scheme — tells FastAPI where to find the token
# ---------------------------------------------------------------------------

# tokenUrl is the endpoint clients use to obtain tokens.
# FastAPI uses this for the Swagger UI "Authorize" button.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

import time

_USER_CACHE: dict[str, tuple[float, User]] = {}

def invalidate_user_cache(user_id: str = None):
    if user_id:
        _USER_CACHE.pop(str(user_id), None)
    else:
        _USER_CACHE.clear()


# ---------------------------------------------------------------------------
# Core dependency: extract current user from JWT
# ---------------------------------------------------------------------------


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT access token.

    This dependency:
    1. Decodes the JWT from the Authorization header.
    2. Verifies it's an access token (not a refresh token).
    3. Loads the user from the database.
    4. Checks that the user is active and not soft-deleted.

    Args:
        token: JWT from the Authorization: Bearer <token> header.
        db: Database session (injected by FastAPI).

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found.
    """
    # 1. Decode and validate the JWT
    try:
        payload = decode_token(token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # 2. Verify this is an access token, not a refresh token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Load user from database (cached in memory for 60s to avoid 400ms network roundtrip per request)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = time.time()
    if user_id in _USER_CACHE:
        ts, cached_user = _USER_CACHE[user_id]
        if now - ts < 60.0:
            return cached_user

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Check active status and soft-delete
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

    _USER_CACHE[user_id] = (now, user)
    return user


# ---------------------------------------------------------------------------
# Role-based access control dependency
# ---------------------------------------------------------------------------


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Create a dependency that restricts access to specific roles.

    This is a dependency factory — call it with the allowed roles and
    use the returned function as a FastAPI dependency.

    Args:
        *allowed_roles: One or more UserRole enum values that are
            permitted to access the endpoint.

    Returns:
        A FastAPI-compatible async dependency function.

    Example:
        @router.delete("/project/{id}",
            dependencies=[Depends(require_roles(UserRole.CENTRAL_MINISTRY))])
        async def delete_project(...):
            ...
    """

    async def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """Check that the current user has one of the allowed roles.

        Returns:
            The authenticated User (allows chaining with get_current_user).

        Raises:
            HTTPException 403: If the user's role is not in allowed_roles.
        """
        if current_user.role not in allowed_roles:
            allowed = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {allowed}",
            )
        return current_user

    return _role_checker
