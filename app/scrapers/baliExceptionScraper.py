from .base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import time
import re

class BaliExceptionScraper(BaseScraper):
    BASE_URL = "https://baliexception.com"
    
    def scrape_all_urls(self) -> List[str]:
        """Scrape all property URLs from Bali Exception"""
        try:
            self.driver.get(f"{self.BASE_URL}/properties")
            self.logger.info("Properties page loaded successfully")
            
            time.sleep(3)
            all_links = []
            current_page = 1
            
            while True:
                self.logger.info(f"Scraping page {current_page}...")
                
                try:
                    # Wait for elements
                    self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "h2.brxe-gzgohv.brxe-heading.propertyCard__title a")
                        )
                    )
                    
                    # Parse HTML
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    cards = soup.select("h2.brxe-gzgohv.brxe-heading.propertyCard__title a")
                    
                    if not cards:
                        self.logger.info(f"No cards found on page {current_page}")
                        break
                    
                    # Extract URLs
                    page_links = self._extract_urls_from_cards(cards)
                    all_links.extend(page_links)
                    
                    self.logger.info(f"Found {len(page_links)} links on page {current_page}")
                    self.logger.info(f"Total links so far: {len(all_links)}")
                    
                    # Try to navigate to next page
                    if not self._navigate_to_next_page(current_page):
                        break
                    
                    current_page += 1
                    time.sleep(3)
                    
                except TimeoutException:
                    self.logger.warning(f"Timeout waiting for elements on page {current_page}")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected error on page {current_page}: {e}")
                    break
            
            return list(set(all_links))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error accessing main page: {e}")
            return []
    
    def _extract_urls_from_cards(self, cards) -> List[str]:
        """Extract URLs from property cards"""
        links = []
        for card in cards:
            href = card.get("href")
            if href:
                full_url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
                links.append(full_url)
        return links
    
    def _navigate_to_next_page(self, current_page: int) -> bool:
        """Navigate to next page"""
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f'.jet-filters-pagination__item[data-value="{current_page + 1}"]')
                )
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", next_button)
            
            self.logger.info(f"Successfully navigated to page {current_page + 1}")
            return True
            
        except TimeoutException:
            self.logger.info(f"Next button not found for page {current_page + 1}. Likely last page.")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to page {current_page + 1}: {e}")
            return False
    
    def scrape_property_details(self, url: str) -> Dict[str, Any]:
        """Scrape details from a single property URL"""
        self.driver.get(url)
        time.sleep(3)  # Wait for page load
        
        soup = BeautifulSoup(self.driver.page_source, "html.parser")


        result = {
            "property_ID": '', 
            "title": '', 
            "description": '', 
            "price_usd": 0, 
            "price_idr": 0, 
            "location": '',
            "type": '',
            "listing_date": '', 
            "status": '',
            "bedrooms": 0,
            "bathrooms": 0,
            "land_size_sqm": 0,
            "building_size_sqm": 0,
            "lease_duration": 0,
            "lease_expiry_year": 0,
            "year_built": 0,
            "url": '', 
            "listing_status": '',
            "amenities": [], 
            "pool_type": '',
            "furnish": '',
            "pool_size": 0,
            "key_information": [], 
            "key_features": [], 
            "features": {} 
        }

        # get the title of the property
        result['title'] = soup.find('h1', class_='brxe-post-title').text.strip()

        # get the price of the property
        price_content = soup.select_one('p.converted-price')
        if price_content:
            result['price_usd'] = price_content.get('data-usd-price')
            result['price_idr'] = price_content.get('data-idr-price')
        else:
            result['price_usd'] = 0
            result['price_idr'] = 0

        # get the listing date of the property
        date_meta = soup.find('meta', {'property': 'article:published_time'})
        if date_meta:
            listing_date = date_meta['content']
            result['listing_date'] = listing_date

        # get the url of the property
        result['url'] = url

        # get the description, amenities, key information, and key features of the property
        post_content = soup.select_one('div.brxe-post-content')
        if post_content:
            paragraphs = post_content.find_all('p')
            section = 'description'
            for p in paragraphs:
                text = p.get_text(strip=True)
                # checking_text = text.lower() if text == str else text
                if 'WE LOVE' in text:
                    section = 'amenities'
                    continue
                elif 'KEY INFORMATION' in text:
                    section = 'key_information'
                    continue
                elif 'Key Features Include' in text:
                    section = 'key_features'
                    continue

                if not text:
                    continue

                if section == 'description':
                    result['description'] += text + '\n'
                elif section == 'amenities':
                    result['amenities'].append(text)
                elif section == 'key_information':
                    result['key_information'].append(text)
                elif section == 'key_features':
                    result['key_features'].append(text)

        # get the features of the property
        features = soup.select('ul.featureList__wrapper li')
        for feature in features:
            label_el = feature.select_one('div.brxe-text-basic.featureList')
            value_el = feature.select_one('div.jet-listing-dynamic-field__content')
            value_el2 = feature.select_one('a.jet-listing-dynamic-terms__link')
            if label_el and value_el:
                result['features'][label_el.get_text(strip=True)] = value_el.get_text(strip=True)
            elif label_el and value_el2:
                result['features'][label_el.get_text(strip=True)] = value_el2.get_text(strip=True)
        
        result = self._fill_missing_fields(result)
        result = self._detect_pool_info(result)
        result = self._estimate_lease_expiry_year(result)

        return result
    
    def _extract_number(self, value):
        """Get the number from a string like '42 m²' → 42 (int)"""
        match = re.search(r'\d+(\.\d+)?', value.replace(",", ""))
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
                
                if main_key in ['bedrooms', 'bathrooms', 'land_size_sqm', 'building_size_sqm', 'lease_duration', 'year_built']:
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
            value = data.get(key)
            if isinstance(value, list):
                text_sources += value
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
        try:
            if data.get('lease_duration') and data.get('year_built'):
                data['lease_expiry_year'] = int(data['year_built']) + int(data['lease_duration'])
        except:
            data['lease_expiry_year'] = 0

        return data
    
    def scrape_limited_urls(self, max_pages: int = 2) -> List[str]:
        """Scrape URLs from limited pages only (for testing)"""
        try:
            self.driver.get(f"{self.BASE_URL}/properties")
            self.logger.info("Properties page loaded successfully")
            
            time.sleep(3)
            all_links = []
            current_page = 1
            
            while current_page <= max_pages:  # LIMIT PAGES
                self.logger.info(f"Scraping page {current_page}/{max_pages}...")
                
                try:
                    # Wait for elements
                    self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "h2.brxe-gzgohv.brxe-heading.propertyCard__title a")
                        )
                    )
                    
                    # Parse HTML
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    cards = soup.select("h2.brxe-gzgohv.brxe-heading.propertyCard__title a")
                    
                    if not cards:
                        self.logger.info(f"No cards found on page {current_page}")
                        break
                    
                    # Extract URLs
                    page_links = self._extract_urls_from_cards(cards)
                    all_links.extend(page_links)
                    
                    self.logger.info(f"Found {len(page_links)} links on page {current_page}")
                    
                    # Navigate to next page (if not last page)
                    if current_page < max_pages:
                        if not self._navigate_to_next_page(current_page):
                            break
                        current_page += 1
                        time.sleep(3)
                    else:
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error on page {current_page}: {e}")
                    break
            
            return list(set(all_links))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error accessing main page: {e}")
            return []