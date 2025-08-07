"""
Multi-competitor API routes for cross-platform operations
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from app.scrapers.baliExceptionScraper import BaliExceptionScraper
from app.services.google_sheets_service import GoogleSheetsService
from typing import List, Dict, Any
import logging
import asyncio
from datetime import datetime

router = APIRouter(prefix="/multi-competitor", tags=["Multi-Competitor"])
logger = logging.getLogger(__name__)

# Available competitors and their configurations
COMPETITORS = {
    "bali-exception": {
        "name": "Bali Exception",
        "scraper_class": BaliExceptionScraper,
        "categories": ["for-sale", "for-rent"],
        "enabled": True
    },
    # Future competitors will be added here
    # "airbnb": {
    #     "name": "Airbnb", 
    #     "scraper_class": AirbnbScraper,
    #     "categories": ["listings"],
    #     "enabled": False
    # },
    # "booking": {
    #     "name": "Booking.com",
    #     "scraper_class": BookingScraper, 
    #     "categories": ["hotels"],
    #     "enabled": False
    # }
}

@router.get("/competitors")
async def list_competitors():
    """List all available competitors and their status"""
    return {
        "total_competitors": len(COMPETITORS),
        "enabled_competitors": len([c for c in COMPETITORS.values() if c["enabled"]]),
        "competitors": {
            comp_id: {
                "name": config["name"],
                "categories": config["categories"],
                "enabled": config["enabled"]
            }
            for comp_id, config in COMPETITORS.items()
        }
    }

@router.get("/competitors/{competitor_id}/info")
async def get_competitor_details(competitor_id: str):
    """Get detailed information about a specific competitor"""
    if competitor_id not in COMPETITORS:
        raise HTTPException(
            status_code=404, 
            detail=f"Competitor '{competitor_id}' not found. Available: {list(COMPETITORS.keys())}"
        )
    
    config = COMPETITORS[competitor_id]
    return {
        "competitor_id": competitor_id,
        "name": config["name"],
        "categories": config["categories"],
        "enabled": config["enabled"],
        "scraper_available": config["enabled"]
    }

@router.post("/scrape-all")
async def scrape_all_competitors(
    competitors: List[str] = Query(default=None, description="Specific competitors to scrape (all enabled if not specified)"),
    max_properties_per_competitor: int = 20,
    save_to_sheets: bool = False,
    background_tasks: BackgroundTasks = None
):
    """Scrape properties from multiple competitors simultaneously"""
    
    # Determine which competitors to scrape
    if competitors is None:
        target_competitors = [comp_id for comp_id, config in COMPETITORS.items() if config["enabled"]]
    else:
        # Validate requested competitors
        invalid_competitors = [comp for comp in competitors if comp not in COMPETITORS]
        if invalid_competitors:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid competitors: {invalid_competitors}. Available: {list(COMPETITORS.keys())}"
            )
        
        disabled_competitors = [comp for comp in competitors if not COMPETITORS[comp]["enabled"]]
        if disabled_competitors:
            raise HTTPException(
                status_code=400,
                detail=f"Disabled competitors: {disabled_competitors}. Enable them first."
            )
        
        target_competitors = competitors
    
    if not target_competitors:
        raise HTTPException(status_code=400, detail="No enabled competitors available")
    
    logger.info(f"Starting multi-competitor scraping: {target_competitors}")
    
    results = {}
    total_properties = 0
    start_time = datetime.now()
    
    # Scrape each competitor
    for competitor_id in target_competitors:
        try:
            logger.info(f"Scraping competitor: {competitor_id}")
            
            config = COMPETITORS[competitor_id]
            scraper_class = config["scraper_class"]
            categories = config["categories"]
            
            # Currently only Bali Exception is implemented
            if competitor_id == "bali-exception":
                with scraper_class(headless=True, stealth_mode=True) as scraper:
                    # Get URLs for all categories
                    urls_dict = scraper.scrape_all_urls(categories)
                    
                    # Flatten URLs with category tracking
                    all_urls_with_category = []
                    for category, urls in urls_dict.items():
                        for url in urls:
                            all_urls_with_category.append((url, category))
                    
                    # Limit properties
                    properties_to_scrape = min(len(all_urls_with_category), max_properties_per_competitor)
                    
                    # Scrape details
                    competitor_properties = []
                    for i, (url, category) in enumerate(all_urls_with_category[:max_properties_per_competitor]):
                        details_list = scraper.scrape_property_details([url], category)
                        if details_list:
                            competitor_properties.extend(details_list)
                    
                    # Get summary
                    summary = scraper.get_scraping_summary()
                    
                    results[competitor_id] = {
                        "name": config["name"],
                        "categories_processed": categories,
                        "total_urls_found": len(all_urls_with_category),
                        "properties_scraped": len(competitor_properties),
                        "properties": competitor_properties,
                        "performance": {
                            "success_rate": f"{summary['success_rate']:.1f}%",
                            "total_errors": summary["error_count"],
                            "scraping_time": summary.get("total_time", "N/A")
                        }
                    }
                    
                    total_properties += len(competitor_properties)
            
        except Exception as e:
            logger.error(f"Error scraping {competitor_id}: {e}")
            results[competitor_id] = {
                "name": COMPETITORS[competitor_id]["name"],
                "error": str(e),
                "properties_scraped": 0,
                "properties": []
            }
    
    # Save to Google Sheets if requested
    sheets_results = {}
    if save_to_sheets:
        try:
            sheets_service = GoogleSheetsService()
            
            # Save each competitor to separate sheet
            for competitor_id, result in results.items():
                if "properties" in result and result["properties"]:
                    competitor_name = result["name"]
                    properties = result["properties"]
                    
                    # Create clean sheet name (remove special characters)
                    sheet_name = competitor_name.replace(" ", "_").replace(".", "_")
                    
                    try:
                        sheet_result = sheets_service.save_properties(properties, sheet_name)
                        sheets_results[competitor_id] = {
                            "sheet_name": sheet_name,
                            "status": "success",
                            "message": sheet_result,
                            "properties_saved": len(properties)
                        }
                        logger.info(f"Saved {len(properties)} properties for {competitor_name} to sheet '{sheet_name}'")
                    except Exception as e:
                        sheets_results[competitor_id] = {
                            "sheet_name": sheet_name,
                            "status": "error", 
                            "message": str(e),
                            "properties_saved": 0
                        }
                        logger.error(f"Failed to save {competitor_name} to sheet: {e}")
            
            # Also save combined data to "All_Competitors" sheet
            all_properties = []
            for result in results.values():
                if "properties" in result:
                    # Add competitor info to each property
                    for prop in result["properties"]:
                        prop_with_competitor = prop.copy()
                        prop_with_competitor["competitor"] = result["name"]
                        all_properties.append(prop_with_competitor)
            
            if all_properties:
                try:
                    combined_result = sheets_service.save_properties(all_properties, "All_Competitors")
                    sheets_results["all_competitors"] = {
                        "sheet_name": "All_Competitors",
                        "status": "success",
                        "message": combined_result,
                        "properties_saved": len(all_properties)
                    }
                except Exception as e:
                    sheets_results["all_competitors"] = {
                        "sheet_name": "All_Competitors", 
                        "status": "error",
                        "message": str(e),
                        "properties_saved": 0
                    }
                    
        except Exception as e:
            logger.error(f"Google Sheets service initialization failed: {e}")
            sheets_results = {"error": f"Service initialization failed: {e}"}
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    response = {
        "operation": "multi-competitor-scrape",
        "timestamp": start_time.isoformat(),
        "competitors_processed": len(target_competitors),
        "total_properties_scraped": total_properties,
        "total_time_seconds": total_time,
        "results_by_competitor": results
    }
    
    if sheets_results:
        response["google_sheets"] = {
            "enabled": True,
            "sheets_created": len([r for r in sheets_results.values() if isinstance(r, dict) and r.get("status") == "success"]),
            "results_by_competitor": sheets_results,
            "summary": {
                "total_sheets": len(sheets_results),
                "successful_saves": len([r for r in sheets_results.values() if isinstance(r, dict) and r.get("status") == "success"]),
                "failed_saves": len([r for r in sheets_results.values() if isinstance(r, dict) and r.get("status") == "error"])
            }
        }
    
    return response

@router.post("/compare-properties")
async def compare_properties_across_competitors(
    competitors: List[str] = Query(default=None, description="Competitors to compare"),
    max_properties_per_competitor: int = 10,
    comparison_fields: List[str] = Query(default=["price", "location", "bedrooms"], description="Fields to compare")
):
    """Compare properties across multiple competitors"""
    
    # First scrape from all competitors
    scrape_result = await scrape_all_competitors(
        competitors=competitors,
        max_properties_per_competitor=max_properties_per_competitor,
        save_to_sheets=False
    )
    
    # Extract properties for comparison
    comparison_data = {}
    for competitor_id, result in scrape_result["results_by_competitor"].items():
        if "properties" in result and result["properties"]:
            comparison_data[competitor_id] = {
                "name": result["name"],
                "property_count": len(result["properties"]),
                "sample_properties": result["properties"][:5],  # Show first 5 for comparison
                "avg_metrics": _calculate_avg_metrics(result["properties"], comparison_fields)
            }
    
    return {
        "operation": "property-comparison",
        "comparison_fields": comparison_fields,
        "competitors_compared": len(comparison_data),
        "comparison_data": comparison_data,
        "summary": {
            "total_properties": sum(data["property_count"] for data in comparison_data.values()),
            "competitors": list(comparison_data.keys())
        }
    }

def _calculate_avg_metrics(properties: List[Dict[str, Any]], fields: List[str]) -> Dict[str, Any]:
    """Calculate average metrics for comparison"""
    metrics = {}
    
    for field in fields:
        values = []
        for prop in properties:
            if field in prop and prop[field] is not None:
                try:
                    # Try to convert to number for averaging
                    if isinstance(prop[field], (int, float)):
                        values.append(prop[field])
                    elif isinstance(prop[field], str) and prop[field].replace('.', '').replace(',', '').isdigit():
                        values.append(float(prop[field].replace(',', '')))
                except:
                    pass
        
        if values:
            metrics[f"avg_{field}"] = sum(values) / len(values)
            metrics[f"min_{field}"] = min(values)
            metrics[f"max_{field}"] = max(values)
        else:
            metrics[f"avg_{field}"] = "N/A"
    
    return metrics
