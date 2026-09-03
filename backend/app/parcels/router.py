import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.parcels.schemas import GeoJSONFeatureCollection, ParcelGeometryUpdate
from app.parcels.service import attach_geometry, get_parcels_in_bbox, get_project_parcels_geojson

router = APIRouter()


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
