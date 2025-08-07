from .base_extractor import BaseExtractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time
import re
import logging

class BaliExceptionForSaleExtractor(BaseExtractor):
    """Extractor for Bali Exception for-sale properties (main domain)"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.USD_RATE = 16350
    
    def get_base_url(self) -> str:
        return "https://baliexception.com"
    
    def get_endpoint(self) -> str:
        return "/properties"
    
    def extract_urls_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract URLs using for-sale specific selector"""
        links = []
        # For-sale uses different selector: h2.brxe-gzgohv.brxe-heading.propertyCard__title a
        cards = soup.select("h2.brxe-gzgohv.brxe-heading.propertyCard__title a")
        
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
        """Navigate to next page using for-sale pagination"""
        try:
            # Look for ">" next button or page number
            next_button = None
            
            # Try different selectors for next page
            selectors = [
                f'.jet-filters-pagination__item[data-value="{current_page + 1}"]',  # Original selector
                "a.next.page-numbers",  # WordPress style
                ".pagination .next",
                f"a[aria-label='Page {current_page + 1}']",
                ".page-numbers .next",
                ".pagination-next"
            ]
            
            for selector in selectors:
                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if next_button:
                # Scroll to button
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                
                # Click button
                driver.execute_script("arguments[0].click();", next_button)
                self.logger.info(f"Successfully navigated to page {current_page + 1}")
                return True
            else:
                self.logger.info(f"No next page button found. Likely last page.")
                return False
                
        except Exception as e:
            self.logger.error(f"Error navigating to page {current_page + 1}: {e}")
            return False
    
    def extract_property_details(self, driver, url: str) -> Dict[str, Any]:
        """Extract property details for for-sale properties"""
        data = {
            'url': url,
            'listing_type': 'for sale',
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
            # Navigate to property page
            driver.get(url)
            time.sleep(3)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
        except Exception as e:
            self.logger.error(f"Error loading page {url}: {e}")
            data['error'] = f"Failed to load page: {e}"
            return data

        # GET TITLE (for-sale might use different selector than for-rent)
        try:
            # Try multiple title selectors
            title_selectors = [
                'h1.brxe-post-title',
                'h1.entry-title',
                'h1.property-title',
                '.property-header h1'
            ]
            
            title_tag = None
            for selector in title_selectors:
                title_tag = soup.select_one(selector)
                if title_tag:
                    break
            
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)
                # Determine property type from title
                title_lower = data['title'].lower()
                if 'villa' in title_lower:
                    data['property_type'] = 'villa'
                elif 'land' in title_lower:
                    data['property_type'] = 'land'
                elif 'house' in title_lower:
                    data['property_type'] = 'house'
                else:
                    data['property_type'] = None
            else:
                self.logger.warning(f"Title element not found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting title for {url}: {e}")

        # GET PRICE
        try:
            # Try multiple price selectors for for-sale
            price_selectors = [
                'p.converted-price',
                'span.wpcs_price',
                '.property-price',
                '.price-value',
                '.listing-price'
            ]
            
            price_element = None
            for selector in price_selectors:
                price_element = soup.select_one(selector)
                if price_element:
                    break
            
            if price_element:
                # For converted-price, try data attributes first
                if price_element.has_attr('data-usd-price') and price_element.has_attr('data-idr-price'):
                    data['price_usd'] = float(price_element.get('data-usd-price', 0))
                    data['price_idr'] = int(price_element.get('data-idr-price', 0))
                else:
                    # Fallback to text extraction
                    raw_price_text = price_element.get_text(strip=True)
                    self.logger.debug(f"Raw price text: '{raw_price_text}' for {url}")

                    # Extract numeric value
                    cleaned_price_str = re.sub(r'[^0-9]', '', raw_price_text)
                    if cleaned_price_str:
                        price_idr_numeric = int(cleaned_price_str)
                        data['price_idr'] = price_idr_numeric
                        data['price_usd'] = round(price_idr_numeric / self.USD_RATE, 2)
                        self.logger.debug(f"Price IDR: {data['price_idr']}, Price USD: {data['price_usd']}")
                    else:
                        self.logger.warning(f"Cleaned price is empty for {url}. Raw: '{raw_price_text}'")
            else:
                self.logger.warning(f"Price element not found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting price for {url}: {e}")

        # GET LOCATION
        try:
            # Try multiple location selectors
            location_selectors = [
                'div.jet-listing-dynamic-field__content',
                '.property-location',
                '.location-info',
                '.address-info'
            ]
            
            location_tag = None
            for selector in location_selectors:
                location_tag = soup.select_one(selector)
                if location_tag:
                    break
            
            if location_tag:
                data['location'] = location_tag.get_text(strip=True)
            else:
                self.logger.warning(f"Location element not found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting location for {url}: {e}")

        # GET FEATURES
        try:
            # Try multiple feature selectors
            feature_selectors = [
                'ul.featureList__wrapper li',
                'div.listing-data__wrapper',
                '.property-features .feature-item',
                '.amenities-list li'
            ]
            
            feature_tags = []
            for selector in feature_selectors:
                feature_tags = soup.select(selector)
                if feature_tags:
                    break
            
            if feature_tags:
                for feature_item in feature_tags:
                    # For ul.featureList__wrapper li structure
                    label_element = feature_item.select_one('div.brxe-text-basic.featureList')
                    value_element1 = feature_item.select_one('div.jet-listing-dynamic-field__content')
                    value_element2 = feature_item.select_one('a.jet-listing-dynamic-terms__link')
                    
                    if label_element and (value_element1 or value_element2):
                        key = label_element.get_text(strip=True)
                        value = (value_element1 or value_element2).get_text(strip=True)
                        data['features'][key] = value
                    else:
                        # Alternative: extract key-value pairs from other structures
                        key_elements = feature_item.select('div.brxe-block > div.brxe-text-basic:not(.listing-data_text)')
                        value_element = feature_item.select_one('div.listing-data__text')

                        if key_elements and value_element:
                            value = value_element.get_text(strip=True)
                            for key_element in key_elements:
                                key = key_element.get_text(strip=True)
                                data['features'][key] = value
                        else:
                            # Simple text content with colon separator
                            feature_text = feature_item.get_text(strip=True)
                            if ':' in feature_text:
                                key, value = feature_text.split(':', 1)
                                data['features'][key.strip()] = value.strip()
            else:
                self.logger.warning(f"No feature elements found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting features for {url}: {e}")

        # GET DESCRIPTION
        try:
            # Try multiple description selectors
            description_selectors = [
                'div.brxe-post-content p',
                'div.x-read-more_content',
                '.property-description',
                '.entry-content p',
                '.description-content'
            ]
            
            description_tags = []
            for selector in description_selectors:
                description_tags = soup.select(selector)
                if description_tags:
                    break
            
            if description_tags:
                for desc_tag in description_tags:
                    paragraph_text = desc_tag.get_text(strip=True)
                    if paragraph_text:
                        data['description'].append(paragraph_text)
                
                if not data['description']:
                    self.logger.warning(f"Description elements found but were empty for {url}")
            else:
                self.logger.warning(f"No description elements found for {url}")
        except Exception as e:
            self.logger.error(f"Error extracting description for {url}: {e}")

        return data