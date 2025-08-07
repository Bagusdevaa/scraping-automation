"""
Main API routes - imports and registers all route modules
"""

from fastapi import APIRouter
from app.api.routes import bali_exception, multi_competitor, system

# Create main router
router = APIRouter()

# Include all route modules
router.include_router(bali_exception.router)
router.include_router(multi_competitor.router)
router.include_router(system.router)

# Legacy compatibility - redirect root endpoints to new structure
@router.get("/")
async def root():
    """API root with navigation to new route structure"""
    return {
        "message": "Scraping Automation API v2.0",
        "documentation": "/docs",
        "routes": {
            "bali_exception": "/bali-exception/*",
            "multi_competitor": "/multi-competitor/*", 
            "system": "/system/*"
        },
        "migration_note": "Legacy endpoints have been restructured. See /docs for updated API."
    }

# Health check endpoint
@router.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy", "version": "2.0"}
