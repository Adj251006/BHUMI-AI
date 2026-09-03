"""Module 2 Verification Script — Auth + Role-Based Access Control.

Run from backend directory:
    python -m scripts.test_module2

Verifies:
1. Module imports and component integrity
2. Password hashing & verification with bcrypt
3. JWT token creation, claims, and decoding
4. Expired and invalid token handling
5. Live API endpoint integration tests via FastAPI TestClient:
   - POST /auth/login (success with seed admin)
   - POST /auth/login (invalid password -> 401)
   - POST /auth/login (non-existent email -> 401)
   - GET /auth/me (authenticated user profile -> 200)
   - GET /auth/me (unauthenticated -> 401)
   - POST /auth/register (admin registering new official -> 201)
   - POST /auth/register (unauthenticated -> 401)
   - POST /auth/register (non-admin role e.g. state_govt -> 403)
   - POST /auth/register (duplicate email -> 409)
   - POST /auth/register (invalid jurisdiction combo -> 422)
   - POST /auth/refresh (valid refresh token -> 200)
   - POST /auth/refresh (access token passed instead of refresh token -> 401)
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from jose import jwt

from app.config import settings
from app.main import app
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenError,
)
from app.models.enums import UserRole


async def run_async_tests():
    print("===========================================================")
    print("  MODULE 2 VERIFICATION — Auth & RBAC Test Suite")
    print("===========================================================")
    print()

    # -------------------------------------------------------------
    # Test 1: Password Hashing & Verification
    # -------------------------------------------------------------
    print("[1/5] Testing password hashing & verification...")
    raw_pass = "SecurePass123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass, "Hash should not match raw password"
    assert hashed.startswith("$2b$"), "Bcrypt hash should start with $2b$"
    assert verify_password(raw_pass, hashed) is True, "Valid password should verify"
    assert verify_password("WrongPass123!", hashed) is False, "Wrong password should fail"
    print("  ✓ Password hashing (bcrypt) round-trip passed")

    # -------------------------------------------------------------
    # Test 2: JWT Token Encoding & Decoding
    # -------------------------------------------------------------
    print("[2/5] Testing JWT token generation & claim verification...")
    user_id = str(uuid.uuid4())
    access_token = create_access_token(user_id=user_id, role="central_ministry")
    refresh_token = create_refresh_token(user_id=user_id)

    payload_access = decode_token(access_token)
    assert payload_access["sub"] == user_id
    assert payload_access["role"] == "central_ministry"
    assert payload_access["type"] == "access"

    payload_refresh = decode_token(refresh_token)
    assert payload_refresh["sub"] == user_id
    assert payload_refresh["type"] == "refresh"
    assert "role" not in payload_refresh
    print("  ✓ JWT access and refresh token claims verified")

    # -------------------------------------------------------------
    # Test 3: Token Expiry & Invalid Token Handling
    # -------------------------------------------------------------
    print("[3/5] Testing expired and tampered JWT token handling...")
    expired_payload = {
        "sub": user_id,
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
    }
    expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    try:
        decode_token(expired_token)
        assert False, "Expired token should raise TokenError"
    except TokenError:
        pass

    try:
        decode_token("invalid.jwt.token")
        assert False, "Malformed token should raise TokenError"
    except TokenError:
        pass
    print("  ✓ Token expiry and tamper detection passed")

    # -------------------------------------------------------------
    # Test 4: Live API Endpoint Integration Tests
    # -------------------------------------------------------------
    print("[4/5] Testing FastAPI Auth API Endpoints...")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        # 4.1 Login with valid admin credentials
        resp = await client.post("/auth/login", json={
            "email": "admin@mord.gov.in",
            "password": "Test@1234"
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        tokens = resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        admin_access_token = tokens["access_token"]
        admin_refresh_token = tokens["refresh_token"]
        print("  ✓ POST /auth/login (Valid credentials) -> 200 OK")

        # 4.2 Login with wrong password
        resp = await client.post("/auth/login", json={
            "email": "admin@mord.gov.in",
            "password": "WrongPassword99"
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"
        print("  ✓ POST /auth/login (Wrong password) -> 401 Unauthorized")

        # 4.3 Login with non-existent email
        resp = await client.post("/auth/login", json={
            "email": "nobody@mord.gov.in",
            "password": "Test@1234"
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"
        print("  ✓ POST /auth/login (Non-existent user) -> 401 Unauthorized")

        # 4.4 GET /auth/me with valid Bearer token
        resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {admin_access_token}"})
        assert resp.status_code == 200
        user_data = resp.json()
        assert user_data["email"] == "admin@mord.gov.in"
        assert user_data["role"] == "central_ministry"
        print("  ✓ GET /auth/me (Authenticated) -> 200 OK")

        # 4.5 GET /auth/me without token
        resp = await client.get("/auth/me")
        assert resp.status_code == 401
        print("  ✓ GET /auth/me (Unauthenticated) -> 401 Unauthorized")

        # 4.6 POST /auth/register (admin creating state official)
        new_email = f"state_officer_{uuid.uuid4().hex[:6]}@maharashtra.gov.in"
        resp = await client.post(
            "/auth/register",
            json={
                "email": new_email,
                "password": "OfficialPass123!",
                "full_name": "Suresh Deshmukh",
                "role": "state_govt",
                "state": "Maharashtra"
            },
            headers={"Authorization": f"Bearer {admin_access_token}"}
        )
        assert resp.status_code == 201, f"Register failed: {resp.text}"
        created_user = resp.json()
        assert created_user["email"] == new_email
        assert created_user["role"] == "state_govt"
        assert created_user["state"] == "Maharashtra"
        print("  ✓ POST /auth/register (Admin creating user) -> 201 Created")

        # Log in as the newly created state official to test non-admin role
        resp = await client.post("/auth/login", json={
            "email": new_email,
            "password": "OfficialPass123!"
        })
        assert resp.status_code == 200
        state_access_token = resp.json()["access_token"]

        # 4.7 POST /auth/register as non-admin user (should be forbidden)
        resp = await client.post(
            "/auth/register",
            json={
                "email": "unauthorized_user@test.com",
                "password": "Pass12345!",
                "full_name": "Test User",
                "role": "state_govt",
                "state": "Goa"
            },
            headers={"Authorization": f"Bearer {state_access_token}"}
        )
        assert resp.status_code == 403
        print("  ✓ POST /auth/register (Non-admin token) -> 403 Forbidden")

        # 4.8 POST /auth/register without token
        resp = await client.post(
            "/auth/register",
            json={
                "email": "anon_user@test.com",
                "password": "Pass12345!",
                "full_name": "Anon User",
                "role": "central_ministry"
            }
        )
        assert resp.status_code == 401
        print("  ✓ POST /auth/register (Unauthenticated) -> 401 Unauthorized")

        # 4.9 POST /auth/register duplicate email
        resp = await client.post(
            "/auth/register",
            json={
                "email": new_email,
                "password": "Pass12345!",
                "full_name": "Duplicate User",
                "role": "state_govt",
                "state": "Maharashtra"
            },
            headers={"Authorization": f"Bearer {admin_access_token}"}
        )
        assert resp.status_code == 409
        print("  ✓ POST /auth/register (Duplicate email) -> 409 Conflict")

        # 4.10 POST /auth/register invalid jurisdiction (state_govt missing state)
        resp = await client.post(
            "/auth/register",
            json={
                "email": "invalid_jurisdiction@test.com",
                "password": "Pass12345!",
                "full_name": "No State User",
                "role": "state_govt"
                # Missing required state field
            },
            headers={"Authorization": f"Bearer {admin_access_token}"}
        )
        assert resp.status_code == 422
        print("  ✓ POST /auth/register (Invalid jurisdiction payload) -> 422 Unprocessable")

        # 4.11 POST /auth/refresh with valid refresh token
        resp = await client.post("/auth/refresh", json={"refresh_token": admin_refresh_token})
        assert resp.status_code == 200
        refreshed = resp.json()
        assert "access_token" in refreshed
        assert "refresh_token" in refreshed
        print("  ✓ POST /auth/refresh (Valid refresh token) -> 200 OK")

        # 4.12 POST /auth/refresh with access token instead of refresh token
        resp = await client.post("/auth/refresh", json={"refresh_token": admin_access_token})
        assert resp.status_code == 401
        print("  ✓ POST /auth/refresh (Invalid token type) -> 401 Unauthorized")

    # -------------------------------------------------------------
    # Test 5: Summary
    # -------------------------------------------------------------
    print()
    print("===========================================================")
    print("  ALL MODULE 2 AUTH & RBAC VERIFICATION CHECKS PASSED ✓")
    print("===========================================================")


def main():
    asyncio.run(run_async_tests())


if __name__ == "__main__":
    main()

