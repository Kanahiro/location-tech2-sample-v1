from typing import Optional

from pydantic import BaseModel


class PointCreate(BaseModel):
    longitude: float
    latitude: float


class PointUpdate(BaseModel):
    longitude: Optional[float] = None
    latitude: Optional[float] = None
