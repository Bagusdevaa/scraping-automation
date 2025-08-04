from fastapi import APIRouter, HTTPException
from app.models.responses import PropertyResponse
from app.scrapers.baliExceptionScraper import BaliExceptionScraper
from app.services.google_sheets_service import GoogleSheetsService
import logging
from pydantic import BaseModel
import time
from app.core.config import settings

from typing import List

class PropertyDetailRequest(BaseModel):
    url: str

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "timestamp": "now"}

@router.post("/scrape/urls", response_model=PropertyResponse)
async def scrape_urls_only():
    """Scrape URLs only (tanpa property details dulu)"""
    try:
        logger.info("Starting URL scraping...")
        
        # Initialize scraper
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            urls = scraper.scrape_all_urls()
            
        return PropertyResponse(
            urls=urls,
            total_count=len(urls),
            message=f"Successfully scraped {len(urls)} URLs"
        )
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/scrape/property-details")
async def scrape_single_property(url: str):
    """Test scrape single property details"""
    try:
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            details = scraper.scrape_property_details(url)
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/bulk-details")
async def scrape_bulk_properties(urls: List[str], max_properties: int = 10):
    """Scrape details for multiple properties (with limit)"""
    try:
        results = []
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            for i, url in enumerate(urls[:max_properties]):
                logger.info(f"Scraping property {i+1}/{min(len(urls), max_properties)}: {url}")
                details = scraper.scrape_property_details(url)
                results.append(details)
                time.sleep(3)
        
        return {
            "total_scraped": len(results),
            "total_requested": len(urls),
            "properties": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/full-workflow")
async def scrape_full_workflow(max_properties: int = 50):
    """Complete workflow: scrape URLs then details"""
    try:
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            # Step 1: Get all URLs
            logger.info("Step 1: Collecting property URLs...")
            urls = scraper.scrape_all_urls()
            
            # Step 2: Scrape details (limited)
            logger.info(f"Step 2: Scraping details for {min(len(urls), max_properties)} properties...")
            properties = []
            for i, url in enumerate(urls[:max_properties]):
                details = scraper.scrape_property_details(url)
                properties.append(details)
                logger.info(f"Completed {i+1}/{min(len(urls), max_properties)}")
                time.sleep(2)
        
        return {
            "total_urls_found": len(urls),
            "properties_scraped": len(properties),
            "properties": properties
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/scrape/full-workflow-with-sheets")
async def scrape_and_save_to_sheets(max_properties: int = 50):
    """Complete workflow: scrape URLs, details, and save to Google Sheets"""
    try:
        # Initialize services
        sheets_service = GoogleSheetsService()
        
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            # Step 1: Get URLs
            logger.info("Step 1: Collecting property URLs...")
            urls = scraper.scrape_all_urls()
            
            # Step 2: Scrape details
            logger.info(f"Step 2: Scraping details for {min(len(urls), max_properties)} properties...")
            properties = []
            for i, url in enumerate(urls[:max_properties]):
                details = scraper.scrape_property_details(url)
                properties.append(details)
                logger.info(f"Completed {i+1}/{min(len(urls), max_properties)}")
                time.sleep(2)
            
            # Step 3: Save to Google Sheets
            logger.info("Step 3: Saving to Google Sheets...")
            sheets_result = sheets_service.save_properties(properties)
        
        return {
            "total_urls_found": len(urls),
            "properties_scraped": len(properties),
            "sheets_result": sheets_result,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/scrape/test-workflow")
async def scrape_test_workflow(max_properties: int = 5, max_pages: int = 2):
    """Test workflow dengan limited URLs dan pages"""
    try:
        sheets_service = GoogleSheetsService()
        
        with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
            # Modified: scrape only first few pages
            logger.info(f"Step 1: Collecting URLs from first {max_pages} pages...")
            urls = scraper.scrape_limited_urls(max_pages=max_pages)  # NEW METHOD
            
            logger.info(f"Step 2: Scraping details for {min(len(urls), max_properties)} properties...")
            properties = []
            for i, url in enumerate(urls[:max_properties]):
                details = scraper.scrape_property_details(url)
                properties.append(details)
                logger.info(f"Completed {i+1}/{min(len(urls), max_properties)}")
                time.sleep(2)
            
            # Step 3: Save to Google Sheets
            logger.info("Step 3: Saving to Google Sheets...")
            sheets_result = sheets_service.save_properties(properties)
        
        return {
            "total_urls_found": len(urls),
            "properties_scraped": len(properties),
            "sheets_result": sheets_result,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/test-config")
async def test_config():
    """Test configuration values"""
    return {
        "sheet_id": bool(settings.GOOGLE_SHEET_ID),
        "credentials_json": bool(settings.GOOGLE_SHEETS_CREDENTIALS_JSON),
        "credentials_file": bool(settings.GOOGLE_SHEETS_CREDENTIALS_FILE),
        "sheet_id_value": settings.GOOGLE_SHEET_ID[:10] + "..." if settings.GOOGLE_SHEET_ID else None,
        "credentials_file_value": settings.GOOGLE_SHEETS_CREDENTIALS_FILE
    }