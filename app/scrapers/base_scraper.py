from abc import ABC, abstractmethod
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from typing import List, Dict, Any
import time
import logging
import undetected_chromedriver as uc
from .utils.selenium_config import SeleniumConfig

class BaseScraper(ABC):
    def __init__(self, headless: bool = False, stealth_mode: bool = True):
        self.driver: uc.Chrome = None
        self.wait: WebDriverWait = None
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def __enter__(self):
        self.setup_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def setup_driver(self):
        """Initialize undetected WebDriver"""
        try:
            if self.stealth_mode:
                self.driver = SeleniumConfig.create_stealth_driver(self.headless)
            else:
                self.driver = SeleniumConfig.create_driver(self.headless)
                
            self.wait = WebDriverWait(self.driver, 15)
            self.logger.info("✅ Undetected WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to setup driver: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("✅ WebDriver closed successfully")
            except Exception as e:
                self.logger.error(f"❌ Error closing driver: {e}")
    
    @abstractmethod
    def scrape_all_urls(self) -> List[str]:
        """Scrape all property URLs from the website"""
        pass
    
    @abstractmethod
    def scrape_property_details(self, url: str) -> Dict[str, Any]:
        """Scrape details from a single property URL"""
        pass
    
    def scrape_all_properties(self) -> List[Dict[str, Any]]:
        """Complete scraping workflow"""
        urls = self.scrape_all_urls()
        properties = []
        
        for url in urls:
            try:
                property_data = self.scrape_property_details(url)
                properties.append(property_data)
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}")
                continue
        
        return properties