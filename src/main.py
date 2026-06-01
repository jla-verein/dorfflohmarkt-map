"""FastAPI application for the Dorfflohmarkt Map."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from .pretix_client import pretix_client
from .models import SellersResponse
from .map_generator import generate_map_html, generate_locations_html, generate_static_map_html
from .static_locations import load_static_locations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dorfflohmarkt Map API",
    description="API for displaying Pretix seller registrations on a map",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache for sellers and static location data
_sellers_cache = None
_categories_cache = None
_static_locations_cache = None


def get_static_locations_data():
    global _static_locations_cache
    if _static_locations_cache is None:
        _static_locations_cache = load_static_locations()
    return _static_locations_cache


async def get_sellers_data():
    """Get sellers from cache or fetch from Pretix API."""
    global _sellers_cache, _categories_cache

    if _sellers_cache is None:
        try:
            _sellers_cache = await pretix_client.get_sellers()
            _categories_cache = pretix_client.get_all_categories(_sellers_cache)
            logger.info(f"Fetched {len(_sellers_cache)} sellers from Pretix")
        except Exception as e:
            logger.error(f"Error fetching sellers from Pretix: {e}")
            raise HTTPException(status_code=500, detail="Error fetching sellers from Pretix")

    assert _categories_cache is not None
    return _sellers_cache, _categories_cache


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/sellers", response_model=SellersResponse)
async def get_sellers():
    """Get all sellers with their categories."""
    sellers, categories = await get_sellers_data()
    return SellersResponse(
        sellers=sellers,
        categories=categories,
        total=len(sellers),
    )


@app.get("/", response_class=HTMLResponse)
async def get_map():
    """Get the interactive map page."""
    sellers, categories = await get_sellers_data()
    static_locations = get_static_locations_data()
    html = generate_map_html(sellers, categories, static_locations)
    return html


@app.get("/locations", response_class=HTMLResponse)
async def get_locations():
    """Get the locations list page."""
    sellers, categories = await get_sellers_data()
    html = generate_locations_html(sellers, categories)
    return html


@app.get("/static-map", response_class=HTMLResponse)
async def get_static_map(
    clustering: bool = True,
    controls: bool = True,
    static_locations: bool = True,
):
    """Get a static map with optional configuration.

    Query parameters:
    - clustering: Enable marker clustering (default: true)
    - controls: Enable map controls like zoom and attribution (default: true)
    - static_locations: Show static location markers (default: true)
    """
    sellers, _ = await get_sellers_data()
    static_locs = get_static_locations_data()
    html = generate_static_map_html(
        sellers,
        static_locs,
        enable_clustering=clustering,
        enable_controls=controls,
        enable_static_locations=static_locations,
    )
    return html


@app.post("/api/refresh")
async def refresh_sellers():
    """Refresh sellers data from Pretix API."""
    global _sellers_cache, _categories_cache, _static_locations_cache
    _sellers_cache = None
    _categories_cache = None
    _static_locations_cache = None
    sellers, categories = await get_sellers_data()
    return {
        "status": "refreshed",
        "sellers_count": len(sellers),
        "categories": categories,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
