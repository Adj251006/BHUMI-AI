import uuid
from typing import Any

import shapely
from fastapi import HTTPException
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
) -> GeoJSONFeatureCollection:
    """Return all geo-tagged parcels for a project as a FeatureCollection."""
    stmt = (
        select(LandParcel)
        .where(LandParcel.project_id == project_id)
        .where(LandParcel.geometry.is_not(None))
    )
    result = await session.execute(stmt)
    parcels = result.scalars().all()

    return _build_feature_collection(parcels)


async def get_parcels_in_bbox(
    session: AsyncSession, min_lon: float, min_lat: float, max_lon: float, max_lat: float
) -> GeoJSONFeatureCollection:
    """Find parcels within a bounding box using PostGIS ST_MakeEnvelope."""
    # ST_MakeEnvelope(xmin, ymin, xmax, ymax, srid)
    bbox = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    
    stmt = (
        select(LandParcel)
        .where(LandParcel.geometry.is_not(None))
        # ST_Intersects checks if the geometries overlap/intersect
        .where(func.ST_Intersects(LandParcel.geometry, bbox))
    )
    
    result = await session.execute(stmt)
    parcels = result.scalars().all()

    return _build_feature_collection(parcels)


def _build_feature_collection(parcels: list[LandParcel]) -> GeoJSONFeatureCollection:
    """Helper to convert LandParcel objects to GeoJSON FeatureCollection."""
    features = []
    for p in parcels:
        if p.geometry is None:
            continue
            
        # Convert WKB geometry from db to shapely geometry
        shply_geom = to_shape(p.geometry)
        
        # Convert to python dict using shapely.geometry.mapping
        geom_dict = shapely.geometry.mapping(shply_geom)
        
        properties = {
            "id": str(p.id),
            "project_id": str(p.project_id),
            "survey_number": p.survey_number,
            "land_type": p.land_type.value,
            "area_hectares": float(p.area_hectares),
            "state": p.state,
            "district": p.district,
            "taluka": p.taluka,
            "village": p.village,
            "possession_status": p.possession_status.value,
        }
        
        features.append(
            GeoJSONFeature(
                geometry=geom_dict,
                properties=properties
            )
        )

    return GeoJSONFeatureCollection(features=features)
