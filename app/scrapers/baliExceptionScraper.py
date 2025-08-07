from .base_scraper import BaseScraper
from .extractors.bali_for_sale_extractor import BaliExceptionForSaleExtractor
from .extractors.bali_for_rent_extractor import BaliExceptionForRentExtractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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
        # Initialize error tracking
        self.scraping_errors = []
        self.scraping_stats = {
            'urls_scraped': 0,
            'urls_failed': 0,
            'properties_extracted': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _scroll_to_trigger_loading(self, scroll_count=3, pause_time=2):
        """Scroll down to trigger lazy loading for for-rent properties"""
        self.logger.info(f"Scrolling {scroll_count} times to trigger content loading...")
        
        for i in range(scroll_count):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            self.logger.info(f"Scroll {i+1}/{scroll_count} completed")
        
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        self.logger.info("Scrolled back to top")
    
    def _add_error(self, error_type: str, url: str = None, category: str = None, 
                   error_message: str = None, exception: Exception = None):
        """Centralized error tracking"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'url': url,
            'category': category,
            'error_message': error_message or (str(exception) if exception else 'Unknown error'),
            'exception_type': type(exception).__name__ if exception else None
        }
        
        self.scraping_errors.append(error_entry)
        self.scraping_stats['urls_failed'] += 1
        
        # Log error
        log_msg = f"[{error_type}] {error_message or str(exception)}"
        if url:
            log_msg += f" | URL: {url}"
        if category:
            log_msg += f" | Category: {category}"
        
        self.logger.error(log_msg)
    
    def _update_stats(self, action: str, category: str = None):
        """Update scraping statistics"""
        if action == 'start':
            self.scraping_stats['start_time'] = datetime.now().isoformat()
        elif action == 'end':
            self.scraping_stats['end_time'] = datetime.now().isoformat()
        elif action == 'url_scraped':
            self.scraping_stats['urls_scraped'] += 1
        elif action == 'property_extracted':
            self.scraping_stats['properties_extracted'] += 1
    
    def get_scraping_summary(self) -> Dict[str, Any]:
        """Get comprehensive scraping summary"""
        total_time = None
        if self.scraping_stats['start_time'] and self.scraping_stats['end_time']:
            start = datetime.fromisoformat(self.scraping_stats['start_time'])
            end = datetime.fromisoformat(self.scraping_stats['end_time'])
            total_time = str(end - start)
        
        return {
            'statistics': self.scraping_stats.copy(),
            'total_time': total_time,
            'error_count': len(self.scraping_errors),
            'success_rate': (
                self.scraping_stats['properties_extracted'] / 
                max(self.scraping_stats['urls_scraped'], 1) * 100
            ),
            'errors_by_type': self._group_errors_by_type(),
            'recent_errors': self.scraping_errors[-5:] if self.scraping_errors else []
        }
    
    def _group_errors_by_type(self) -> Dict[str, int]:
        """Group errors by type for analysis"""
        error_counts = {}
        for error in self.scraping_errors:
            error_type = error.get('error_type', 'unknown')
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts
    
    def scrape_all_urls(self, categories: List[str] = None) -> Dict[str, List[str]]:
        """Scrape URLs for specified categories"""
        if categories is None:
            categories = ['for-sale', 'for-rent']  # Default to both
        
        results = {}
        
        for category in categories:
            if category not in self.extractors:
                self._add_error('invalid_category', category=category, 
                              error_message=f"Unknown category: {category}")
                continue
                
            self.logger.info(f"=== SCRAPING CATEGORY: {category.upper()} ===")
            extractor = self.extractors[category]
            
            try:
                # Navigate to category page
                full_url = f"{extractor.get_base_url()}{extractor.get_endpoint()}"
                
                try:
                    self.driver.get(full_url)
                    self.logger.info(f"Loaded {category} page: {full_url}")
                    time.sleep(3)
                except Exception as e:
                    self._add_error('page_load_failed', url=full_url, category=category, exception=e)
                    results[category] = []
                    continue
                
                # For-rent category needs scrolling to trigger lazy loading
                if category == 'for-rent':
                    try:
                        self.logger.info("For-rent detected: performing scroll to trigger lazy loading...")
                        self._scroll_to_trigger_loading(3)  # Scroll 3 times to load content
                    except Exception as e:
                        self.logger.warning(f"Scroll failed, continuing anyway: {e}")
                
                all_links = []
                current_page = 1
                consecutive_failures = 0
                max_consecutive_failures = 3
                
                while consecutive_failures < max_consecutive_failures:
                    self.logger.info(f"Scraping {category} page {current_page}...")
                    
                    try:
                        # Wait for elements specific to this category with longer timeout
                        if category == 'for-sale':
                            selector = "h2.brxe-gzgohv.brxe-heading.propertyCard__title a"
                            timeout = 15
                        else:  # for-rent
                            selector = "div.brxe-tdjmvf a"
                            timeout = 30  # Longer timeout for for-rent
                            
                        wait = WebDriverWait(self.driver, timeout)
                        wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        
                        # Additional scroll for for-rent on each page
                        if category == 'for-rent':
                            try:
                                self._scroll_to_trigger_loading(2)
                            except Exception as e:
                                self.logger.warning(f"Page scroll failed: {e}")
                        
                        # Parse HTML and extract URLs
                        try:
                            soup = BeautifulSoup(self.driver.page_source, "html.parser")
                            page_links = extractor.extract_urls_from_page(soup)
                        except Exception as e:
                            self._add_error('url_extraction_failed', 
                                          url=f"{full_url}?page={current_page}", 
                                          category=category, exception=e)
                            consecutive_failures += 1
                            current_page += 1
                            continue
                        
                        if not page_links:
                            self.logger.info(f"No links found on {category} page {current_page}")
                            consecutive_failures += 1
                            if consecutive_failures >= 2:  # Stop after 2 empty pages
                                break
                        else:
                            consecutive_failures = 0  # Reset counter on success
                        
                        # Add new links, avoiding duplicates
                        new_links = [link for link in page_links if link not in all_links]
                        all_links.extend(new_links)
                        
                        self.logger.info(f"Found {len(new_links)} new links on {category} page {current_page}")
                        self.logger.info(f"Total {category} links so far: {len(all_links)}")
                        
                        # Try to navigate to next page
                        try:
                            if not extractor.navigate_to_next_page(self.driver, current_page):
                                self.logger.info(f"No more pages for {category}")
                                break
                        except Exception as e:
                            self.logger.warning(f"Navigation to next page failed: {e}")
                            break
                        
                        current_page += 1
                        time.sleep(3)
                        
                    except TimeoutException as e:
                        self._add_error('timeout', 
                                      url=f"{full_url}?page={current_page}", 
                                      category=category, exception=e)
                        consecutive_failures += 1
                        current_page += 1
                        continue
                        
                    except Exception as e:
                        self._add_error('page_scraping_failed', 
                                      url=f"{full_url}?page={current_page}", 
                                      category=category, exception=e)
                        consecutive_failures += 1
                        current_page += 1
                        continue
                
                # Clean up and deduplicate results
                results[category] = list(set(all_links))  # Remove duplicates
                self.logger.info(f"=== COMPLETED {category.upper()}: {len(results[category])} total URLs ===")
                
            except Exception as e:
                self._add_error('category_scraping_failed', category=category, exception=e)
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
        self._update_stats('start')
        
        for i, url in enumerate(urls):
            self._update_stats('url_scraped')
            
            try:
                self.logger.info(f"Processing {category} property {i+1}/{len(urls)}: {url}")
                
                # Navigate to property page with retries
                max_retries = 3
                property_data = None
                
                for retry in range(max_retries):
                    try:
                        # Navigate to property page
                        self.driver.get(url)
                        self.logger.info(f"Loaded property page (attempt {retry+1})")
                        
                        # Progressive wait strategy
                        base_wait_time = 3 + (retry * 2)  # 3, 5, 7 seconds
                        self.logger.info(f"Waiting {base_wait_time}s for page to fully load...")
                        time.sleep(base_wait_time)
                        
                        # Try to wait for key elements to load
                        try:
                            wait = WebDriverWait(self.driver, 15)
                            if category == 'for-sale':
                                # Wait for title or price elements
                                wait.until(EC.any_of(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1")),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, ".property-title")),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='title']"))
                                ))
                            else:  # for-rent
                                # Wait for rental-specific elements
                                wait.until(EC.any_of(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1")),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, ".villa-title")),
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='title']"))
                                ))
                        except TimeoutException:
                            self.logger.warning(f"Timeout waiting for elements on attempt {retry+1}")
                        
                        # Use extractor to get property details
                        property_data = extractor.extract_property_details(self.driver, url)
                        
                        if property_data and property_data.get('title'):
                            # Success - data extracted
                            break
                        else:
                            self.logger.warning(f"No/incomplete data on attempt {retry+1}")
                            
                    except Exception as e:
                        self.logger.warning(f"Attempt {retry+1} failed: {e}")
                        
                    # Wait before retry
                    if retry < max_retries - 1:
                        wait_time = 2 * (retry + 1)
                        self.logger.info(f"Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                
                if property_data and property_data.get('title'):
                    results.append(property_data)
                    self._update_stats('property_extracted')
                    self.logger.info(f"[SUCCESS] Successfully scraped {category} property: {property_data.get('title', 'No title')}")
                else:
                    self._add_error('extraction_failed', url=url, category=category,
                                  error_message='No data extracted after retries')
                
                # Rate limiting between properties
                time.sleep(3)  # Longer pause between properties
                
            except Exception as e:
                self._add_error('property_scraping_failed', url=url, category=category, exception=e)
                continue
        
        self._update_stats('end')
        self.logger.info(f"Completed detailed scraping for {category}: {len(results)} properties")
        return results
    
    def scrape_all_properties(self, category: str = None, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Complete scraping workflow with category support
        
        Args:
            category: Specific category to scrape ('for-sale' or 'for-rent'), or None for both
            max_pages: Maximum pages to scrape per category (None for all pages)
        """
        if category:
            # Single category
            if category not in self.extractors:
                raise ValueError(f"Unknown category: {category}. Available: {list(self.extractors.keys())}")
            
            self.logger.info(f"=== SCRAPING SINGLE CATEGORY: {category.upper()} ===")
            urls_dict = self.scrape_all_urls([category])
            urls = urls_dict.get(category, [])
            
            # Limit URLs if max_pages specified (rough estimate: ~20 properties per page)
            if max_pages and len(urls) > max_pages * 20:
                urls = urls[:max_pages * 20]
                self.logger.info(f"Limited to {len(urls)} URLs for max_pages={max_pages}")
            
            return self.scrape_property_details_bulk(urls, category)
        else:
            # All categories
            self.logger.info("=== SCRAPING ALL CATEGORIES ===")
            all_properties = []
            
            for cat in self.extractors.keys():
                self.logger.info(f"Processing category: {cat}")
                cat_properties = self.scrape_all_properties(category=cat, max_pages=max_pages)
                all_properties.extend(cat_properties)
            
            return all_properties

    def print_scraping_summary(self):
        """Print formatted scraping summary to console"""
        summary = self.get_scraping_summary()
        
        print("\n" + "="*50)
        print("[STATS] SCRAPING SUMMARY")
        print("="*50)
        
        print(f"⏱️  Total time: {summary.get('total_time', 'N/A')}")
        print(f"📄 URLs processed: {summary['statistics']['urls_scraped']}")
        print(f"[SUCCESS] Properties extracted: {summary['statistics']['properties_extracted']}")
        print(f"[ERROR] Failed attempts: {summary['statistics']['urls_failed']}")
        print(f"📈 Success rate: {summary['success_rate']:.1f}%")
        
        if summary['error_count'] > 0:
            print(f"\n[WARNING]  ERRORS:")
            for error_type, count in summary['errors_by_type'].items():
                print(f"   {error_type}: {count}")
        else:
            print(f"\n[SUCCESS] No errors detected!")
        
        print("="*50)
    
    def export_errors_to_file(self, filename: str = None):
        """Export errors to JSON file for analysis"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"scraping_errors_{timestamp}.json"
        
        error_report = {
            'export_timestamp': datetime.now().isoformat(),
            'total_errors': len(self.scraping_errors),
            'errors_by_type': self._group_errors_by_type(),
            'detailed_errors': self.scraping_errors,
            'statistics': self.scraping_stats
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                import json
                json.dump(error_report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📁 Error report exported to: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to export error report: {e}")
            return None