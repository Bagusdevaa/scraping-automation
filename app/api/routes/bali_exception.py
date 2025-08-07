"""
Bali Exception specific API routes
"""

from fastapi import APIRouter, HTTPException, Query
from app.scrapers.baliExceptionScraper import BaliExceptionScraper
from app.services.google_sheets_service import GoogleSheetsService
import logging
from typing import List

router = APIRouter(prefix="/bali-exception", tags=["Bali Exception"])
logger = logging.getLogger(__name__)

@router.get("/info")
async def get_competitor_info():
    """Get Bali Exception scraper information"""
    return {
        "competitor": "Bali Exception",
        "base_urls": {
            "for-sale": "https://baliexception.com",
            "for-rent": "https://villas.baliexception.com"
        },
        "supported_categories": ["for-sale", "for-rent"],
        "features": [
            "Multi-category scraping",
            "Scroll-based lazy loading",
            "Retry mechanisms",
            "Error tracking"
        ]
    }

@router.post("/urls")
async def scrape_bali_exception_urls(
    categories: List[str] = Query(default=["for-sale", "for-rent"], description="Categories to scrape")
):
    """Scrape URLs from Bali Exception"""
    try:
        # Validate categories
        valid_categories = ["for-sale", "for-rent"]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}"
            )
        
        logger.info(f"Starting Bali Exception URL scraping for categories: {categories}")
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            urls_by_category = scraper.scrape_all_urls(categories)
            
        total_count = sum(len(urls) for urls in urls_by_category.values())
        
        return {
            "competitor": "bali-exception",
            "urls": urls_by_category,
            "total_count": total_count,
            "categories": list(urls_by_category.keys()),
            "category_counts": {category: len(urls) for category, urls in urls_by_category.items()},
            "message": f"Successfully scraped {total_count} URLs from Bali Exception"
        }
        
    except Exception as e:
        logger.error(f"Bali Exception URL scraping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape")
async def scrape_bali_exception_properties(
    categories: List[str] = Query(default=["for-sale"], description="Categories to scrape"),
    max_properties: int = 20,
    save_to_sheets: bool = False,
    unlimited: bool = Query(default=False, description="Scrape ALL properties (ignores max_properties)")
):
    """Scrape property details from Bali Exception"""
    try:
        # Validate categories
        valid_categories = ["for-sale", "for-rent"]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]
        if invalid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid categories: {invalid_categories}. Valid options: {valid_categories}"
            )
        
        logger.info(f"Starting Bali Exception property scraping: {categories}, max: {max_properties}, unlimited: {unlimited}")
        
        # Initialize services
        sheets_service = GoogleSheetsService() if save_to_sheets else None
        
        with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
            # Get URLs
            urls_dict = scraper.scrape_all_urls(categories)
            
            # Flatten URLs with category tracking
            all_urls_with_category = []
            for category, urls in urls_dict.items():
                for url in urls:
                    all_urls_with_category.append((url, category))
            
            # Determine how many properties to scrape
            if unlimited:
                properties_to_scrape = len(all_urls_with_category)
                logger.info(f"UNLIMITED mode: Will scrape ALL {properties_to_scrape} properties")
            else:
                properties_to_scrape = min(len(all_urls_with_category), max_properties)
                logger.info(f"LIMITED mode: Will scrape {properties_to_scrape} out of {len(all_urls_with_category)} properties")
            
            # Scrape details
            all_properties = []
            for i, (url, category) in enumerate(all_urls_with_category[:properties_to_scrape]):
                logger.info(f"Scraping {category} property {i+1}/{properties_to_scrape}")
                
                details_list = scraper.scrape_property_details([url], category)
                if details_list:
                    all_properties.extend(details_list)
                
                # Progress logging for unlimited mode
                if unlimited and (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i+1}/{properties_to_scrape} properties scraped ({((i+1)/properties_to_scrape)*100:.1f}%)")
            
            # Save to Google Sheets if requested
            sheets_result = None
            if save_to_sheets and sheets_service and all_properties:
                try:
                    sheet_name = "Bali_Exception"
                    sheets_result = sheets_service.save_properties(all_properties, sheet_name)
                    sheets_result = {
                        "sheet_name": sheet_name,
                        "status": "success", 
                        "message": sheets_result,
                        "properties_saved": len(all_properties)
                    }
                except Exception as e:
                    sheets_result = {
                        "sheet_name": "Bali_Exception",
                        "status": "error",
                        "message": str(e),
                        "properties_saved": 0
                    }
            
            # Get scraping summary
            summary = scraper.get_scraping_summary()
        
        response = {
            "competitor": "bali-exception",
            "categories_processed": categories,
            "total_urls_found": len(all_urls_with_category),
            "properties_scraped": len(all_properties),
            "scraping_mode": "unlimited" if unlimited else "limited",
            "properties": all_properties,
            "performance": {
                "success_rate": f"{summary['success_rate']:.1f}%",
                "total_errors": summary["error_count"],
                "scraping_time": summary.get("total_time", "N/A")
            }
        }
        
        if sheets_result:
            response["google_sheets"] = sheets_result
        
        return response
        
    except Exception as e:
        logger.error(f"Bali Exception property scraping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/full-workflow")
async def bali_exception_full_workflow(
    categories: List[str] = Query(default=["for-sale"], description="Categories to scrape"),
    max_properties: int = 50,
    save_to_sheets: bool = True,
    unlimited: bool = Query(default=False, description="Scrape ALL properties (ignores max_properties)")
):
    """Complete Bali Exception workflow with Google Sheets export"""
    return await scrape_bali_exception_properties(
        categories=categories,
        max_properties=max_properties,
        save_to_sheets=save_to_sheets,
        unlimited=unlimited
    )
