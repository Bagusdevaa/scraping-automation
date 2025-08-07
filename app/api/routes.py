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
async def scrape_bulk_properties(
    urls: List[str], 
    max_properties: int = 10,
    category: str = Query(default="auto", description="Category: for-sale, for-rent, or auto-detect")
):
    """Scrape details for multiple properties (with limit) and category support"""
    try:
        if category not in ["for-sale", "for-rent", "auto"]:
            raise HTTPException(status_code=400, detail="Category must be 'for-sale', 'for-rent', or 'auto'")
        
        results = []
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            for i, url in enumerate(urls[:max_properties]):
                logger.info(f"Scraping property {i+1}/{min(len(urls), max_properties)}: {url}")
                
                # Auto-detect category from URL if not specified
                if category == "auto":
                    if 'villas.baliexception.com' in url:
                        detected_category = 'for-rent'
                    else:
                        detected_category = 'for-sale'
                else:
                    detected_category = category
                
                # Use category-specific method
                details_list = scraper.scrape_property_details([url], detected_category)
                if details_list:
                    results.extend(details_list)
        
        return {
            "total_scraped": len(results),
            "total_requested": len(urls),
            "max_properties_limit": max_properties,
            "category_used": category,
            "properties": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/full-workflow")
async def scrape_full_workflow(
    max_properties: int = 50,
    categories: List[str] = Query(default=["for-sale", "for-rent"], description="Categories to scrape")
):
    """Complete workflow: scrape URLs then details with multi-category support"""
    try:
        # Validate categories
        valid_categories = ["for-sale", "for-rent"]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}"
            )
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Step 1: Get all URLs by category
            logger.info(f"Step 1: Collecting property URLs for categories: {categories}...")
            urls_dict = scraper.scrape_all_urls(categories)
            
            # Flatten URLs and track category
            all_urls_with_category = []
            for category, urls in urls_dict.items():
                for url in urls:
                    all_urls_with_category.append((url, category))
            
            total_urls = len(all_urls_with_category)
            logger.info(f"Found {total_urls} total URLs across {len(categories)} categories")
            
            # Step 2: Scrape details (limited)
            properties_to_scrape = min(total_urls, max_properties)
            logger.info(f"Step 2: Scraping details for {properties_to_scrape} properties...")
            
            all_properties = []
            for i, (url, category) in enumerate(all_urls_with_category[:max_properties]):
                logger.info(f"Scraping {category} property {i+1}/{properties_to_scrape}: {url}")
                
                details_list = scraper.scrape_property_details([url], category)
                if details_list:
                    all_properties.extend(details_list)
                
                logger.info(f"Completed {i+1}/{properties_to_scrape}")
        
        return {
            "total_urls_found": total_urls,
            "urls_by_category": {cat: len(urls) for cat, urls in urls_dict.items()},
            "properties_scraped": len(all_properties),
            "categories_processed": categories,
            "properties": all_properties
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/scrape/full-workflow-with-sheets")
async def scrape_and_save_to_sheets(
    categories: List[str] = Query(default=["for-sale", "for-rent"], description="Categories to scrape"),
    max_properties: int = 100
):
    """Complete workflow: scrape URLs, details, and save to Google Sheets with multi-category support"""
    try:
        # Validate categories
        valid_categories = ["for-sale", "for-rent"]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}"
            )
        
        # Initialize services
        sheets_service = GoogleSheetsService()
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Step 1: Get URLs by category
            logger.info(f"Step 1: Collecting property URLs for categories: {categories}...")
            urls_dict = scraper.scrape_all_urls(categories)
            
            # Flatten URLs with category tracking
            all_urls_with_category = []
            for category, urls in urls_dict.items():
                for url in urls:
                    all_urls_with_category.append((url, category))
            
            total_urls = len(all_urls_with_category)
            properties_to_scrape = min(total_urls, max_properties)
            
            logger.info(f"Found {total_urls} URLs, will scrape {properties_to_scrape} properties")
            
            # Step 2: Scrape details
            logger.info(f"Step 2: Scraping details for {properties_to_scrape} properties...")
            all_properties = []
            
            for i, (url, category) in enumerate(all_urls_with_category[:max_properties]):
                logger.info(f"Scraping {category} property {i+1}/{properties_to_scrape}")
                
                details_list = scraper.scrape_property_details([url], category)
                if details_list:
                    all_properties.extend(details_list)
            
            # Step 3: Save to Google Sheets
            logger.info("Step 3: Saving to Google Sheets...")
            sheets_result = sheets_service.save_properties(all_properties)
            
            # Get scraping summary
            summary = scraper.get_scraping_summary()
        
        return {
            "total_urls_found": total_urls,
            "urls_by_category": {cat: len(urls) for cat, urls in urls_dict.items()},
            "properties_scraped": len(all_properties),
            "categories_processed": categories,
            "sheets_result": sheets_result,
            "scraping_summary": {
                "success_rate": summary["success_rate"],
                "error_count": summary["error_count"],
                "total_time": summary.get("total_time", "N/A")
            },
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/scrape/test-workflow")
async def scrape_test_workflow(
    max_properties: int = 5, 
    max_pages: int = 2,
    categories: List[str] = Query(default=["for-sale"], description="Categories to scrape")
):
    """Test workflow dengan limited URLs dan pages"""
    try:
        # Validate categories
        valid_categories = ["for-sale", "for-rent"]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}"
            )
        
        sheets_service = GoogleSheetsService()
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Step 1: Get URLs with category support (limit by taking sample)
            logger.info(f"Step 1: Collecting URLs for categories: {categories}...")
            urls_dict = scraper.scrape_all_urls(categories)
            
            # Limit URLs per category based on max_pages estimate (rough: ~20 URLs per page)
            max_urls_per_category = max_pages * 20
            limited_urls = []
            
            for category, urls in urls_dict.items():
                category_urls = urls[:max_urls_per_category]
                limited_urls.extend(category_urls)
                logger.info(f"   {category}: {len(category_urls)} URLs (limited from {len(urls)})")
            
            logger.info(f"Step 2: Scraping details for {min(len(limited_urls), max_properties)} properties...")
            properties = []
            for i, url in enumerate(limited_urls[:max_properties]):
                # Determine category from URL
                if 'villas.baliexception.com' in url:
                    category = 'for-rent'
                else:
                    category = 'for-sale'
                    
                details_list = scraper.scrape_property_details([url], category)
                if details_list:
                    properties.extend(details_list)
                logger.info(f"Completed {i+1}/{min(len(limited_urls), max_properties)}")
            
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

