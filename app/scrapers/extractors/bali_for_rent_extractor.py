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
import requests

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
        """Scroll to bottom of page - from your code"""
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
        """Complete URL extraction workflow from your code"""
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
            # Common fields for both for-sale and for-rent
            'url': url,
            'listing_type': 'for rent',
            'Company': 'Bali Exception',
            'property_ID': '',
            'title': '',
            'description': '',
            'price_usd': 0,
            'price_idr': 0,
            'location': '',
            'type': '',
            'listing_date': '',
            'status': '',
            'bedrooms': 0,
            'bathrooms': 0,
            'land_size_sqm': 0,
            'building_size_sqm': 0,
            'lease_duration': 0,
            'lease_expiry_year': 0,
            'year_built': 0,
            'listing_status': '',
            'amenities': [],
            'pool': False,
            'pool_type': '',
            'pool_size': 0,
            'furnish': '',
            'key_information': [],
            'key_features': [],
            'features': {},
            # Additional fields that might be in for-sale only (will be null for for-rent)
            'property_type': None
        }

        try:
            # Navigate to property page with Selenium (but we'll use requests for actual scraping)
            import requests
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            
            # Parse with BeautifulSoup - fallback to html.parser if lxml not available
            try:
                soup = BeautifulSoup(res.text, "lxml")
            except:
                self.logger.warning("lxml not available, falling back to html.parser")
                soup = BeautifulSoup(res.text, "html.parser")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error: Could not retrieve page from {url}. Reason: {e}")
            data['error'] = f"Failed to retrieve page: {e}"
            return data
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during page retrieval for {url}. Reason: {e}")
            data['error'] = f"Unexpected error during page retrieval: {e}"
            return data

        # GET TITLE
        try:
            title_tag = soup.find('h1', class_='brxe-post-title')
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)
                # Determine property type from title
                title_lower = data['title'].lower()
                if 'villa' in title_lower:
                    data['type'] = 'villa'
                elif 'land' in title_lower:
                    data['type'] = 'land'
                elif 'house' in title_lower:
                    data['type'] = 'house'
                else:
                    data['type'] = ''
            else:
                self.logger.warning(f"Title element (h1.brxe-post-title) not found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting title for {url}. Reason: {e}")

        # GET PRICE
        try:
            price_span = soup.select_one('span.wpcs_price')
            if price_span:
                raw_price_text = price_span.get_text(strip=True)
                self.logger.debug(f"Raw price text found: '{raw_price_text}' for {url}")

                cleaned_price_str = re.sub(r'[^0-9]', '', raw_price_text)
                if cleaned_price_str:
                    price_idr_numeric = int(cleaned_price_str)
                    data['price_idr'] = price_idr_numeric
                    data['price_usd'] = round(price_idr_numeric / self.USD_RATE, 2)
                    self.logger.debug(f"Price IDR: {data['price_idr']}, Price USD: {data['price_usd']} for {url}")
                else:
                    self.logger.warning(f"Cleaned price (numeric) is empty for {url}. Raw text: '{raw_price_text}'")
            else:
                self.logger.warning(f"Price span.wpcs_price element not found for {url}")
        except (AttributeError, ValueError, TypeError) as e:
            self.logger.error(f"Error processing price for {url}. Reason: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while extracting price for {url}. Reason: {e}")

        # GET LOCATION
        try:
            location_tag = soup.select_one('div.jet-listing-dynamic-field__content')
            if location_tag:
                data['location'] = location_tag.get_text(strip=True)
            else:
                self.logger.warning(f"Location element (div.jet-listing-dynamic-field__content) not found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting location for {url}. Reason: {e}")

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
                        self.logger.warning(f"Incomplete feature data found in a listing-data__wrapper for {url}")
            else:
                self.logger.warning(f"No feature elements (div.listing-data__wrapper) found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting features for {url}. Reason: {e}")

        # GET DESCRIPTION
        try:
            description_tags = soup.select('div.x-read-more_content')
            description_text = ''
            if description_tags:
                for p_tag in description_tags:
                    paragraph_text = p_tag.get_text(strip=True)
                    if paragraph_text:
                        description_text += paragraph_text + '\n'
                data['description'] = description_text.strip()
                if not data['description']:
                    self.logger.warning(f"Description elements found but were empty for {url}")
            else:
                self.logger.warning(f"No description elements (div.x-read-more_content) found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting description for {url}. Reason: {e}")

        # FILL MISSING FIELDS FROM FEATURES
        data = self._fill_missing_fields(data)
        
        # DETECT POOL INFORMATION
        data = self._detect_pool_info(data)
        
        # ESTIMATE LEASE EXPIRY YEAR
        data = self._estimate_lease_expiry_year(data)

        return data

    def _extract_number(self, value):
        """Get the number from a string like '42 m²' → 42 (int)"""
        if not value:
            return 0
        match = re.search(r'\d+(\.\d+)?', str(value).replace(",", ""))
        if match:
            return float(match.group()) if '.' in match.group() else int(match.group())
        return 0

    def _fill_missing_fields(self, data):
        """Fill missing fields from features data"""
        feature_map = {
            'Property ID': 'property_ID',
            'Bedroom': 'bedrooms',
            'Bathroom': 'bathrooms',
            'Land Area': 'land_size_sqm',
            'Property Size': 'building_size_sqm',
            'Furnish': 'furnish',
            'Leasehold': 'lease_duration',
            'Year Built': 'year_built',
            'Status': 'status',
            'Type': 'type',
            'Area': 'location',
            'Label': 'listing_status',
            'Pool Size': 'pool_size'
        }

        for f_key, main_key in feature_map.items():
            if main_key in data and (data[main_key] == '' or data[main_key] == 0):
                value = data['features'].get(f_key, '')
                
                if main_key in ['bedrooms', 'bathrooms', 'land_size_sqm', 'building_size_sqm', 'lease_duration', 'year_built', 'pool_size']:
                    if main_key == 'lease_duration':
                        if isinstance(value, str) and value.strip():
                            value = self._extract_number(value.split()[0])
                        else:
                            value = 0
                    else:
                        value = self._extract_number(value)
                
                data[main_key] = value
        
        return data

    def _detect_pool_info(self, data):
        """Detect pool information from text content"""
        pool_keywords = ['pool', 'swimming pool', 'plunge pool', 'lap pool', 'infinity pool', 'jacuzzi']
        pool_types = ['private', 'shared', 'communal', 'infinity', 'plunge', 'lap', 'jacuzzi']
        
        text_sources = []
        for key in ['description', 'key_information', 'key_features', 'amenities']:
            value = data.get(key, '')
            if isinstance(value, list):
                text_sources.extend(value)
            elif isinstance(value, str):
                text_sources.append(value)

        all_text = ' '.join(text_sources).lower()

        # Pool existence
        has_pool = any(kw in all_text for kw in pool_keywords)

        # Pool type
        pool_type = ''
        for t in pool_types:
            if t in all_text:
                pool_type = t
                break

        data['pool'] = has_pool
        data['pool_type'] = pool_type.title() if pool_type else ''
        return data

    def _estimate_lease_expiry_year(self, data):
        """Estimate lease expiry year"""
        try:
            if data.get('lease_duration') and data.get('year_built'):
                data['lease_expiry_year'] = int(data['year_built']) + int(data['lease_duration'])
        except:
            data['lease_expiry_year'] = 0
        return data