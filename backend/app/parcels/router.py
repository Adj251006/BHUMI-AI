import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.parcels.schemas import GeoJSONFeatureCollection, ParcelGeometryUpdate
from app.parcels.service import attach_geometry, get_parcels_in_bbox, get_project_parcels_geojson

from typing import Optional
from sqlalchemy import select
from app.models.land_parcel import LandParcel

router = APIRouter()


@router.get("/")
async def list_parcels(
    project_id: Optional[uuid.UUID] = None,
    session: AsyncSession = Depends(get_db),
):
    q = select(LandParcel).where(LandParcel.deleted_at.is_(None))
    if project_id:
        q = q.where(LandParcel.project_id == project_id)
    result = await session.execute(q.limit(100))
    parcels = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "project_id": str(p.project_id),
            "survey_number": p.survey_number,
            "land_type": p.land_type.value,
            "area_hectares": float(p.area_hectares),
            "state": p.state,
            "district": p.district,
            "taluka": p.taluka,
            "village": p.village,
            "ownership_type": p.ownership_type.value,
            "possession_status": p.possession_status.value,
        }
        for p in parcels
    ]


@router.get("/{parcel_id}")
async def get_parcel(
    parcel_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(select(LandParcel).where(LandParcel.id == parcel_id))
    p = result.scalar_one_or_none()
    if not p:
        from fastapi import HTTPException
        raise HTTPException(404, "Parcel not found")
    return {
        "id": str(p.id),
        "project_id": str(p.project_id),
        "survey_number": p.survey_number,
        "land_type": p.land_type.value,
        "area_hectares": float(p.area_hectares),
        "state": p.state,
        "district": p.district,
        "taluka": p.taluka,
        "village": p.village,
        "ownership_type": p.ownership_type.value,
        "possession_status": p.possession_status.value,
    }


@router.patch("/{parcel_id}/geometry")
async def update_parcel_geometry(
    parcel_id: uuid.UUID,
    geometry: ParcelGeometryUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Attach or update the PostGIS geometry of a LandParcel.
    Expects a valid GeoJSON Polygon or MultiPolygon.
    Only permitted for district_authority, state_govt, or central_ministry.
    """
    parcel = await attach_geometry(
        session=session,
        parcel_id=parcel_id,
        geometry_data=geometry,
        user_role=current_user.role.value,
    )
    return {"status": "success", "message": "Geometry updated successfully", "parcel_id": str(parcel.id)}


@router.get("/spatial", response_model=GeoJSONFeatureCollection)
async def spatial_search(
    min_lon: float = Query(..., description="Minimum longitude (West)"),
    min_lat: float = Query(..., description="Minimum latitude (South)"),
    max_lon: float = Query(..., description="Maximum longitude (East)"),
    max_lat: float = Query(..., description="Maximum latitude (North)"),
    session: AsyncSession = Depends(get_db),
):
    """
    Find parcels within a specific bounding box.
    Returns a GeoJSON FeatureCollection.
    """
    return await get_parcels_in_bbox(
        session=session,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
    )


@router.get("/project/{project_id}", response_model=GeoJSONFeatureCollection)
async def project_parcels_geojson(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Get all geo-tagged parcels for a given project as a GeoJSON FeatureCollection.
    """
    return await get_project_parcels_geojson(session=session, project_id=project_id)
