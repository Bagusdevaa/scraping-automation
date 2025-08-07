# API Routes Documentation v2.0

## Overview
The API has been restructured into modular routes for better organization and scalability:

```
app/api/
├── routes_new.py          # Main router (imports all modules)
├── routes.py              # Legacy routes (deprecated)
└── routes/
    ├── __init__.py
    ├── bali_exception.py   # Bali Exception specific endpoints
    ├── multi_competitor.py # Cross-competitor operations
    └── system.py          # System utilities and health checks
```

## API Endpoints

### 🏠 Bali Exception Routes (`/api/v1/bali-exception`)
- `GET /bali-exception/info` - Get competitor information and supported categories
- `POST /bali-exception/urls` - Scrape URLs only (no property details)
- `POST /bali-exception/scrape` - Scrape property details with optional Google Sheets
- `POST /bali-exception/full-workflow` - Complete workflow (default: all categories, 50 properties, save to sheets)

### 🌐 Multi-Competitor Routes (`/api/v1/multi-competitor`)
- `GET /multi-competitor/competitors` - List all available competitors and their status
- `GET /multi-competitor/competitors/{id}/info` - Get detailed competitor information
- `POST /multi-competitor/scrape-all` - Scrape from multiple competitors with separate sheets
- `POST /multi-competitor/compare-properties` - Compare properties across competitors

### ⚙️ System Routes (`/api/v1/system`)
- `GET /system/health` - Simple health check
- `GET /system/info` - Comprehensive system information (platform, memory, Chrome)
- `GET /system/chrome-status` - Chrome/ChromeDriver status and test
- `POST /system/test-scraping` - Test scraping capabilities end-to-end
- `GET /system/logs` - Get recent application logs
- `GET /system/sheets/info` - Get Google Sheets configuration and available sheets
- `POST /system/sheets/create-competitor-sheet` - Create new sheet for specific competitor

## Usage Examples

### 1. Scrape All Categories from Bali Exception (Full Workflow)
```bash
curl -X POST "http://localhost:8000/api/v1/bali-exception/full-workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "categories": ["for-sale", "for-rent"],
    "max_properties": 100,
    "save_to_sheets": true
  }'
```

### 2. Scrape Specific Category Only
```bash
curl -X POST "http://localhost:8000/api/v1/bali-exception/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "categories": ["for-sale"],
    "max_properties": 50,
    "save_to_sheets": true
  }'
```

### 3. Get URLs Only (No Property Details)
```bash
curl -X POST "http://localhost:8000/api/v1/bali-exception/urls" \
  -H "Content-Type: application/json" \
  -d '{
    "categories": ["for-sale", "for-rent"]
  }'
```

### 4. Multi-Competitor Scraping with Separate Sheets
```bash
curl -X POST "http://localhost:8000/api/v1/multi-competitor/scrape-all" \
  -H "Content-Type: application/json" \
  -d '{
    "competitors": ["bali-exception"],
    "max_properties_per_competitor": 50,
    "save_to_sheets": true
  }'
```

### 5. System Health Check
```bash
curl "http://localhost:8000/api/v1/system/health"
```

### 6. Check Google Sheets Status
```bash
curl "http://localhost:8000/api/v1/system/sheets/info"
```

### 7. Test Complete System
```bash
curl -X POST "http://localhost:8000/api/v1/system/test-scraping"
```

## Default Parameters

### Bali Exception Routes:
- **Default categories**: `["for-sale"]` for `/scrape`, `["for-sale", "for-rent"]` for `/urls`
- **Default max_properties**: `20` for `/scrape`, `50` for `/full-workflow`
- **Default save_to_sheets**: `false` for `/scrape`, `true` for `/full-workflow`

### Multi-Competitor Routes:
- **Default competitors**: All enabled competitors if not specified
- **Default max_properties_per_competitor**: `20`
- **Default save_to_sheets**: `false`

## Google Sheets Integration

