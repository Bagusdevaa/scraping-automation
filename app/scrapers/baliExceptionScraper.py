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
        """Scrape details from a single property URL with robust error handling"""
        self.logger.info(f"Scraping property: {url}")
        
        try:
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
                "url": url, 
                "listing_status": '',
                "amenities": [], 
                "pool_type": '',
                "furnish": '',
                "pool_size": 0,
                "key_information": [], 
                "key_features": [], 
                "features": {},
                "scraping_errors": []  # Track any extraction errors
            }

            # get the title of the property
            try:
                title_elem = soup.find('h1', class_='brxe-post-title')
                result['title'] = title_elem.text.strip() if title_elem else ""
                if not result['title']:
                    result['scraping_errors'].append("Title element not found")
                    self.logger.warning(f"⚠️ Title not found for {url}")
            except Exception as e:
                result['scraping_errors'].append(f"Title extraction error: {e}")
                self.logger.error(f"❌ Title extraction failed for {url}: {e}")

            # get the price of the property
            try:
                price_content = soup.select_one('p.converted-price')
                if price_content:
                    result['price_usd'] = price_content.get('data-usd-price', 0)
                    result['price_idr'] = price_content.get('data-idr-price', 0)
                else:
                    result['price_usd'] = 0
                    result['price_idr'] = 0
                    result['scraping_errors'].append("Price element not found")
                    self.logger.warning(f"⚠️ Price not found for {url}")
            except Exception as e:
                result['scraping_errors'].append(f"Price extraction error: {e}")
                self.logger.error(f"❌ Price extraction failed for {url}: {e}")

            # get the listing date of the property
            try:
                date_meta = soup.find('meta', {'property': 'article:published_time'})
                if date_meta:
                    listing_date = date_meta['content']
                    result['listing_date'] = listing_date
                else:
                    result['scraping_errors'].append("Listing date not found")
            except Exception as e:
                result['scraping_errors'].append(f"Date extraction error: {e}")
                self.logger.error(f"❌ Date extraction failed for {url}: {e}")

            # get the description, amenities, key information, and key features of the property
            try:
                post_content = soup.select_one('div.brxe-post-content')
                if post_content:
                    paragraphs = post_content.find_all('p')
                    section = 'description'
                    for p in paragraphs:
                        try:
                            text = p.get_text(strip=True) if p else ""
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
                        except Exception as inner_e:
                            self.logger.warning(f"⚠️ Paragraph processing error: {inner_e}")
                            continue
                else:
                    result['scraping_errors'].append("Post content not found")
            except Exception as e:
                result['scraping_errors'].append(f"Content extraction error: {e}")
                self.logger.error(f"❌ Content extraction failed for {url}: {e}")

            # get the features of the property
            try:
                features = soup.select('ul.featureList__wrapper li')
                for feature in features:
                    try:
                        label_el = feature.select_one('div.brxe-text-basic.featureList')
                        value_el = feature.select_one('div.jet-listing-dynamic-field__content')
                        value_el2 = feature.select_one('a.jet-listing-dynamic-terms__link')
                        
                        if label_el and value_el:
                            label_text = label_el.get_text(strip=True) if label_el else ""
                            value_text = value_el.get_text(strip=True) if value_el else ""
                            if label_text and value_text:
                                result['features'][label_text] = value_text
                        elif label_el and value_el2:
                            label_text = label_el.get_text(strip=True) if label_el else ""
                            value_text = value_el2.get_text(strip=True) if value_el2 else ""
                            if label_text and value_text:
                                result['features'][label_text] = value_text
                    except Exception as feature_e:
                        self.logger.warning(f"⚠️ Feature processing error: {feature_e}")
                        continue
            except Exception as e:
                result['scraping_errors'].append(f"Features extraction error: {e}")
                self.logger.error(f"❌ Features extraction failed for {url}: {e}")
            
            # Apply processing methods with error handling
            try:
                result = self._fill_missing_fields(result)
                result = self._detect_pool_info(result)
                result = self._estimate_lease_expiry_year(result)
            except Exception as e:
                result['scraping_errors'].append(f"Post-processing error: {e}")
                self.logger.error(f"❌ Post-processing failed for {url}: {e}")

            # Log success/warnings
            if result['scraping_errors']:
                self.logger.warning(f"⚠️ Property scraped with {len(result['scraping_errors'])} errors: {url}")
            else:
                self.logger.info(f"✅ Property scraped successfully: {result.get('title', 'No title')}")

            return result
            
        except Exception as e:
            # Catastrophic failure - return error result
            self.logger.error(f"Complete scraping failure for {url}: {e}")
            return {
                "url": url,
                "scraping_errors": [f"Complete failure: {e}"],
                "title": "",
                "description": "",
                "price_usd": 0,
                "price_idr": 0,
                "location": "",
                "features": {},
                "error": True
            }
    
    def _extract_number(self, value):
        """Get the number from a string like '42 m²' → 42 (int)"""
        match = re.search(r'\d+(\.\d+)?', value.replace(",", ""))
        if match:
            return float(match.group()) if '.' in match.group() else int(match.group())
        return 0
    
    def _fill_missing_fields(self, data):
        """Fill missing fields from features data with error handling"""
        try:
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
                try:
                    if main_key in data and (data[main_key] == '' or data[main_key] == 0):
                        value = data.get('features', {}).get(f_key, '')
                        
                        if main_key in ['bedrooms', 'bathrooms', 'land_size_sqm', 'building_size_sqm', 'lease_duration', 'year_built']:
                            if main_key == 'lease_duration':
                                if isinstance(value, str) and value.strip():
                                    try:
                                        value = self._extract_number(value.split()[0])
                                    except:
                                        value = 0
                                else:
                                    value = 0
                            else:
                                try:
                                    value = self._extract_number(value)
                                except:
                                    value = 0
                        
                        data[main_key] = value
                except Exception as e:
                    self.logger.warning(f"⚠️ Error processing field {f_key}: {e}")
                    continue
            
            return data
        except Exception as e:
            self.logger.error(f"❌ _fill_missing_fields failed: {e}")
            return data
    
    def _detect_pool_info(self, data):
        """Detect pool information from text content with error handling"""
        try:
            pool_keywords = ['pool', 'swimming pool', 'plunge pool', 'lap pool', 'infinity pool', 'jacuzzi']
            pool_types = ['private', 'shared', 'communal', 'infinity', 'plunge', 'lap', 'jacuzzi']
            
            text_sources = []
            for key in ['description', 'key_information', 'key_features', 'amenities']:
                try:
                    value = data.get(key, '')
                    if isinstance(value, list):
                        text_sources.extend(value)
                    elif isinstance(value, str):
                        text_sources.append(value)
                except Exception as e:
                    self.logger.warning(f"⚠️ Error processing text source {key}: {e}")
                    continue

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
        except Exception as e:
            self.logger.error(f"❌ _detect_pool_info failed: {e}")
            # Return data with default pool values
            data['pool'] = False
            data['pool_type'] = ''
            return data
    
    def _estimate_lease_expiry_year(self, data):
        """Estimate lease expiry year with error handling"""
        try:
            if data.get('lease_duration') and data.get('year_built'):
                lease_duration = int(data['lease_duration']) if isinstance(data['lease_duration'], (int, str)) else 0
                year_built = int(data['year_built']) if isinstance(data['year_built'], (int, str)) else 0
                
                if lease_duration > 0 and year_built > 0:
                    data['lease_expiry_year'] = year_built + lease_duration
                else:
                    data['lease_expiry_year'] = 0
            else:
                data['lease_expiry_year'] = 0
        except Exception as e:
            self.logger.warning(f"⚠️ Error calculating lease expiry: {e}")
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