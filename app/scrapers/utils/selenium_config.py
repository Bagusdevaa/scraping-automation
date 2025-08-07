import undetected_chromedriver as uc
from typing import Optional
import os
import logging

class SeleniumConfig:
    @staticmethod
    def get_chrome_options(headless: bool = False) -> uc.ChromeOptions:
        """Standard Chrome options for all scrapers using undetected-chromedriver"""
        options = uc.ChromeOptions()
        
        # Basic options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Remove hardcoded user agent - let undetected-chromedriver handle it
        # This prevents version mismatch issues
        
        # Additional stealth options (optional with undetected-chromedriver)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            options.add_argument('--headless=new')
            
        return options
    
    @staticmethod
    def create_driver(headless: bool = False, version_main: Optional[int] = None) -> uc.Chrome:
        """Create undetected Chrome WebDriver with standard configuration"""
        try:
            options = SeleniumConfig.get_chrome_options(headless)
            
            # Mendapatkan path dari environment variables dengan fallback
            chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/google-chrome-stable")
            chromedriver_bin = os.getenv("CHROMEDRIVER_BIN", "/usr/local/bin/chromedriver")
            
            # Check if Chrome binary exists
            if not os.path.exists(chrome_bin):
                chrome_bin = "/usr/bin/google-chrome"  # Another fallback
                if not os.path.exists(chrome_bin):
                    chrome_bin = None  # Let undetected-chromedriver find it
            
            # Create undetected Chrome driver dengan path yang spesifik
            driver = uc.Chrome(
                browser_executable_path=chrome_bin,
                driver_executable_path=chromedriver_bin,
                options=options,
                version_main=version_main
            )
            
            # Set timeouts
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(10)
            
            logging.info("✅ Undetected WebDriver initialized successfully")
            logging.info(f"Chrome binary: {chrome_bin}")
            logging.info(f"ChromeDriver: {chromedriver_bin}")
            return driver
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize undetected WebDriver: {e}")
            raise Exception(f"Failed to initialize WebDriver: {e}")
    
    @staticmethod
    def create_stealth_driver(headless: bool = False) -> uc.Chrome:
        """Create maximum stealth undetected Chrome WebDriver"""
        try:
            options = uc.ChromeOptions()
            
            # Minimal options for maximum stealth
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            if headless:
                options.add_argument('--headless=new')
            
            # Mendapatkan path dari environment variables dengan fallback
            chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/google-chrome-stable")
            chromedriver_bin = os.getenv("CHROMEDRIVER_BIN", "/usr/local/bin/chromedriver")

            # Check if Chrome binary exists
            if not os.path.exists(chrome_bin):
                chrome_bin = "/usr/bin/google-chrome"  # Another fallback
                if not os.path.exists(chrome_bin):
                    chrome_bin = None  # Let undetected-chromedriver find it

            # Let undetected-chromedriver handle most anti-detection
            driver = uc.Chrome(
                browser_executable_path=chrome_bin,
                driver_executable_path=chromedriver_bin,
                options=options
            )
            driver.set_page_load_timeout(60)
            
            logging.info("✅ Stealth WebDriver initialized successfully")
            logging.info(f"Chrome binary: {chrome_bin}")
            logging.info(f"ChromeDriver: {chromedriver_bin}")
            return driver
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize stealth WebDriver: {e}")
            raise Exception(f"Failed to initialize stealth WebDriver: {e}")