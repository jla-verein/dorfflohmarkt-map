"""Configuration management for the Dorfflohmarkt Map API."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    pretix_api_token: str
    pretix_event_slug: str
    pretix_organizer: str
    pretix_product_id: int
    api_host: str = "http://localhost:8000"
    pretix_api_base_url: str = "https://pretix.eu/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
