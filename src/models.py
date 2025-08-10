from typing import Any, List

from pydantic import BaseModel


class Geometry(BaseModel):
    """Model for geometry with type and coordinates."""

    type: str
    coordinates: Any


class Feature(BaseModel):
    """Model for a feature with type, geometry, and properties."""

    type: str = "Feature"
    geometry: Geometry
    properties: dict


class FeatureCollection(BaseModel):
    """Model for a collection of features."""

    type: str = "FeatureCollection"
    features: List[Feature]
