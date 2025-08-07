import undetected_chromedriver as uc
from typing import Optional
import os
import platform
import shutil
import logging

class SeleniumConfig:
    @staticmethod
    def _detect_chrome_path():
        """Smart detection untuk Chrome binary path cross-platform"""
        system = platform.system().lower()
        
        if system == "windows":
            # Windows paths (x64 dan ARM64)
            windows_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                # Edge sebagai fallback untuk ARM64 Windows
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
            
            for path in windows_paths:
                if os.path.exists(path):
                    logging.info(f"[SUCCESS] Found Chrome at: {path}")
                    return path
                    
        elif system == "linux":
            # Linux paths (production VPS)
            linux_paths = [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/opt/google/chrome/chrome"
            ]
            
            for path in linux_paths:
                if os.path.exists(path):
                    logging.info(f"[SUCCESS] Found Chrome at: {path}")
                    return path
                    
        elif system == "darwin":  # macOS
            mac_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            ]
            
            for path in mac_paths:
                if os.path.exists(path):
                    logging.info(f"[SUCCESS] Found Chrome at: {path}")
                    return path
        
        # Jika tidak ada yang ditemukan, return None - biarkan undetected-chromedriver auto-detect
        logging.warning("[WARNING] Chrome path not found, using auto-detection")
        return None
    
    @staticmethod
    def _detect_chromedriver_path():
        """Smart detection untuk ChromeDriver - dengan prioritas auto-download"""
        # Pertama cek apakah sudah ada di system PATH
        chromedriver_cmd = "chromedriver.exe" if platform.system().lower() == "windows" else "chromedriver"
        
        if shutil.which(chromedriver_cmd):
            path = shutil.which(chromedriver_cmd)
            logging.info(f"[SUCCESS] Found ChromeDriver in PATH: {path}")
            return path
        
        # Jika tidak ada, return None - biarkan undetected-chromedriver auto-download
        logging.info("[INFO] ChromeDriver not found in PATH, using auto-download")
        return None
    @staticmethod
    def get_chrome_options(headless: bool = True) -> uc.ChromeOptions:
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
    def create_driver(headless: bool = True, version_main: Optional[int] = None) -> uc.Chrome:
        """Create undetected Chrome WebDriver dengan smart auto-detection"""
        try:
            options = SeleniumConfig.get_chrome_options(headless)
            
            # Smart detection untuk paths
            chrome_bin = SeleniumConfig._detect_chrome_path()
            chromedriver_bin = SeleniumConfig._detect_chromedriver_path()
            
            # Auto-detect Chrome version jika tidak diberikan
            if version_main is None:
                try:
                    # Untuk Windows, coba detect version dari registry atau file
                    if platform.system().lower() == "windows" and chrome_bin:
                        import subprocess
                        result = subprocess.run([chrome_bin, '--version'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            version_str = result.stdout.strip()
                            # Extract version number (e.g., "Google Chrome 138.0.7204.184")
                            import re
                            match = re.search(r'(\d+)\.', version_str)
                            if match:
                                version_main = int(match.group(1))
                                logging.info(f"🔍 Auto-detected Chrome version: {version_main}")
                except Exception as e:
                    logging.warning(f"[WARNING] Could not auto-detect Chrome version: {e}")
                    # Default fallback untuk Chrome 138 (current version on Windows ARM64)
                    version_main = 138
                    logging.info(f"[TOOL] Using fallback Chrome version: {version_main}")
            
            # Create driver dengan conditional parameters
            driver_kwargs = {
                'options': options,
                'version_main': version_main
            }
            
            # Hanya tambahkan path jika ditemukan, biarkan undetected-chromedriver auto-detect
            if chrome_bin:
                driver_kwargs['browser_executable_path'] = chrome_bin
            if chromedriver_bin:
                driver_kwargs['driver_executable_path'] = chromedriver_bin
            
            logging.info(f"🚀 Initializing WebDriver...")
            logging.info(f"   Platform: {platform.system()} {platform.machine()}")
            logging.info(f"   Chrome binary: {chrome_bin or 'auto-detect'}")
            logging.info(f"   ChromeDriver: {chromedriver_bin or 'auto-download'}")
            logging.info(f"   Chrome version: {version_main}")
            
            driver = uc.Chrome(**driver_kwargs)
            
            # Set timeouts
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(10)
            
            logging.info("[SUCCESS] Undetected WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            logging.error(f"[ERROR] Failed to initialize undetected WebDriver: {e}")
            logging.info("💡 Tip: undetected-chromedriver akan auto-download ChromeDriver jika diperlukan")
            raise Exception(f"Failed to initialize WebDriver: {e}")
    
    @staticmethod
    def create_stealth_driver(headless: bool = True) -> uc.Chrome:
        """Create maximum stealth undetected Chrome WebDriver dengan smart auto-detection"""
        try:
            options = uc.ChromeOptions()
            
            # Minimal options for maximum stealth
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Performance optimization untuk ARM64
            if platform.machine().lower() in ['arm64', 'aarch64']:
                options.add_argument('--disable-features=VizDisplayCompositor')
                options.add_argument('--disable-software-rasterizer')
            
            if headless:
                options.add_argument('--headless=new')
            
            # Smart detection untuk paths
            chrome_bin = SeleniumConfig._detect_chrome_path()
            chromedriver_bin = SeleniumConfig._detect_chromedriver_path()
            
            # Auto-detect Chrome version
            version_main = None
            try:
                if platform.system().lower() == "windows" and chrome_bin:
                    import subprocess
                    result = subprocess.run([chrome_bin, '--version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        version_str = result.stdout.strip()
                        import re
                        match = re.search(r'(\d+)\.', version_str)
                        if match:
                            version_main = int(match.group(1))
                            logging.info(f"🔍 Auto-detected Chrome version: {version_main}")
            except Exception as e:
                logging.warning(f"[WARNING] Could not auto-detect Chrome version: {e}")
                version_main = 138  # Default fallback
                logging.info(f"[TOOL] Using fallback Chrome version: {version_main}")
            
            # Create driver dengan conditional parameters
            driver_kwargs = {
                'options': options,
                'version_main': version_main
            }
            
            if chrome_bin:
                driver_kwargs['browser_executable_path'] = chrome_bin
            if chromedriver_bin:
                driver_kwargs['driver_executable_path'] = chromedriver_bin
            
            logging.info(f"🥷 Initializing Stealth WebDriver...")
            logging.info(f"   Platform: {platform.system()} {platform.machine()}")
            logging.info(f"   Chrome binary: {chrome_bin or 'auto-detect'}")
            logging.info(f"   ChromeDriver: {chromedriver_bin or 'auto-download'}")
            logging.info(f"   Chrome version: {version_main}")

            # Let undetected-chromedriver handle most anti-detection
            driver = uc.Chrome(**driver_kwargs)
            driver.set_page_load_timeout(60)
            
            logging.info("[SUCCESS] Stealth WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            logging.error(f"[ERROR] Failed to initialize stealth WebDriver: {e}")
            logging.info("💡 Tip: Pastikan Google Chrome terinstall atau gunakan Edge untuk ARM64")
            raise Exception(f"Failed to initialize stealth WebDriver: {e}")
    
    @staticmethod
    def debug_environment():
        """Debug environment untuk troubleshooting"""
        logging.info("🔍 Environment Debug Information:")
        logging.info(f"   OS: {platform.system()} {platform.release()}")
        logging.info(f"   Architecture: {platform.machine()}")
        logging.info(f"   Python: {platform.python_version()}")
        
        chrome_path = SeleniumConfig._detect_chrome_path()
        chromedriver_path = SeleniumConfig._detect_chromedriver_path()
        
        logging.info(f"   Chrome detected: {'[SUCCESS]' if chrome_path else '[ERROR]'} {chrome_path or 'Not found'}")
        logging.info(f"   ChromeDriver detected: {'[SUCCESS]' if chromedriver_path else '[INFO]'} {chromedriver_path or 'Will auto-download'}")
        
        # Check undetected-chromedriver version
        try:
            import undetected_chromedriver as uc
            logging.info(f"   undetected-chromedriver: [SUCCESS] {uc.__version__ if hasattr(uc, '__version__') else 'installed'}")
        except ImportError:
            logging.error("   undetected-chromedriver: [ERROR] Not installed")
        
        return {
            "os": platform.system(),
            "architecture": platform.machine(),
            "chrome_path": chrome_path,
            "chromedriver_path": chromedriver_path
        }

# Convenience functions for easier imports
def create_stealth_driver(headless: bool = True) -> uc.Chrome:
    """Convenience function untuk create stealth driver"""
    return SeleniumConfig.create_stealth_driver(headless=headless)

def get_chrome_options(headless: bool = True) -> uc.ChromeOptions:
    """Convenience function untuk get Chrome options"""
    return SeleniumConfig.get_chrome_options(headless=headless)