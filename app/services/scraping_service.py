from app.scrapers.baliExceptionScraper import BaliExceptionScraper
import logging

logger = logging.getLogger(__name__)

class ScrapingService:
    def __init__(self):
        pass
    
    def scrape_urls_only(self) -> dict:
        """Scrape URLs only untuk testing"""
        try:
            logger.info("Starting Bali Exception URL scraping...")
            
            with BaliExceptionScraper(headless=False, stealth_mode=True) as scraper:
                urls = scraper.scrape_all_urls()
                
            return {
                "urls": urls,
                "total_count": len(urls),
                "status": "success"
            }
                
        except Exception as e:
            logger.error(f"URL scraping failed: {e}")
            raise