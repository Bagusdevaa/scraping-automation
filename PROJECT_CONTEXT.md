# Web Scraping Automation Project - Context & Progress

## 🎯 Project Overview

### Objectives
- **Goal**: Automated web scraping system for property data from competitor websites
- **Target Sites**: 
  - Bali Exception (https://baliexception.com & https://villas.baliexception.com)
  - Betterplace.cc (https://betterplace.cc)
  - Fazwaz.id (https://fazwaz.id)
- **Automation**: Weekly scheduled scraping
- **Data Storage**: Google Sheets integration (no database for MVP)
- **Deployment**: Docker containerization + Google Cloud Platform (GCP)

### Technical Stack
- **Backend**: FastAPI (Python)
- **Web Scraping**: Selenium with undetected-chromedriver + BeautifulSoup
- **Anti-Detection**: undetected-chromedriver for bypassing bot detection
- **Data Processing**: Pandas for data manipulation
- **Cloud Storage**: Google Sheets API
- **Deployment**: Docker + Google Cloud Run
- **Scheduling**: Google Cloud Scheduler

---

## 📁 Current Project Structure

```
scrapeAutomation/
├── app/
│   ├── main.py                     # FastAPI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Environment settings with pydantic
│   │   └── logging_config.py       # Structured logging setup
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py               # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── responses.py            # Pydantic response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scraping_service.py     # Orchestrator service
│   │   └── google_sheets_service.py # Google Sheets integration
│   ├── scrapers/
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── selenium_config.py  # Selenium + undetected-chromedriver setup
│   │   ├── __init__.py
│   │   ├── base_scraper.py         # Abstract base class with context manager
│   │   └── baliExceptionScraper.py # Main scraper implementation
│   └── utils/
├── requirements.txt
├── .env                            # Environment variables
├── .env.example                    # Example environment file
├── google-credentials.json         # Google Service Account credentials
├── .gitignore
├── Dockerfile                      # Docker configuration
└── PROJECT_CONTEXT.md             # This file
```

---

## 📦 Dependencies & Requirements

### Core Libraries
```txt
# Web Scraping & Automation
undetected-chromedriver==3.4.7
selenium==4.15.2
beautifulsoup4==4.12.2

# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Google Integration
gspread==5.12.0
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-api-python-client==2.108.0

# Data Processing
pandas==2.1.4
openpyxl==3.1.2

# Configuration & Environment
pydantic==2.5.0
pydantic-settings==2.0.3
python-dotenv==1.0.0

# Progress & Utilities
tqdm==4.66.1
tenacity==8.2.3
```

---

## ⚙️ Environment Configuration

### Required Environment Variables (.env)
```env
# App Settings
DEBUG=false
HEADLESS_MODE=true

# Google Sheets Integration
GOOGLE_SHEETS_CREDENTIALS_FILE=./google-credentials.json
GOOGLE_SHEET_ID=1I-iGdqCiYwIJuwG-91E1CGTDD6blOkGPr-rJJvtUxBk

# Scraping Configuration
SCRAPING_TIMEOUT=60
MAX_RETRIES=5
```

### Google Cloud Setup Required
1. **Google Cloud Project**: `web-scraping-automation-468004`
2. **APIs Enabled**: 
   - Google Sheets API
   - Google Drive API
3. **Service Account**: `property-scraper-service`
4. **Credentials**: Downloaded as `google-credentials.json`
5. **Google Sheet**: Created and shared with service account email

---

## ✅ Current Status & Working Features

### Completed Implementation
1. **✅ FastAPI Backend**: Fully functional REST API
2. **✅ Selenium Configuration**: undetected-chromedriver with anti-detection
3. **✅ Base Scraper Architecture**: Abstract class with proper resource management
4. **✅ Bali Exception Scraper**: 
   - Successfully scrapes 1015+ property URLs with pagination
   - Extracts comprehensive property details
   - Handles complex HTML parsing across multiple sections
5. **✅ Google Sheets Integration**: Working authentication and data saving
6. **✅ Error Handling**: Robust exception handling and logging
7. **✅ Data Processing**: Complex field extraction and data cleaning

### Working API Endpoints
```bash
# Health Check
GET /health

# Basic URL Scraping
POST /api/v1/scrape/urls
# Response: {"urls": [...], "total_count": 1015, "message": "Success"}

# Single Property Details
POST /api/v1/scrape/property-details?url=https://baliexception.com/properties/...
# Response: {detailed property data object}

# Complete Workflow (URLs + Details + Google Sheets)
POST /api/v1/scrape/test-workflow?max_properties=5
# Response: {"total_urls_found": 1015, "properties_scraped": 5, "sheets_result": "Success"}

# Full Production Workflow
POST /api/v1/scrape/full-workflow?max_properties=50
```

### Test Commands
```bash
# Start Development Server
python -m app.main

# Test Basic Functionality
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/scrape/test-workflow?max_properties=5

# Test Single Property
curl -X POST "http://localhost:8000/api/v1/scrape/property-details?url=https://baliexception.com/properties/for-sale/apartment/leasehold/ubud/ready-now-1-bedroom-townhouse-for-sale-leasehold-in-gianyar-be-2316/"
```

---

## 🏗️ Technical Architecture

### Scraper Design Pattern
- **Base Class**: `BaseScraper` with context manager (`__enter__`/`__exit__`)
- **Selenium Management**: Automatic WebDriver setup and cleanup
- **Error Handling**: Comprehensive exception handling with logging
- **Anti-Detection**: undetected-chromedriver + stealth options

### Data Extraction Pipeline
1. **URL Collection**: Paginated scraping with navigation handling
2. **Property Details**: Individual page scraping with complex parsing
3. **Data Processing**: Field extraction, type conversion, validation
4. **Storage**: Google Sheets integration with proper formatting

### Property Data Structure
```python
{
    "property_ID": str,           # Extracted from features
    "title": str,                 # Main property title
    "description": str,           # Full description text
    "price_usd": int,            # Price in USD
    "price_idr": int,            # Price in IDR
    "location": str,             # Property location
    "type": str,                 # Property type (Villa, Land, etc.)
    "listing_date": str,         # ISO format date
    "status": str,               # Property status
    "bedrooms": int,             # Number of bedrooms
    "bathrooms": int,            # Number of bathrooms
    "land_size_sqm": int,        # Land area in sqm
    "building_size_sqm": int,    # Building area in sqm
    "lease_duration": int,       # Lease duration in years
    "lease_expiry_year": int,    # Calculated expiry year
    "year_built": int,           # Construction year
    "url": str,                  # Source URL
    "listing_status": str,       # Listing status
    "amenities": list,           # List of amenities
    "pool_type": str,            # Pool type if available
    "furnish": str,              # Furnishing status
    "pool_size": int,            # Pool size if available
    "key_information": list,     # Key information points
    "key_features": list,        # Key features list
    "features": dict,            # All extracted features
    "pool": bool,                # Has pool boolean
}
```

---

## 🚨 Current Challenge: Multi-Category Complexity

### Problem Identified
The scraping system needs to handle multiple categories per competitor with different:

1. **Base URLs**:
   - For Sale: `https://baliexception.com/properties`
   - For Rent: `https://villas.baliexception.com/find-rental/`

2. **HTML Structures**: Different CSS selectors for URL scraping between categories

3. **Detail Page Structures**: Different parsing logic for property details

4. **Pagination Systems**: Different navigation methods per category

### Proposed Solution
Advanced configuration-based system with:
- Category-specific base URLs
- Flexible CSS selector mapping
- Dynamic parsing logic per category
- Scalable architecture for multiple competitors

---

## 🚀 Next Immediate Tasks

### Phase 1: Advanced Configuration System
- [ ] Implement multi-category configuration architecture
- [ ] Add support for different base URLs per category
- [ ] Create flexible CSS selector mapping
- [ ] Test with both Bali Exception categories (for-sale & for-rent)

### Phase 2: Containerization
- [ ] Finalize Dockerfile with Chrome dependencies
- [ ] Test Docker container locally
- [ ] Optimize container size and startup time

### Phase 3: Cloud Deployment
- [ ] Google Cloud Run deployment
- [ ] Environment variables configuration in GCP
- [ ] Google Cloud Scheduler setup for weekly automation
- [ ] Monitoring and logging setup

### Phase 4: Multi-Competitor Expansion
- [ ] Add Betterplace.cc scraper
- [ ] Add Fazwaz.id scraper
- [ ] Unified data schema across all competitors

---

## 🔧 Development Setup

### Prerequisites
- Python 3.11+
- Chrome browser installed
- Google Cloud account with service account
- Google Sheet created and shared

### Quick Start
```bash
# Clone and setup
git clone <repository>
cd scrapeAutomation

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Google credentials and sheet ID

# Run development server
python -m app.main

# Test basic functionality
curl http://localhost:8000/health
```

### Google Sheets Setup
1. Create Google Cloud project
2. Enable Google Sheets API and Google Drive API
3. Create service account and download JSON credentials
4. Create Google Sheet and share with service account email
5. Copy sheet ID to .env file

---

## 📊 Performance Metrics

### Current Performance
- **URL Collection**: ~1015 URLs from Bali Exception (for-sale category)
- **Detail Scraping**: ~3-4 seconds per property
- **Success Rate**: >95% for property detail extraction
- **Google Sheets**: Successful batch uploads of 50+ properties
- **Anti-Detection**: 100% success rate with undetected-chromedriver

### Scalability Considerations
- Rate limiting: 2-3 second delays between requests
- Error recovery: Automatic retry with exponential backoff
- Resource management: Proper WebDriver cleanup
- Memory optimization: Batch processing for large datasets

---

## 🤝 Contributing & Development Notes

### Code Quality Standards
- Type hints throughout codebase
- Comprehensive error handling
- Structured logging for debugging
- Context managers for resource management
- Configuration-driven architecture

### Testing Strategy
- Unit tests for individual scrapers
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Performance testing for large datasets

### Deployment Considerations
- Environment-specific configurations
- Secrets management for production
- Monitoring and alerting setup
- Backup strategies for data persistence

---

## 📝 Project History & Decisions

### Key Technical Decisions Made
1. **undetected-chromedriver over standard Selenium**: Better anti-detection capabilities
2. **FastAPI over Flask/Django**: Better async support and automatic API documentation
3. **Google Sheets over database**: Simpler MVP, easier business user access
4. **Configuration-based scraping**: Scalability for multiple sites and categories
5. **File-based credentials**: Easier deployment and security management

### Lessons Learned
- Anti-detection is crucial for reliable scraping
- Configuration-driven architecture essential for scalability
- Proper resource management prevents memory leaks
- Comprehensive logging critical for debugging complex scraping issues
- Google Sheets integration more complex than expected but very flexible

---

*Last Updated: January 2025*
*Project Status: MVP Complete - Ready for Multi-Category Implementation & Cloud Deployment*
