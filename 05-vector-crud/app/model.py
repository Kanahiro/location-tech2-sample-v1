from pydantic import BaseModel


class PoiCreate(BaseModel):
    name: str
    longitude: float
    latitude: float