### Sheet Structure:
- **Individual Competitor Sheets**: `Bali_Exception`, `Airbnb`, etc.
- **Combined Sheet**: `All_Competitors` (includes "competitor" column)
- **Auto-creation**: Sheets created automatically if they don't exist
- **Data handling**: Replace (clear + update) for consistency
- **Data sanitization**: Automatic handling of invalid values (inf, NaN, null)

### Data Safety Features:
- ✅ **Safe number parsing**: Handles `inf`, `-inf`, `NaN` values
- ✅ **String sanitization**: Removes non-printable characters
- ✅ **JSON compliance**: Ensures all data is Google Sheets compatible
- ✅ **Error recovery**: Graceful handling of malformed data

## Response Format

### Successful Response:
```json
{
  "competitor": "bali-exception",
  "categories_processed": ["for-sale", "for-rent"],
  "total_urls_found": 150,
  "properties_scraped": 50,
  "performance": {
    "success_rate": "98.0%",
    "total_errors": 1,
    "scraping_time": "2.5 minutes"
  },
  "google_sheets": {
    "sheet_name": "Bali_Exception",
    "status": "success",
    "properties_saved": 50
  },
  "properties": [...]
}
```

### Multi-Competitor Response:
```json
{
  "operation": "multi-competitor-scrape",
  "competitors_processed": 1,
  "total_properties_scraped": 50,
  "google_sheets": {
    "enabled": true,
    "sheets_created": 2,
    "results_by_competitor": {
      "bali-exception": {
        "sheet_name": "Bali_Exception",
        "status": "success",
        "properties_saved": 50
      },
      "all_competitors": {
        "sheet_name": "All_Competitors", 
        "status": "success",
        "properties_saved": 50
      }
    }
  },
  "results_by_competitor": {...}
}
```

## Future Competitors

The multi-competitor architecture is designed to easily add new competitors:

```python
# In multi_competitor.py
COMPETITORS = {
    "bali-exception": {...},
    "airbnb": {
        "name": "Airbnb",
        "scraper_class": AirbnbScraper,
        "categories": ["listings"],
        "enabled": False  # Ready for implementation
    },
    "booking": {
        "name": "Booking.com", 
        "scraper_class": BookingScraper,
        "categories": ["hotels"],
        "enabled": False
    }
}
```

## Migration from v1.0

Legacy endpoints from `routes.py` are deprecated. Use the new structure:

- Old: `POST /api/v1/scrape_comprehensive`
- New: `POST /api/v1/bali-exception/scrape`

- Old: `POST /api/v1/scrape_full_workflow` 
- New: `POST /api/v1/bali-exception/full-workflow`

## Development

To add a new competitor:

1. Create scraper class in `app/scrapers/`
2. Add competitor config to `COMPETITORS` in `multi_competitor.py`
3. Optionally create dedicated route file in `app/api/routes/`
4. Update `routes_new.py` to include new routes

## Quick Start Guide

### 1. Start the API Server
```bash
# From project directory
python -m uvicorn app.main:app --reload --port 8000

# Or using Docker
docker run -d -p 8000:8000 --name scraper-api scraping-automation:v2.0
```

### 2. Test System Health
```bash
curl "http://localhost:8000/api/v1/system/health"
curl "http://localhost:8000/api/v1/system/chrome-status"
```

### 3. Scrape All Categories and Save to Google Sheets
```bash
curl -X POST "http://localhost:8000/api/v1/bali-exception/full-workflow"
```

### 4. Access Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Production Deployment

The new structure supports:
- ✅ Single container deployment
- ✅ Multi-competitor operations with separate Google Sheets
- ✅ Comprehensive monitoring and health checks
- ✅ Modular scalability for adding new competitors
- ✅ Performance tracking and error reporting
- ✅ Docker-ready with Chrome auto-detection

## Port Configuration
- **Development**: `8000` (default)
- **Production**: Update port in docker run command as needed
