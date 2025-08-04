from .base_extractor import BaseExtractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import time
import re
import logging

class BaliExceptionForSaleExtractor(BaseExtractor):
    """Extractor for Bali Exception for-sale properties"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_base_url(self) -> str:
        return "https://baliexception.com"
    
    def get_endpoint(self) -> str:
        return "/properties"
    
    def extract_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract URLs from for-sale listing page"""
        links = []
        cards = soup.select("h2.brxe-gzgohv.brxe-heading.propertyCard__title a")
        
        for card in cards:
            href = card.get("href")
            if href:
                full_url = href if href.startswith('http') else f"{self.get_base_url()}{href}"
                links.append(full_url)
        
        return links
    
    def navigate_to_next_page(self, driver, current_page: int) -> bool:
        """Navigate to next page using numbered pagination"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            
            wait = WebDriverWait(driver, 15)
            next_button = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f'.jet-filters-pagination__item[data-value="{current_page + 1}"]')
                )
            )
            
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_button)
            
            self.logger.info(f"Successfully navigated to page {current_page + 1}")
            return True
            
        except TimeoutException:
            self.logger.info(f"Next button not found for page {current_page + 1}. Likely last page.")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to page {current_page + 1}: {e}")
            return False
    
    def extract_property_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract property details from for-sale property page"""
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
            "url": url, 
            "listing_status": '',
            "amenities": [], 
            "pool_type": '',
            "furnish": '',
            "pool_size": 0,
            "key_information": [], 
            "key_features": [], 
            "features": {},
            "listing_type": "for-sale"
        }

        # Get the title of the property
        title_elem = soup.find('h1', class_='brxe-post-title')
        result['title'] = title_elem.text.strip() if title_elem else ""

        # Get the price of the property
        price_content = soup.select_one('p.converted-price')
        if price_content:
            result['price_usd'] = price_content.get('data-usd-price', 0)
            result['price_idr'] = price_content.get('data-idr-price', 0)
        else:
            result['price_usd'] = 0
            result['price_idr'] = 0

        # Get the listing date of the property
        date_meta = soup.find('meta', {'property': 'article:published_time'})
        if date_meta:
            listing_date = date_meta['content']
            result['listing_date'] = listing_date

        # Get the description, amenities, key information, and key features
        post_content = soup.select_one('div.brxe-post-content')
        if post_content:
            paragraphs = post_content.find_all('p')
            section = 'description'
            for p in paragraphs:
                text = p.get_text(strip=True)
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

        # Get the features of the property
        features = soup.select('ul.featureList__wrapper li')
        for feature in features:
            label_el = feature.select_one('div.brxe-text-basic.featureList')
            value_el = feature.select_one('div.jet-listing-dynamic-field__content')
            value_el2 = feature.select_one('a.jet-listing-dynamic-terms__link')
            if label_el and value_el:
                result['features'][label_el.get_text(strip=True)] = value_el.get_text(strip=True)
            elif label_el and value_el2:
                result['features'][label_el.get_text(strip=True)] = value_el2.get_text(strip=True)
        
        # Apply processing methods
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