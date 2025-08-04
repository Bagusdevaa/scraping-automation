from .base_extractor import BaseExtractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import re
import logging

class BaliExceptionForRentExtractor(BaseExtractor):
    """Extractor for Bali Exception for-rent properties (villas subdomain)"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.USD_RATE = 16350  # Exchange rate from your code
    
    def get_base_url(self) -> str:
        return "https://villas.baliexception.com"
    
    def get_endpoint(self) -> str:
        return "/find-rental/"  # Note trailing slash
    
    def _scroll_to_bottom(self, driver, max_scrolls=100, scroll_pause_time=2):
        """Scroll to bottom of page - from your Jupyter notebook"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        while scroll_count < max_scrolls:
            self.logger.info(f"Scrolling down... (attempt {scroll_count + 1})")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                self.logger.info("Reached bottom of page or no more content loading.")
                break
            last_height = new_height
            scroll_count += 1
        
        self.logger.info(f"Finished scrolling after {scroll_count} attempts.")

    def extract_all_urls(self, driver) -> List[str]:
        """Complete URL extraction workflow from your Jupyter notebook"""
        try:
            driver.get(f"{self.get_base_url()}{self.get_endpoint()}")
            self.logger.info("Page loaded successfully.")
            
            # Wait for page to load
            time.sleep(3)
            
            all_links = []
            self._scroll_to_bottom(driver)
            
            # Start from page 1
            current_page = 1
            
            while True:
                self.logger.info(f"Scraping page {current_page}...")
                
                try:
                    # Wait for elements with longer timeout
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.brxe-tdjmvf a"))
                    )
                    
                    # Parse HTML
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    
                    # Extract URLs from current page
                    page_links = self.extract_urls_from_page(soup)
                    
                    if not page_links:
                        self.logger.warning(f"No links found on page {current_page}")
                        break
                    
                    # Add to total, avoiding duplicates
                    new_links = [link for link in page_links if link not in all_links]
                    all_links.extend(new_links)
                    
                    self.logger.info(f"Found {len(new_links)} new links on page {current_page}")
                    self.logger.info(f"Total links so far: {len(all_links)}")
                    
                    # Try to navigate to next page
                    if not self.navigate_to_next_page(driver, current_page):
                        break
                        
                    current_page += 1
                    time.sleep(3)  # Wait for page load
                    
                except TimeoutException:
                    self.logger.warning(f"Timeout waiting for elements on page {current_page}")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error on page {current_page}: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Error accessing main page: {e}")
            return []

        self.logger.info(f"=== SCRAPING RESULTS ===")
        self.logger.info(f"Total found: {len(all_links)} links")
        
        return all_links

    def extract_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract URLs using for-rent specific selector"""
        links = []
        cards = soup.select("div.brxe-tdjmvf a")
        
        for card in cards:
            href = card.get("href")
            if href:
                # Handle relative URLs
                if href.startswith('/'):
                    full_url = f"{self.get_base_url()}{href}"
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"{self.get_base_url()}/{href}"
                links.append(full_url)
        
        return links
    
    def navigate_to_next_page(self, driver, current_page: int) -> bool:
        """Navigate using numbered pagination"""
        try:
            wait = WebDriverWait(driver, 15)
            next_button = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f'.jet-filters-pagination__item[data-value="{current_page + 1}"]')
                )
            )
            
            # Scroll to button to ensure it's visible
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            
            # Click button
            driver.execute_script("arguments[0].click();", next_button)
            self.logger.info(f"Successfully navigated to page {current_page + 1}")
            return True
            
        except TimeoutException:
            self.logger.info(f"Next button not found for page {current_page + 1}. Likely last page.")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to page {current_page + 1}: {e}")
            return False
    
    def extract_property_details(self, driver, url: str) -> Dict[str, Any]:
        """Extract property details using Selenium driver (NOT requests)"""
        data = {
            'url': url,
            'listing_type': 'for rent',
            'Company': 'Bali Exception',
            'title': None,
            'property_type': None,
            'price_idr': None,
            'price_usd': None,
            'location': None,
            'features': {},
            'description': []
        }

        try:
            # Navigate to property page with Selenium
            driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
        except Exception as e:
            self.logger.error(f"Error loading page {url}: {e}")
            data['error'] = f"Failed to load page: {e}"
            return data

        # GET TITLE
        try:
            title_tag = soup.find('h1', class_='brxe-post-title')
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)
                if 'villa' in data['title'].lower():
                    data['property_type'] = 'villa'
                elif 'land' in data['title'].lower():
                    data['property_type'] = 'land'
                else:
                    data['property_type'] = None
            else:
                self.logger.warning(f"Title element (h1.brxe-post-title) not found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting title for {url}: {e}")

        # GET PRICE
        try:
            price_span = soup.select_one('span.wpcs_price')
            if price_span:
                raw_price_text = price_span.get_text(strip=True)
                self.logger.debug(f"Raw price text: '{raw_price_text}' for {url}")

                cleaned_price_str = re.sub(r'[^0-9]', '', raw_price_text)
                if cleaned_price_str:
                    price_idr_numeric = int(cleaned_price_str)
                    data['price_idr'] = price_idr_numeric
                    data['price_usd'] = round(price_idr_numeric / self.USD_RATE, 2)
                    self.logger.debug(f"Price IDR: {data['price_idr']}, Price USD: {data['price_usd']}")
                else:
                    self.logger.warning(f"Cleaned price is empty for {url}. Raw: '{raw_price_text}'")
            else:
                self.logger.warning(f"Price span.wpcs_price not found for {url}")
        except (AttributeError, ValueError, TypeError) as e:
            self.logger.error(f"Error processing price for {url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error extracting price for {url}: {e}")

        # GET LOCATION
        try:
            location_tag = soup.select_one('div.jet-listing-dynamic-field__content')
            if location_tag:
                data['location'] = location_tag.get_text(strip=True)
            else:
                self.logger.warning(f"Location element not found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting location for {url}: {e}")

        # GET FEATURES
        try:
            feature_tags = soup.find_all('div', class_='listing-data__wrapper')
            if feature_tags:
                for i in feature_tags:
                    key_tag_elements = i.select('div.brxe-block > div.brxe-text-basic:not(.listing-data_text)')
                    value_tag = i.find('div', class_='listing-data__text')

                    if key_tag_elements and value_tag:
                        value = value_tag.get_text(strip=True)
                        for key_element in key_tag_elements:
                            key = key_element.get_text(strip=True)
                            data['features'][key] = value
                    else:
                        self.logger.warning(f"Incomplete feature data in listing-data__wrapper for {url}")
            else:
                self.logger.warning(f"No feature elements (div.listing-data__wrapper) found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting features for {url}: {e}")

        # GET DESCRIPTION
        try:
            description_tags = soup.select('div.x-read-more_content')
            if description_tags:
                for p_tag in description_tags:
                    paragraph_text = p_tag.get_text(strip=True)
                    if paragraph_text:  # Only append if there's actual text
                        data['description'].append(paragraph_text)
                if not data['description']:  # If list is empty after stripping
                    self.logger.warning(f"Description elements found but were empty for {url}")
            else:
                self.logger.warning(f"No description elements (div.x-read-more_content) found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting description for {url}: {e}")

        return data