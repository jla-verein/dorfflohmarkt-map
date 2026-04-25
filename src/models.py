"""Data models for sellers and orders."""
from typing import Optional
from pydantic import BaseModel


class Seller(BaseModel):
    """A seller registering for the Dorfflohmarkt."""

    address: str
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    categories: list[str]
    location_description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "address": "123 Main St",
                "city": "Berlin",
                "postal_code": "10115",
                "country": "DE",
                "categories": ["🧒 Kinder & Baby", "👕 Kleidung & Accessoires"],
                "location_description": "Großes Regal mit Spielzeugen",
                "latitude": 52.5200,
                "longitude": 13.4050,
            }
        }


class SellersResponse(BaseModel):
    """Response containing all sellers."""

    sellers: list[Seller]
    categories: list[str]
    total: int
