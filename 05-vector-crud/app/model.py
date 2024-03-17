from typing import Optional

from pydantic import BaseModel


class PoiCreate(BaseModel):
    name: str
    longitude: float
    latitude: float


class PoiUpdate(BaseModel):
    name: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
