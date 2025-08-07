from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from app.api.routes_new import router
from app.core.config import settings
from app.core.logging_config import setup_logging
import uvicorn
import os

# Fix Windows console encoding issues
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup logging with Unicode support
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Multi-Competitor Property Scraping API",
    description="Automated property scraping service for multiple competitors",
    version="2.0.0"
)

# Include routers
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Property Scraping API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "property-scraper"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )