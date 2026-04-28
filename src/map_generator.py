"""Generate Leaflet map HTML with seller data."""
import json
from .models import Seller


def generate_map_html(sellers: list[Seller], categories: list[str]) -> str:
    """
    Generate HTML for an interactive Leaflet map with seller markers.

    Args:
        sellers: List of Seller objects
        categories: List of available categories

    Returns:
        HTML string for the map
    """
    # Convert sellers to GeoJSON format
    geojson_features = []
    for seller in sellers:
        # Skip sellers without coordinates
        if seller.latitude is None or seller.longitude is None:
            continue

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [seller.longitude, seller.latitude],
            },
            "properties": {
                "address": seller.address,
                "city": seller.city,
                "postal_code": seller.postal_code,
                "country": seller.country,
                "categories": seller.categories,
                "location_description": seller.location_description,
            },
        }
        geojson_features.append(feature)

    geojson = {"type": "FeatureCollection", "features": geojson_features}
    geojson_json = json.dumps(geojson)

    # Generate category checkboxes
    category_filters = "\n".join(
        [
            f'            <label><input type="checkbox" class="category-filter" value="{cat}" checked> {cat}</label>'
            for cat in categories
        ]
    )

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dorfflohmarkt Karte</title>

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
    <!-- Leaflet MarkerCluster CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.Default.min.css" />
    <!-- Font Awesome for Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <!-- Leaflet Awesome Markers -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css" />

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen",
                "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue",
                sans-serif;
            background: #f5f5f5;
        }}

        .container {{
            display: flex;
            height: 100vh;
        }}

        #map {{
            flex: 1;
            height: 100%;
        }}

        .sidebar {{
            width: 320px;
            background: white;
            box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
            padding: 20px;
            z-index: 100;
        }}

        .sidebar h1 {{
            font-size: 20px;
            margin-bottom: 20px;
            color: #1a1a1a;
            font-weight: 700;
        }}

        .filters {{
            margin-bottom: 25px;
        }}

        .filters h2 {{
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 12px;
            color: #333;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .category-filters {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .category-filters label {{
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            font-size: 14px;
            color: #444;
            padding: 4px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }}

        .category-filters label:hover {{
            background-color: #f0f0f0;
        }}

        .category-filters input[type="checkbox"] {{
            cursor: pointer;
            width: 18px;
            height: 18px;
            accent-color: #2196F3;
        }}

        .stats {{
            padding: 15px;
            background: #f9f9f9;
            border-radius: 6px;
            border-left: 4px solid #2196F3;
            font-size: 13px;
            color: #555;
        }}

        .stats p {{
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
        }}

        .stats strong {{
            color: #333;
        }}

        .navigation {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}

        .nav-link {{
            display: inline-block;
            background: #2196F3;
            color: white;
            padding: 10px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: background-color 0.2s;
            width: 100%;
            text-align: center;
        }}

        .nav-link:hover {{
            background: #1976D2;
        }}

        .sidebar-toggle {{
            display: none;
        }}

        @media (max-width: 768px) {{
            .container {{
                flex-direction: column;
                height: 100vh;
            }}

            .sidebar {{
                width: 100%;
                height: 45%;
                max-height: none;
                position: relative;
                bottom: auto;
                left: auto;
                right: auto;
                box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.15);
                overflow-y: auto;
                -webkit-overflow-scrolling: touch;
                z-index: 50;
                border-top: 1px solid #e0e0e0;
                padding: 15px;
            }}

            .sidebar.sidebar-hidden {{
                max-height: none;
                overflow-y: auto;
                padding: 15px;
            }}

            #map {{
                height: 55%;
                width: 100%;
                flex: 0 0 55%;
            }}

            .sidebar h1 {{
                font-size: 16px;
                margin-bottom: 12px;
            }}

            .filters {{
                margin-bottom: 15px;
            }}

            .filters h2 {{
                font-size: 11px;
            }}

            .category-filters {{
                gap: 6px;
            }}

            .category-filters label {{
                font-size: 12px;
                padding: 2px;
            }}

            .category-filters input[type="checkbox"] {{
                width: 16px;
                height: 16px;
            }}

            .stats {{
                font-size: 11px;
                padding: 10px;
            }}

            .stats p {{
                margin-bottom: 4px;
            }}

            .nav-link {{
                padding: 8px 12px;
                font-size: 12px;
            }}
        }}

        .popup-content {{
            min-width: 220px;
        }}

        .popup-content .address {{
            font-size: 13px;
            color: #555;
            margin-bottom: 10px;
            line-height: 1.4;
        }}

        .popup-content .categories {{
            font-size: 12px;
            margin-top: 8px;
        }}

        .popup-content .categories strong {{
            display: block;
            margin-bottom: 6px;
            color: #333;
        }}

        .popup-content .category-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            color: white;
            padding: 3px 10px;
            border-radius: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
            font-size: 11px;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar" id="sidebar">
            <h1>🛍️ 2. Angelbachtaler Dorfflohmarkt</h1>

            <div class="filters">
                <h2>Kategorien</h2>
                <div class="category-filters">
{category_filters}
                </div>
            </div>

            <div class="stats">
                <p><strong>Flohmarktstände:</strong> <span id="seller-count">0</span></p>
                <p><strong>Sichtbar:</strong> <span id="visible-count">0</span></p>
            </div>

            <div class="navigation">
                <a href="/locations" class="nav-link">📋 Alle Orte</a>
            </div>
        </div>

        <div id="map"></div>
    </div>

    <!-- Leaflet JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
    <!-- Leaflet MarkerCluster JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/leaflet.markercluster.min.js"></script>
    <!-- Leaflet Awesome Markers -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.min.js"></script>

    <script>
        // Initialize map (will be centered after loading data)
        const map = L.map('map').setView([51.5, 10.0], 6);

        // Add OpenStreetMap tile layer
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19,
        }}).addTo(map);

        // Data from backend
        const geoJsonData = {geojson_json};
        const allCategories = {json.dumps(categories)};

        // Store all markers
        let markers = {{}};
        let markerClusterGroup = L.markerClusterGroup({{
            maxClusterRadius: 80,
            iconCreateFunction: function(cluster) {{
                const count = cluster.getChildCount();
                let size = 'small';
                let color = '#0099ff';

                if (count > 10) {{
                    size = 'large';
                    color = '#d41159';
                }} else if (count > 5) {{
                    size = 'medium';
                    color = '#ff8c00';
                }}

                return L.divIcon({{
                    html: '<div style="background:' + color + '; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px;">' + count + '</div>',
                    className: 'cluster-' + size,
                    iconSize: [40, 40]
                }});
            }}
        }});

        // Create custom marker icon
        function getMarkerColor(index) {{
            const colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0', '#00BCD4'];
            return colors[index % colors.length];
        }}

        // Create markers from GeoJSON
        function createMarkers() {{
            let bounds = L.latLngBounds();
            let markerIndex = 0;

            geoJsonData.features.forEach(feature => {{
                const props = feature.properties;
                const coords = feature.geometry.coordinates;
                const latlng = [coords[1], coords[0]];

                // Create a styled marker
                const marker = L.circleMarker(latlng, {{
                    radius: 10,
                    fillColor: getMarkerColor(markerIndex),
                    color: '#ffffff',
                    weight: 3,
                    opacity: 1,
                    fillOpacity: 0.85
                }});

                // Add a pulsing effect with shadow
                marker.setStyle({{
                    className: 'seller-marker'
                }});

                const popupContent = `
                    <div class="popup-content">
                        <div class="address">
                            <strong>📍 Adresse:</strong><br>
                            ${{props.address}}<br>
                            ${{props.postal_code}} ${{props.city}}
                        </div>
                        ${{props.location_description ? '<div class="location-desc" style="font-size: 13px; color: #333; margin: 8px 0; padding: 8px; background: #f5f5f5; border-radius: 4px;"><strong>📍 Standort:</strong> ' + props.location_description + '</div>' : ''}}
                        <div class="categories">
                            <strong>🏷️ Kategorien:</strong><br>
                            ${{props.categories.map(cat => `<span class="category-badge">${{cat}}</span>`).join('')}}
                        </div>
                    </div>
                `;

                marker.bindPopup(popupContent);
                marker.on('click', function() {{
                    marker.openPopup();
                }});

                markers[markerIndex] = {{
                    marker: marker,
                    categories: props.categories
                }};

                markerClusterGroup.addLayer(marker);
                bounds.extend(latlng);
                markerIndex++;
            }});

            map.addLayer(markerClusterGroup);

            // Fit map to bounds
            if (geoJsonData.features.length > 0) {{
                map.fitBounds(bounds, {{ padding: [50, 50] }});
            }}
        }}

        createMarkers();

        // Handle category filter changes
        const categoryFilters = document.querySelectorAll('.category-filter');
        categoryFilters.forEach(filter => {{
            filter.addEventListener('change', updateFilters);
        }});

        function updateFilters() {{
            const selectedCategories = Array.from(categoryFilters)
                .filter(f => f.checked)
                .map(f => f.value);

            let visibleCount = 0;

            Object.values(markers).forEach(item => {{
                const hasSelectedCategory = item.categories.some(cat =>
                    selectedCategories.includes(cat)
                );

                if (hasSelectedCategory) {{
                    markerClusterGroup.addLayer(item.marker);
                    visibleCount++;
                }} else {{
                    markerClusterGroup.removeLayer(item.marker);
                }}
            }});

            document.getElementById('visible-count').textContent = visibleCount;
        }}

        // Initialize stats
        document.getElementById('seller-count').textContent = geoJsonData.features.length;
        document.getElementById('visible-count').textContent = geoJsonData.features.length;
    </script>
</body>
</html>
"""

    return html


def generate_locations_html(sellers: list[Seller], categories: list[str]) -> str:
    """
    Generate HTML for locations list page with DataTables.

    Args:
        sellers: List of Seller objects
        categories: List of available categories

    Returns:
        HTML string for the locations page
    """
    # Prepare data for the tables
    sellers_data = []
    unique_cities = set()
    for seller in sellers:
        unique_cities.add(seller.city)
        sellers_data.append({
            "address": seller.address,
            "city": seller.city,
            "postal_code": seller.postal_code,
            "categories": ", ".join(seller.categories),
            "location_description": seller.location_description or "",
            "latitude": seller.latitude,
            "longitude": seller.longitude,
        })

    sellers_json = json.dumps(sellers_data)
    has_multiple_cities = len(unique_cities) > 1

    # Build columns array based on whether we have multiple cities
    columns_def = """[
                    {{
                        data: null,
                        render: function() {{
                            return '<input type="checkbox" class="row-checkbox">';
                        }},
                        orderable: false,
                        searchable: false
                    }},
                    {{ data: 'address' }},"""

    if has_multiple_cities:
        columns_def += """
                    {{ data: 'city' }},
                    {{ data: 'postal_code' }},"""

    columns_def += """
                    {{ data: 'location_description' }},
                    {{ data: 'categories' }}
                ]"""

    # Prepare grouped by categories and sort by address
    grouped = {}
    for seller in sellers:
        for category in seller.categories:
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                "address": seller.address,
                "city": seller.city,
                "postal_code": seller.postal_code,
                "location_description": seller.location_description or "",
            })

    # Sort addresses within each category
    for category in grouped:
        grouped[category].sort(key=lambda x: (x['city'], x['address']))

    # Sort categories
    sorted_categories = sorted(grouped.keys())

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2. Angelbachtaler Dorfflohmarkt - Alle Orte</title>

    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/2.1.4/css/dataTables.bootstrap5.css" />
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" />

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen",
                "Ubuntu", "Cantarell", "Fira Sans", "Droid Sans", "Helvetica Neue",
                sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container-custom {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            padding: 30px;
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .header h1 {{
            font-size: 28px;
            color: #1a1a1a;
            font-weight: 700;
            margin: 0;
            flex: 1;
        }}

        .header-buttons {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .back-link {{
            background: #2196F3;
            color: white;
            padding: 10px 16px;
            border-radius: 4px;
            text-decoration: none;
            font-weight: 500;
            transition: background-color 0.2s;
            font-size: 14px;
        }}

        .back-link:hover {{
            background: #1976D2;
            color: white;
        }}

        .back-link.print {{
            background: #4CAF50;
        }}

        .back-link.print:hover {{
            background: #45a049;
        }}

        .tabs {{
            margin-bottom: 20px;
        }}

        .nav-tabs {{
            border-bottom: 2px solid #e0e0e0;
        }}

        .nav-link {{
            color: #666;
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: 500;
            padding: 12px 20px;
            transition: all 0.3s;
        }}

        .nav-link:hover {{
            color: #2196F3;
        }}

        .nav-link.active {{
            color: #2196F3;
            border-bottom-color: #2196F3;
            background: transparent;
        }}

        .export-buttons {{
            margin-bottom: 15px;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .export-btn {{
            background: #2196F3;
            color: white;
            padding: 8px 14px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: background-color 0.2s;
        }}

        .export-btn:hover {{
            background: #1976D2;
        }}

        .export-btn:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}

        .selection-controls {{
            margin-bottom: 15px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 4px;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }}

        .selection-controls label {{
            margin-bottom: 0;
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
        }}

        .selection-info {{
            font-size: 12px;
            color: #666;
            margin-left: auto;
        }}

        .table {{
            font-size: 14px;
        }}

        .table thead {{
            background: #f9f9f9;
        }}

        .table thead th {{
            color: #333;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
            padding: 12px;
        }}

        .table tbody td {{
            padding: 12px;
            border-bottom: 1px solid #f0f0f0;
            vertical-align: middle;
        }}

        .table tbody tr:hover {{
            background-color: #f5f9ff;
        }}

        .table tbody tr.selected {{
            background-color: #e3f2fd;
        }}

        .category-section {{
            margin-bottom: 30px;
        }}

        .category-header {{
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-weight: 600;
            font-size: 15px;
        }}

        .category-table {{
            margin-bottom: 20px;
        }}

        .category-table .table {{
            margin-bottom: 0;
        }}

        .badge {{
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}

        .dataTables_wrapper {{
            padding: 0;
        }}

        .dataTables_filter {{
            margin-bottom: 15px;
        }}

        .dataTables_filter input {{
            border-radius: 4px;
            border: 1px solid #ddd;
            padding: 8px 12px;
        }}

        .dataTables_info {{
            font-size: 13px;
            color: #666;
        }}

        .dataTables_paginate {{
            margin-top: 15px;
        }}

        @media print {{
            .container-custom {{
                box-shadow: none;
                padding: 0;
            }}

            .header {{
                display: none;
            }}

            .tabs {{
                display: none;
            }}

            .export-buttons {{
                display: none;
            }}

            .selection-controls {{
                display: none;
            }}

            .nav-tabs {{
                display: none;
            }}

            #table-panel {{
                display: block !important;
            }}

            .table {{
                font-size: 11px;
            }}

            .table thead th {{
                padding: 6px;
            }}

            .table tbody td {{
                padding: 6px;
            }}
        }}

        @media (max-width: 768px) {{
            .container-custom {{
                padding: 15px;
            }}

            .header {{
                flex-direction: column;
            }}

            .header h1 {{
                font-size: 22px;
            }}

            .header-buttons {{
                width: 100%;
            }}

            .back-link {{
                flex: 1;
            }}

            .table {{
                font-size: 12px;
            }}

            .table thead th {{
                padding: 8px;
            }}

            .table tbody td {{
                padding: 8px;
            }}

            .export-buttons {{
                width: 100%;
            }}

            .export-btn {{
                flex: 1;
                min-width: 100px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container-custom">
        <div class="header">
            <h1>🛍️ 2. Angelbachtaler Dorfflohmarkt - Alle Orte</h1>
            <div class="header-buttons">
                <a href="/" class="back-link">← Zur Karte</a>
                <a href="javascript:window.print()" class="back-link print">🖨️ Drucken</a>
            </div>
        </div>

        <!-- Nav tabs -->
        <div class="tabs">
            <ul class="nav nav-tabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="table-tab" data-bs-toggle="tab" data-bs-target="#table-panel" type="button" role="tab">
                        📋 Alle Flohmarktstände
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="categories-tab" data-bs-toggle="tab" data-bs-target="#categories-panel" type="button" role="tab">
                        🏷️ Nach Kategorie
                    </button>
                </li>
            </ul>
        </div>

        <!-- Tab panes -->
        <div class="tab-content">
            <!-- All Sellers Tab -->
            <div class="tab-pane fade show active" id="table-panel" role="tabpanel">
                <div class="export-buttons">
                    <button class="export-btn" id="export-csv-btn">📥 Als CSV exportieren</button>
                    <button class="export-btn" id="export-excel-btn">📥 Als Excel exportieren</button>
                    <button class="export-btn" id="export-gmaps-btn">📥 Google Maps (.kml)</button>
                </div>

                <table id="sellers-table" class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th style="width: 30px;"><input type="checkbox" class="check-header"></th>
                            <th>Adresse</th>
                            {f'<th>Stadt</th>' if has_multiple_cities else ''}
                            {f'<th>PLZ</th>' if has_multiple_cities else ''}
                            <th>Standort</th>
                            <th>Kategorien</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
            </div>

            <!-- By Category Tab -->
            <div class="tab-pane fade" id="categories-panel" role="tabpanel">
"""

    # Add category sections sorted by address
    for category in sorted_categories:
        locations = grouped[category]
        html += f"""
                <div class="category-section">
                    <div class="category-header">🏷️ {category} ({len(locations)})</div>
                    <div class="category-table">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Adresse</th>
                                    {f'<th>Stadt</th>' if has_multiple_cities else ''}
                                    {f'<th>PLZ</th>' if has_multiple_cities else ''}
                                    <th>Standort</th>
                                </tr>
                            </thead>
                            <tbody>
"""
        for location in locations:
            city_col = f"<td>{location['city']}</td>" if has_multiple_cities else ""
            postal_col = f"<td>{location['postal_code']}</td>" if has_multiple_cities else ""
            html += f"""
                                <tr>
                                    <td>{location['address']}</td>
                                    {city_col}{postal_col}<td>{location.get('location_description', '')}</td>
                                </tr>
"""
        html += """
                            </tbody>
                        </table>
                    </div>
                </div>
"""

    html += f"""
            </div>
        </div>
    </div>

    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <!-- Bootstrap JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <!-- DataTables JS -->
    <script src="https://cdn.datatables.net/2.1.4/js/dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/2.1.4/js/dataTables.bootstrap5.js"></script>
    <!-- SheetJS for Excel export -->
    <script src="https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js"></script>

    <script>
        // Initialize DataTable
        const sellersData = {sellers_json};
        let table;

        $(document).ready(function() {{
            table = $('#sellers-table').DataTable({{
                data: sellersData,
                columns: {columns_def},
                language: {{
                    "sEmptyTable": "Keine Daten in der Tabelle",
                    "sInfo": "_START_ bis _END_ von _TOTAL_ Einträgen",
                    "sInfoEmpty": "0 bis 0 von 0 Einträgen",
                    "sInfoFiltered": "(gefiltert aus _MAX_ Einträgen)",
                    "sLengthMenu": "_MENU_ Einträge pro Seite",
                    "sSearch": "Suchen:",
                    "sZeroRecords": "Keine übereinstimmenden Einträge",
                    "oPaginate": {{
                        "sFirst": "« Erste",
                        "sLast": "Letzte »",
                        "sNext": "Nächste",
                        "sPrevious": "Zurück"
                    }}
                }},
                order: [[1, 'asc']],
                paging: true,
                pageLength: 25,
                ordering: true,
                searching: true,
                responsive: true
            }});

            // Update total count
            document.getElementById('total-count').textContent = sellersData.length;

            // Handle select all checkbox (header checkbox)
            const headerCheckbox = document.querySelector('.check-header');
            if (headerCheckbox) {{
                headerCheckbox.addEventListener('change', function() {{
                    document.querySelectorAll('.row-checkbox').forEach(cb => {{
                        cb.checked = this.checked;
                        cb.dispatchEvent(new Event('change'));
                    }});
                }});
            }}

            // Handle row selection
            $(document).on('change', '.row-checkbox', function() {{
                const count = document.querySelectorAll('.row-checkbox:checked').length;
                document.getElementById('selected-count').textContent = count;

                // Update row highlighting
                $(this).closest('tr').toggleClass('selected');

                // Update header checkbox state
                const headerCheckbox = document.querySelector('.check-header');
                const totalCheckboxes = document.querySelectorAll('.row-checkbox').length;
                if (headerCheckbox) {{
                    headerCheckbox.checked = count === totalCheckboxes && totalCheckboxes > 0;
                    headerCheckbox.indeterminate = count > 0 && count < totalCheckboxes;
                }}
            }});

            // CSV Export
            document.getElementById('export-csv-btn').addEventListener('click', function() {{
                exportAsCSV();
            }});

            // Excel Export
            document.getElementById('export-excel-btn').addEventListener('click', function() {{
                exportAsExcel();
            }});

            // Google Maps KML Export
            document.getElementById('export-gmaps-btn').addEventListener('click', function() {{
                exportAsKML();
            }});
        }});

        function getSelectedRows() {{
            const selected = [];
            document.querySelectorAll('.row-checkbox:checked').forEach((checkbox, index) => {{
                selected.push(sellersData[table.row(checkbox.closest('tr')).index()]);
            }});
            return selected.length > 0 ? selected : sellersData;
        }}

        function exportAsCSV() {{
            const rows = getSelectedRows();
            let csv = 'Adresse,Stadt,PLZ,Standort,Kategorien\\n';

            rows.forEach(row => {{
                const address = '"' + (row.address || '').replace(/"/g, '""') + '"';
                const city = '"' + (row.city || '').replace(/"/g, '""') + '"';
                const postal = '"' + (row.postal_code || '').replace(/"/g, '""') + '"';
                const description = '"' + (row.location_description || '').replace(/"/g, '""') + '"';
                const categories = '"' + (row.categories || '').replace(/"/g, '""') + '"';
                csv += address + ',' + city + ',' + postal + ',' + description + ',' + categories + '\\n';
            }});

            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'dorfflohmarkt-' + new Date().toISOString().split('T')[0] + '.csv';
            link.click();
        }}

        function exportAsExcel() {{
            const rows = getSelectedRows();
            const data = rows.map(row => ({{
                'Adresse': row.address,
                'Stadt': row.city,
                'PLZ': row.postal_code,
                'Standort': row.location_description,
                'Kategorien': row.categories
            }}));

            const ws = XLSX.utils.json_to_sheet(data);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Flohmarktstände');
            XLSX.writeFile(wb, 'dorfflohmarkt-' + new Date().toISOString().split('T')[0] + '.xlsx');
        }}

        function exportAsKML() {{
            const rows = getSelectedRows();

            let kml = '<?xml version="1.0" encoding="UTF-8"?>\\n';
            kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\\n';
            kml += '  <Document>\\n';
            kml += '    <name>Dorfflohmarkt Stände</name>\\n';
            kml += '    <description>Flohmarktstände mit Adressen und Kategorien</description>\\n';

            rows.forEach((row, index) => {{
                if (row.latitude && row.longitude) {{
                    kml += '    <Placemark>\\n';
                    kml += '      <name>' + escapeXml(row.address) + '</name>\\n';
                    kml += '      <description>' + escapeXml(row.postal_code + ' ' + row.city + '\\n' + row.categories) + '</description>\\n';
                    kml += '      <Point>\\n';
                    kml += '        <coordinates>' + row.longitude + ',' + row.latitude + ',0</coordinates>\\n';
                    kml += '      </Point>\\n';
                    kml += '    </Placemark>\\n';
                }}
            }});

            kml += '  </Document>\\n';
            kml += '</kml>';

            const blob = new Blob([kml], {{ type: 'application/vnd.google-earth.kml+xml;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'dorfflohmarkt-' + new Date().toISOString().split('T')[0] + '.kml';
            link.click();

            alert('KML-Datei exportiert und kann in Google Maps importiert werden.');
        }}

        function escapeXml(str) {{
            return (str || '').replace(/[<>&'"]/g, function(c) {{
                switch (c) {{
                    case '<': return '&lt;';
                    case '>': return '&gt;';
                    case '&': return '&amp;';
                    case '\\\'': return '&apos;';
                    case '"': return '&quot;';
                }}
            }});
        }}
    </script>
</body>
</html>
"""

    return html

