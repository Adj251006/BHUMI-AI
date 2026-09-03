import asyncio
import sys
import os
import uuid

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI

from app.database import engine, get_db
from app.models.user import User
from app.models.project import Project
from app.models.land_parcel import LandParcel
from app.main import app

# Create a local test user and token to use in the tests
async def get_test_token(client: httpx.AsyncClient) -> str:
    # First, let's make sure we have a user in the DB.
    # The seed script creates 'district.auth@sih.gov.in' with 'Test@1234'.
    login_data = {
        "email": "dc@pune.gov.in",
        "password": "Test@1234"
    }
    response = await client.post("/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Failed to login: {response.text}")
        sys.exit(1)
    return response.json()["access_token"]


async def get_test_parcel_id() -> str:
    async with engine.begin() as conn:
        result = await conn.execute(select(LandParcel.id).limit(1))
        row = result.first()
        if not row:
            print("No parcels in DB. Did you run the seed script?")
            sys.exit(1)
        return str(row[0])

async def get_test_project_id() -> str:
    async with engine.begin() as conn:
        result = await conn.execute(select(Project.id).limit(1))
        row = result.first()
        if not row:
            print("No projects in DB.")
            sys.exit(1)
        return str(row[0])


async def test_update_geometry(client: httpx.AsyncClient, token: str, parcel_id: str):
    print(f"\n--- Testing PATCH /api/parcels/{parcel_id}/geometry ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    geo_data = {
        "type": "Polygon",
        "coordinates": [
            [
                [73.8567, 18.5204],
                [73.8577, 18.5204],
                [73.8577, 18.5214],
                [73.8567, 18.5214],
                [73.8567, 18.5204]
            ]
        ]
    }
    
    response = await client.patch(
        f"/api/parcels/{parcel_id}/geometry",
        json=geo_data,
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ Geometry updated successfully.")
        print("Response:", response.json())
    else:
        print(f"✗ Failed to update geometry: {response.status_code}")
        print("Response:", response.text)
        sys.exit(1)


async def test_project_geojson(client: httpx.AsyncClient, project_id: str):
    print(f"\n--- Testing GET /api/parcels/project/{project_id} ---")
    response = await client.get(f"/api/parcels/project/{project_id}")
    if response.status_code == 200:
        data = response.json()
        print("✓ Project GeoJSON retrieved successfully.")
        print(f"Returned {len(data['features'])} features.")
    else:
        print(f"✗ Failed to get project geojson: {response.status_code}")
        print("Response:", response.text)
        sys.exit(1)


async def test_spatial_search(client: httpx.AsyncClient):
    print("\n--- Testing GET /api/parcels/spatial ---")
    params = {
        "min_lon": 73.8560,
        "min_lat": 18.5200,
        "max_lon": 73.8580,
        "max_lat": 18.5220
    }
    response = await client.get("/api/parcels/spatial", params=params)
    if response.status_code == 200:
        data = response.json()
        print("✓ Spatial search successful.")
        print(f"Returned {len(data['features'])} features.")
    else:
        print(f"✗ Failed to perform spatial search: {response.status_code}")
        print("Response:", response.text)
        sys.exit(1)


async def main():
    print("Starting Module 4 tests...")
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        token = await get_test_token(client)
        parcel_id = await get_test_parcel_id()
        project_id = await get_test_project_id()
        
        await test_update_geometry(client, token, parcel_id)
        await test_project_geojson(client, project_id)
        await test_spatial_search(client)
        
    print("\n✓ Module 4 backend tests complete.")

if __name__ == "__main__":
    asyncio.run(main())
