from fastapi import APIRouter, HTTPException, Query
from app.models.responses import PropertyResponse
from app.scrapers.baliExceptionScraper import BaliExceptionScraper
from app.scrapers.utils.selenium_config import SeleniumConfig
from app.services.google_sheets_service import GoogleSheetsService
import logging
from pydantic import BaseModel
import time
from app.core.config import settings
from typing import List, Optional

class PropertyDetailRequest(BaseModel):
    url: str

class CategoryScrapeRequest(BaseModel):
    categories: Optional[List[str]] = ["for-sale", "for-rent"]

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/debug/environment")
async def debug_environment():
    """Debug environment setup untuk troubleshooting ChromeDriver issues"""
    try:
        env_info = SeleniumConfig.debug_environment()
        return {
            "status": "success",
            "environment": env_info,
            "message": "Environment debug completed - check logs for details"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to debug environment"
        }

@router.get("/debug/webdriver")
async def debug_webdriver():
    """Test WebDriver initialization untuk debugging"""
    try:
        logger.info("🧪 Testing WebDriver initialization...")
        
        # Test stealth driver creation
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Try to navigate to a simple page
            scraper.driver.get("https://httpbin.org/user-agent")
            time.sleep(2)
            
            page_title = scraper.driver.title
            current_url = scraper.driver.current_url
            user_agent = scraper.driver.execute_script("return navigator.userAgent;")
            
        return {
            "status": "success",
            "webdriver_test": {
                "initialization": "✅ Success",
                "page_title": page_title,
                "current_url": current_url,
                "user_agent": user_agent[:100] + "..." if len(user_agent) > 100 else user_agent
            },
            "message": "WebDriver test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"WebDriver test failed: {e}")
        return {
            "status": "error",
            "webdriver_test": {
                "initialization": "❌ Failed",
                "error": str(e)
            },
            "message": "WebDriver test failed - check environment debug"
        }

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "timestamp": "now"}

@router.post("/scrape/urls")
async def scrape_urls_only(
    categories: List[str] = Query(default=["for-sale", "for-rent"], description="Categories to scrape: for-sale, for-rent")
):
    """Scrape URLs only (tanpa property details dulu) dengan multiple categories"""
    try:
        logger.info(f"Starting URL scraping for categories: {categories}")
        
        # Validate categories
        valid_categories = ["for-sale", "for-rent"]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}"
            )
        
        # Initialize scraper
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            urls_by_category = scraper.scrape_all_urls(categories)
            
        # Calculate total count
        total_count = sum(len(urls) for urls in urls_by_category.values())
        
        return {
            "urls": urls_by_category,
            "total_count": total_count,
            "categories": list(urls_by_category.keys()),
            "category_counts": {category: len(urls) for category, urls in urls_by_category.items()},
            "message": f"Successfully scraped {total_count} URLs across {len(categories)} categories"
        }
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/scrape/property-details")
async def scrape_single_property(url: str, category: str = "for-sale"):
    """Test scrape single property details dengan category support"""
    try:
        if category not in ["for-sale", "for-rent"]:
            raise HTTPException(status_code=400, detail="Category must be 'for-sale' or 'for-rent'")
            
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Use category-specific extractor
            extractor = scraper.extractors[category]
            details = extractor.extract_property_details(scraper.driver, url)
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/bulk-details")
async def scrape_bulk_properties(urls: List[str], max_properties: int = 10):
    """Scrape details for multiple properties (with limit)"""
    try:
        results = []
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
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
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
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
async def scrape_and_save_to_sheets():
    """Complete workflow: scrape URLs, details, and save to Google Sheets"""
    try:
        # Initialize services
        sheets_service = GoogleSheetsService()
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Step 1: Get URLs
            logger.info("Step 1: Collecting property URLs...")
            urls = scraper.scrape_all_urls()
            
            # Step 2: Scrape details
            logger.info(f"Step 2: Scraping details for {len(urls)} properties...")
            properties = []
            for i, url in enumerate(urls):
                details = scraper.scrape_property_details(url)
                properties.append(details)
                logger.info(f"Completed {i+1}/{len(urls)} properties")
                time.sleep(3)
            
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
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
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