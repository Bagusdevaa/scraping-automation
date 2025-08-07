"""
System and utility API routes
"""

from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.scrapers.utils.selenium_config import SeleniumConfig
import logging
import platform
import psutil
import os
from datetime import datetime

router = APIRouter(prefix="/system", tags=["System"])
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """System health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": "production" if os.getenv("ENVIRONMENT") == "production" else "development"
    }

@router.get("/info")
async def system_info():
    """Get comprehensive system information"""
    try:
        # System information
        system_info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "memory_usage_percent": psutil.virtual_memory().percent
        }
        
        # Chrome/ChromeDriver information
        try:
            selenium_config = SeleniumConfig()
            chrome_info = selenium_config.get_chrome_info()
        except Exception as e:
            chrome_info = {"error": str(e)}
        
        # Environment configuration
        config_info = {
            "log_level": getattr(settings, 'LOG_LEVEL', 'INFO'),
            "google_sheets_enabled": bool(settings.GOOGLE_SHEET_ID),
            "headless_mode": settings.HEADLESS_MODE,
            "stealth_mode": getattr(settings, 'STEALTH_MODE', True)
        }
        
        return {
            "system": system_info,
            "chrome_driver": chrome_info,
            "configuration": config_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chrome-status")
async def chrome_status():
    """Check Chrome and ChromeDriver status"""
    try:
        selenium_config = SeleniumConfig()
        
        # Get Chrome information
        chrome_info = selenium_config.get_chrome_info()
        
        # Test driver creation
        driver_test = {"status": "unknown", "error": None}
        try:
            with selenium_config.create_stealth_driver(headless=True) as driver:
                driver.get("https://www.google.com")
                driver_test = {"status": "working", "test_url": "https://www.google.com"}
        except Exception as e:
            driver_test = {"status": "failed", "error": str(e)}
        
        return {
            "chrome_info": chrome_info,
            "driver_test": driver_test,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chrome status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-scraping")
async def test_scraping_capability():
    """Test basic scraping functionality"""
    try:
        from app.scrapers.baliExceptionScraper import BaliExceptionScraper
        
        test_results = {
            "chrome_driver": {"status": "unknown"},
            "bali_exception": {"status": "unknown"},
            "overall": {"status": "unknown"}
        }
        
        # Test Chrome driver
        try:
            selenium_config = SeleniumConfig()
            with selenium_config.create_stealth_driver(headless=True) as driver:
                driver.get("https://www.google.com")
                test_results["chrome_driver"] = {"status": "working"}
        except Exception as e:
            test_results["chrome_driver"] = {"status": "failed", "error": str(e)}
        
        # Test Bali Exception scraper
        if test_results["chrome_driver"]["status"] == "working":
            try:
                with BaliExceptionScraper(headless=True, stealth_mode=True) as scraper:
                    # Try to get just the first few URLs
                    urls = scraper.scrape_all_urls(["for-sale"])
                    url_count = sum(len(urls) for urls in urls.values())
                    
                    test_results["bali_exception"] = {
                        "status": "working",
                        "urls_found": url_count
                    }
            except Exception as e:
                test_results["bali_exception"] = {"status": "failed", "error": str(e)}
        
        # Overall status
        if (test_results["chrome_driver"]["status"] == "working" and 
            test_results["bali_exception"]["status"] == "working"):
            test_results["overall"] = {"status": "all_systems_operational"}
        else:
            test_results["overall"] = {"status": "issues_detected"}
        
        return {
            "test_results": test_results,
            "timestamp": datetime.now().isoformat(),
            "recommendations": _get_test_recommendations(test_results)
        }
        
    except Exception as e:
        logger.error(f"Scraping capability test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_recent_logs(lines: int = 50):
    """Get recent application logs"""
    try:
        log_files = []
        
        # Look for log files in the workspace
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        for file in os.listdir(workspace_root):
            if file.endswith('.log'):
                log_files.append(os.path.join(workspace_root, file))
        
        if not log_files:
            return {"message": "No log files found", "logs": []}
        
        # Get the most recent log file
        latest_log = max(log_files, key=os.path.getmtime)
        
        # Read last N lines
        with open(latest_log, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "log_file": os.path.basename(latest_log),
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines),
            "logs": [line.strip() for line in recent_lines]
        }
        
    except Exception as e:
        logger.error(f"Log retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_test_recommendations(test_results: dict) -> list:
    """Generate recommendations based on test results"""
    recommendations = []
    
    if test_results["chrome_driver"]["status"] == "failed":
        recommendations.append("Chrome driver issues detected. Check Chrome installation and version compatibility.")
    
    if test_results["bali_exception"]["status"] == "failed":
        recommendations.append("Bali Exception scraper issues detected. Check website accessibility and scraper configuration.")
    
    if test_results["overall"]["status"] == "all_systems_operational":
        recommendations.append("All systems operational. Ready for production scraping.")
    
        return recommendations

@router.get("/sheets/info")
async def get_sheets_info():
    """Get Google Sheets configuration and available sheets"""
    try:
        from app.services.google_sheets_service import GoogleSheetsService
        
        sheets_service = GoogleSheetsService()
        
        if not sheets_service.gc or not sheets_service.sheet_id:
            return {
                "status": "not_configured",
                "message": "Google Sheets not configured",
                "sheets": []
            }
        
        # Get spreadsheet info
        spreadsheet = sheets_service.gc.open_by_key(sheets_service.sheet_id)
        worksheets = spreadsheet.worksheets()
        
        sheets_info = []
        for ws in worksheets:
            row_count = len(ws.get_all_values())
            sheets_info.append({
                "name": ws.title,
                "id": ws.id,
                "rows": row_count,
                "cols": ws.col_count,
                "url": f"https://docs.google.com/spreadsheets/d/{sheets_service.sheet_id}/edit#gid={ws.id}"
            })
        
        return {
            "status": "configured",
            "spreadsheet_id": sheets_service.sheet_id,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{sheets_service.sheet_id}",
            "total_sheets": len(sheets_info),
            "sheets": sheets_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get sheets info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sheets/create-competitor-sheet")
async def create_competitor_sheet(competitor_name: str):
    """Create a new sheet for a specific competitor"""
    try:
        from app.services.google_sheets_service import GoogleSheetsService
        
        sheets_service = GoogleSheetsService()
        
        if not sheets_service.gc or not sheets_service.sheet_id:
            raise HTTPException(status_code=400, detail="Google Sheets not configured")
        
        # Clean sheet name
        sheet_name = competitor_name.replace(" ", "_").replace(".", "_")
        
        # Open spreadsheet
        spreadsheet = sheets_service.gc.open_by_key(sheets_service.sheet_id)
        
        # Check if sheet already exists
        try:
            existing_sheet = spreadsheet.worksheet(sheet_name)
            return {
                "status": "exists",
                "sheet_name": sheet_name,
                "message": f"Sheet '{sheet_name}' already exists",
                "url": f"https://docs.google.com/spreadsheets/d/{sheets_service.sheet_id}/edit#gid={existing_sheet.id}"
            }
        except:
            # Sheet doesn't exist, create it
            new_sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=50)
            
            # Add headers for property data
            headers = [
                "title", "price", "location", "bedrooms", "bathrooms", 
                "area", "property_type", "description", "url", "images", 
                "scraped_at", "competitor"
            ]
            new_sheet.update('A1', [headers])
            
            return {
                "status": "created",
                "sheet_name": sheet_name,
                "sheet_id": new_sheet.id,
                "message": f"Successfully created sheet '{sheet_name}'",
                "url": f"https://docs.google.com/spreadsheets/d/{sheets_service.sheet_id}/edit#gid={new_sheet.id}"
            }
        
    except Exception as e:
        logger.error(f"Failed to create competitor sheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))