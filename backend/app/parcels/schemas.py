from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class GeoJSONFeature(BaseModel):
    type: str = Field("Feature", pattern="^Feature$")
    geometry: dict[str, Any]
    properties: dict[str, Any] = {}

class GeoJSONFeatureCollection(BaseModel):
    type: str = Field("FeatureCollection", pattern="^FeatureCollection$")
    features: list[GeoJSONFeature]


class ParcelGeometryUpdate(BaseModel):
    """GeoJSON MultiPolygon or Polygon geometry to update a parcel's geometry."""
    type: str = Field(..., description="Must be Polygon or MultiPolygon")
    coordinates: list[Any] = Field(..., description="Coordinates array based on geometry type")
