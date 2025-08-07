from .base_scraper import BaseScraper
from .extractors.bali_for_sale_extractor import BaliExceptionForSaleExtractor
from .extractors.bali_for_rent_extractor import BaliExceptionForRentExtractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import time
import re

class BaliExceptionScraper(BaseScraper):
    """Multi-category scraper for Bali Exception properties"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize extractors for different property types
        self.extractors = {
            'for-sale': BaliExceptionForSaleExtractor(),
            'for-rent': BaliExceptionForRentExtractor()
        }
    
    def scrape_all_urls(self, categories: List[str] = None) -> Dict[str, List[str]]:
        """Scrape URLs for specified categories"""
        if categories is None:
            categories = ['for-sale', 'for-rent']  # Default to both
        
        results = {}
        
        for category in categories:
            if category not in self.extractors:
                self.logger.warning(f"Unknown category: {category}")
                continue
                
            self.logger.info(f"=== SCRAPING CATEGORY: {category.upper()} ===")
            extractor = self.extractors[category]
            
            try:
                # Navigate to category page
                full_url = f"{extractor.get_base_url()}{extractor.get_endpoint()}"
                self.driver.get(full_url)
                self.logger.info(f"Loaded {category} page: {full_url}")
                
                time.sleep(3)
                all_links = []
                current_page = 1
                
                while True:
                    self.logger.info(f"Scraping {category} page {current_page}...")
                    
                    try:
                        # Wait for elements specific to this category
                        if category == 'for-sale':
                            selector = "h2.brxe-gzgohv.brxe-heading.propertyCard__title a"
                        else:  # for-rent
                            selector = "div.brxe-tdjmvf a"
                            
                        self.wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        
                        # Parse HTML and extract URLs
                        soup = BeautifulSoup(self.driver.page_source, "html.parser")
                        page_links = extractor.extract_urls_from_page(soup)
                        
                        if not page_links:
                            self.logger.info(f"No links found on {category} page {current_page}")
                            break
                        
                        # Add new links, avoiding duplicates
                        new_links = [link for link in page_links if link not in all_links]
                        all_links.extend(new_links)
                        
                        self.logger.info(f"Found {len(new_links)} new links on {category} page {current_page}")
                        self.logger.info(f"Total {category} links so far: {len(all_links)}")
                        
                        # Try to navigate to next page
                        if not extractor.navigate_to_next_page(self.driver, current_page):
                            break
                        
                        current_page += 1
                        time.sleep(3)
                        
                    except TimeoutException:
                        self.logger.warning(f"Timeout waiting for {category} elements on page {current_page}")
                        break
                    except Exception as e:
                        self.logger.error(f"Unexpected error on {category} page {current_page}: {e}")
                        break
                
                results[category] = list(set(all_links))  # Remove duplicates
                self.logger.info(f"=== COMPLETED {category.upper()}: {len(results[category])} total URLs ===")
                
            except Exception as e:
                self.logger.error(f"Error accessing {category} main page: {e}")
                results[category] = []
        
        return results
    
    def scrape_property_details(self, urls: List[str], category: str = 'for-sale') -> List[Dict[str, Any]]:
        """Scrape detailed property information using category-specific extractor"""
        if category not in self.extractors:
            self.logger.error(f"Unknown category: {category}")
            return []
        
        extractor = self.extractors[category]
        results = []
        
        self.logger.info(f"Starting detailed scraping for {len(urls)} {category} properties...")
        
        for i, url in enumerate(urls):
            try:
                self.logger.info(f"Processing {category} property {i+1}/{len(urls)}: {url}")
                
                # Use extractor to get property details
                property_data = extractor.extract_property_details(self.driver, url)
                
                if property_data:
                    results.append(property_data)
                    self.logger.info(f"Successfully scraped {category} property: {property_data.get('title', 'No title')}")
                else:
                    self.logger.warning(f"No data extracted for {category} URL: {url}")
                
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error scraping {category} property {url}: {e}")
                continue
        
        self.logger.info(f"Completed detailed scraping for {category}: {len(results)} properties")
        return results