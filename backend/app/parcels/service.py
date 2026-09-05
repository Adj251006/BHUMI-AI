import uuid
from typing import Any

import shapely
from fastapi import HTTPException
# pyrefly: ignore [missing-import]
from geoalchemy2.shape import to_shape
from shapely.geometry import MultiPolygon, Polygon, shape
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.land_parcel import LandParcel
from app.parcels.schemas import GeoJSONFeature, GeoJSONFeatureCollection, ParcelGeometryUpdate


async def attach_geometry(
    session: AsyncSession,
    parcel_id: uuid.UUID,
    geometry_data: ParcelGeometryUpdate,
    user_role: str,
) -> LandParcel:
    """Validate and attach a GeoJSON geometry to a LandParcel."""
    # Enforce role-based access
    if user_role not in ["district_authority", "state_govt", "central_ministry"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to geo-tag parcels.",
        )

    # 1. Fetch parcel
    parcel = await session.get(LandParcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    # 2. Convert and validate geometry using shapely
    try:
        geom_dict = geometry_data.model_dump()
        s_geom = shape(geom_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid geometry data: {e}")

    # Ensure it's a Polygon or MultiPolygon
    if not isinstance(s_geom, (Polygon, MultiPolygon)):
        raise HTTPException(
            status_code=400,
            detail="Geometry must be a Polygon or MultiPolygon.",
        )

    # Convert Polygon to MultiPolygon if necessary
    if isinstance(s_geom, Polygon):
        s_geom = MultiPolygon([s_geom])

    # Check validity (e.g. self-intersecting)
    if not s_geom.is_valid:
        raise HTTPException(
            status_code=400,
            detail="Geometry is invalid (e.g., self-intersecting boundaries).",
        )

    # Validate bounds (lat: -90 to 90, lon: -180 to 180)
    minx, miny, maxx, maxy = s_geom.bounds
    if not (-180 <= minx <= 180 and -180 <= maxx <= 180 and -90 <= miny <= 90 and -90 <= maxy <= 90):
        raise HTTPException(
            status_code=400,
            detail="Coordinates out of valid lon/lat bounds.",
        )

    # 3. Update parcel (Convert shapely object to WKT for PostGIS)
    parcel.geometry = f"SRID=4326;{s_geom.wkt}"
    await session.commit()
    await session.refresh(parcel)
    
    return parcel


async def get_project_parcels_geojson(
    session: AsyncSession, project_id: uuid.UUID
) -> dict:
    """Return all geo-tagged parcels for a project as a FeatureCollection using ST_AsGeoJSON."""
    import json
    stmt = (
        select(LandParcel, func.ST_AsGeoJSON(LandParcel.geometry).label("geojson_str"))
        .where(LandParcel.project_id == project_id)
        .where(LandParcel.geometry.is_not(None))
    )
    result = await session.execute(stmt)
    rows = result.all()
    
    features = []
    for parcel, geojson_str in rows:
        features.append(
            {
                "type": "Feature",
                "id": str(parcel.id),
                "geometry": json.loads(geojson_str) if geojson_str else None,
                "properties": {
                    "id": str(parcel.id),
                    "project_id": str(parcel.project_id),
                    "survey_number": parcel.survey_number,
                    "land_type": parcel.land_type.value,
                    "area_hectares": float(parcel.area_hectares),
                    "state": parcel.state,
                    "district": parcel.district,
                    "taluka": parcel.taluka,
                    "village": parcel.village,
                    "possession_status": parcel.possession_status.value,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


async def get_parcels_in_bbox(
    session: AsyncSession, min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> dict:
    """Find parcels within a bounding box using PostGIS ST_MakeEnvelope and ST_AsGeoJSON."""
    import json
    bbox = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    
    stmt = (
        select(LandParcel, func.ST_AsGeoJSON(LandParcel.geometry).label("geojson_str"))
        .where(LandParcel.geometry.is_not(None))
        .where(func.ST_Intersects(LandParcel.geometry, bbox))
    )
    
    result = await session.execute(stmt)
    rows = result.all()

    features = []
    for parcel, geojson_str in rows:
        features.append(
            {
                "type": "Feature",
                "id": str(parcel.id),
                "geometry": json.loads(geojson_str) if geojson_str else None,
                "properties": {
                    "id": str(parcel.id),
                    "project_id": str(parcel.project_id),
                    "survey_number": parcel.survey_number,
                    "land_type": parcel.land_type.value,
                    "area_hectares": float(parcel.area_hectares),
                    "state": parcel.state,
                    "district": parcel.district,
                    "taluka": parcel.taluka,
                    "village": parcel.village,
                    "possession_status": parcel.possession_status.value,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}

