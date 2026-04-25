"""FastAPI application for the Dorfflohmarkt Map."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import settings
from .pretix_client import pretix_client
from .models import SellersResponse
from .map_generator import generate_map_html, generate_locations_html

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

# Cache for sellers data
_sellers_cache = None
_categories_cache = None


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
    html = generate_map_html(sellers, categories)
    return html


@app.get("/locations", response_class=HTMLResponse)
async def get_locations():
    """Get the locations list page."""
    sellers, categories = await get_sellers_data()
    html = generate_locations_html(sellers, categories)
    return html


@app.post("/api/refresh")
async def refresh_sellers():
    """Refresh sellers data from Pretix API."""
    global _sellers_cache, _categories_cache
    _sellers_cache = None
    _categories_cache = None
    sellers, categories = await get_sellers_data()
    return {
        "status": "refreshed",
        "sellers_count": len(sellers),
        "categories": categories,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
