from app.scrapers.baliExceptionScraper import BaliExceptionScraper
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ScrapingService:
    def __init__(self):
        pass
    
    def scrape_urls_only(self, categories: List[str] = None) -> dict:
        """Scrape URLs only untuk testing dengan support multiple categories"""
        try:
            logger.info(f"Starting Bali Exception URL scraping for categories: {categories or ['for-sale', 'for-rent']}")
            
            with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
                urls_by_category = scraper.scrape_all_urls(categories)
                
            # Calculate total count across all categories
            total_count = sum(len(urls) for urls in urls_by_category.values())
            
            return {
                "urls": urls_by_category,
                "total_count": total_count,
                "categories": list(urls_by_category.keys()),
                "category_counts": {category: len(urls) for category, urls in urls_by_category.items()},
                "status": "success"
            }
                
        except Exception as e:
            logger.error(f"URL scraping failed: {e}")
            raise