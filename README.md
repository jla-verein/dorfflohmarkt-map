# Dorfflohmarkt Map

An interactive map application that displays seller registrations from a Pretix event. Built with FastAPI, Leaflet.js, and OpenStreetMap.

## Features

- 🗺️ Interactive map powered by OpenStreetMap and Leaflet
- 🏷️ Filter sellers by product categories
- 📍 Cluster markers for better performance with large datasets
- 🐳 Docker support for easy deployment
- ⚙️ Environment-based configuration
- 📱 Responsive design (desktop and mobile)

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose (optional, for containerized deployment)

## Setup

### 1. Clone the repository and install dependencies

```bash
cd dorfflohmarkt-map
uv sync
```

### 2. Configure environment variables

Copy the `.env.example` file to `.env` and fill in your Pretix credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Pretix configuration:

```env
PRETIX_API_TOKEN=your-pretix-api-token-here
PRETIX_ORGANIZER=your-organizer-slug
PRETIX_EVENT_SLUG=your-event-slug
PRETIX_PRODUCT_ID=123
API_HOST=http://localhost:8000
```

**Finding your Pretix credentials:**
- Get your API token from your Pretix account settings
- Find the organizer slug and event slug in your Pretix event URL
- Find the product ID in the Pretix event editor

### 3. Run the application

**Development:**

```bash
uv run python -m uvicorn src.main:app --reload
```

The application will be available at `http://localhost:8000`

**Production with Docker:**

```bash
docker-compose up
```

## API Endpoints

- `GET /` - Interactive map page
- `GET /api/sellers` - JSON data of all sellers with their categories
- `GET /health` - Health check endpoint
- `POST /api/refresh` - Refresh seller data from Pretix

## Project Structure

```
dorfflohmarkt-map/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic data models
│   ├── pretix_client.py     # Pretix API client
│   └── map_generator.py     # Leaflet map HTML generation
├── templates/
│   └── map.html             # Map HTML template
├── pyproject.toml           # uv project configuration
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── .env.example             # Environment variables template
└── README.md                # This file
```

## How it works

1. **Data fetching**: The application fetches paid orders from Pretix for a specific product
2. **Data extraction**: Seller information (name, address, categories) is extracted from order data
3. **Map generation**: An interactive Leaflet map is generated with seller markers
4. **Filtering**: Users can filter sellers by category using client-side JavaScript
5. **Clustering**: Markers are clustered for better performance with large datasets

## Data flow

```
Pretix API
    ↓
pretix_client.py (fetch orders)
    ↓
models.py (parse data)
    ↓
map_generator.py (generate HTML)
    ↓
Leaflet.js (render map)
    ↓
User sees interactive map
```

## Caching

Seller data is cached in memory and refreshed when:
- The server starts
- The `/api/refresh` endpoint is called

For production deployments with multiple instances, consider implementing a shared cache (Redis).

## Geocoding

Currently, addresses are displayed as text in popups. To add coordinates:

1. Implement geocoding in `pretix_client.py` using `geopy` (already installed)
2. Call a geocoding service (e.g., Nominatim) to convert addresses to coordinates
3. Store coordinates in the `Seller` model

Example with geopy:

```python
from geopy.geocoders import Nominatim

geocoder = Nominatim(user_agent="dorfflohmarkt-map")
location = geocoder.geocode(address_string)
if location:
    seller.latitude = location.latitude
    seller.longitude = location.longitude
```

## Customization

### Styling

Edit the `<style>` section in `map_generator.py` to customize colors, layout, and appearance.

### Map tiles

Change the tile layer in `map_generator.py`:

```javascript
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    // Change to another provider:
    // https://wiki.openstreetmap.org/wiki/Tile_servers
})
```

### Categories

The categories are automatically extracted from Pretix order answers. Make sure your Pretix event has category questions configured.

## Troubleshooting

**"Error fetching sellers from Pretix"**
- Check your API token in `.env`
- Verify organizer slug and event slug are correct
- Ensure the product ID exists and has orders

**Map not showing markers**
- Check if seller addresses have been geocoded (coordinates)
- Verify the Pretix order data includes addresses

**Docker build fails**
- Ensure uv.lock file is present: `uv sync`
- Check that Docker and Docker Compose are installed

## Development

### Running tests

```bash
uv run pytest
```

### Code formatting and linting

```bash
uv run black src/
uv run ruff check src/
```

### Adding dependencies

```bash
uv add package-name
```

## License

[Add your license here]

## Support

For issues or questions, please open an issue on the project repository.
