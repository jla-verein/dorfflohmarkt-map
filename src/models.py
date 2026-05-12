"""Data models for sellers and orders."""
from typing import Optional, Literal
from pydantic import BaseModel


class Seller(BaseModel):
    """A seller registering for the Dorfflohmarkt."""

    address: str
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    categories: list[str]
    location_description: Optional[str] = None
    other_text: Optional[str] = None
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


class StaticLocation(BaseModel):
    """A static map location such as toilets, food/drink, or parking."""

    id: Optional[str] = None
    type: Literal["toilets", "food_and_drink", "parking"]
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "DE"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    osmid: Optional[str] = None
    opening_hours: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wc-1",
                "type": "toilets",
                "name": "Öffentliche Toilette",
                "address": "Talstraße 11",
                "postal_code": "74918",
                "city": "Angelbachtal",
                "opening_hours": "10:00 - 18:00",
                "osmid": "N123456789"
            }
        }


class SellersResponse(BaseModel):
    """Response containing all sellers."""

    sellers: list[Seller]
    categories: list[str]
    total: int