@router.post("/scrape/comprehensive")
async def scrape_comprehensive_workflow(
    categories: List[str] = Query(default=["for-sale"], description="Categories to scrape"),
    max_properties: int = 20,
    save_to_sheets: bool = True,
    include_summary: bool = True
):
    """Comprehensive scraping workflow with full error tracking and performance metrics"""
    try:
        # Validate categories
        valid_categories = ["for-sale", "for-rent"]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}"
            )
        
        logger.info(f"Starting comprehensive scraping for categories: {categories}")
        
        # Initialize services
        sheets_service = GoogleSheetsService() if save_to_sheets else None
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Phase 1: URL Collection
            logger.info("Phase 1: URL Collection")
            urls_dict = scraper.scrape_all_urls(categories)
            
            # Phase 2: Property Details Extraction
            logger.info("Phase 2: Property Details Extraction")
            all_properties = []
            
            for category, urls in urls_dict.items():
                category_limit = max_properties // len(categories)
                logger.info(f"Processing {category}: {len(urls)} URLs, limiting to {category_limit}")
                
                if urls:
                    sample_urls = urls[:category_limit]
                    properties = scraper.scrape_property_details(sample_urls, category)
                    all_properties.extend(properties)
            
            # Phase 3: Google Sheets Export (if requested)
            sheets_result = None
            if save_to_sheets and sheets_service and all_properties:
                logger.info("Phase 3: Google Sheets Export")
                sheets_result = sheets_service.save_properties(all_properties)
            
            # Phase 4: Summary Generation
            summary = None
            if include_summary:
                summary = scraper.get_scraping_summary()
        
        response = {
            "status": "success",
            "categories_processed": categories,
            "url_collection": {
                "total_urls": sum(len(urls) for urls in urls_dict.values()),
                "by_category": {cat: len(urls) for cat, urls in urls_dict.items()}
            },
            "property_extraction": {
                "total_properties": len(all_properties),
                "max_limit": max_properties,
                "properties": all_properties
            }
        }
        
        if sheets_result:
            response["google_sheets"] = sheets_result
            
        if summary:
            response["performance_summary"] = {
                "success_rate": f"{summary['success_rate']:.1f}%",
                "total_errors": summary["error_count"],
                "scraping_time": summary.get("total_time", "N/A"),
                "errors_by_type": summary["errors_by_type"]
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Comprehensive scraping failed: {e}")
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