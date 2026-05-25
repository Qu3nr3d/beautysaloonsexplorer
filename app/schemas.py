from pydantic import BaseModel
from typing import Optional


class SalonBase(BaseModel):
    name:         str
    address:      str
    district:     str
    phone:        Optional[str] = ""
    website:      Optional[str] = ""
    services:     Optional[str] = ""
    price_range:  Optional[str] = ""
    rating:       Optional[str] = ""
    review_count: Optional[str] = ""
    lat:          Optional[float] = 0.0
    lon:          Optional[float] = 0.0
    source:       Optional[str] = ""


class SalonCreate(SalonBase):
    pass


class SalonUpdate(BaseModel):
    """Wszystkie pola opcjonalne — PATCH semantyka."""
    name:         Optional[str]   = None
    address:      Optional[str]   = None
    district:     Optional[str]   = None
    phone:        Optional[str]   = None
    website:      Optional[str]   = None
    services:     Optional[str]   = None
    price_range:  Optional[str]   = None
    rating:       Optional[str]   = None
    review_count: Optional[str]   = None
    lat:          Optional[float] = None
    lon:          Optional[float] = None
    source:       Optional[str]   = None


class SalonResponse(SalonBase):
    id: int

    model_config = {"from_attributes": True}


class SalonListItem(BaseModel):
    """Skrócony widok dla listingu."""
    id:          int
    name:        str
    district:    str
    rating:      Optional[str] = ""
    price_range: Optional[str] = ""

    model_config = {"from_attributes": True}