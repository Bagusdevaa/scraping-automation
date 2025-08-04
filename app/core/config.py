from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Property Scraper"
    DEBUG: bool = False
    
    # Google Sheets settings
    GOOGLE_SHEETS_CREDENTIALS_JSON: Optional[str] = None
    GOOGLE_SHEETS_CREDENTIALS_FILE: Optional[str] = None 
    GOOGLE_SHEET_ID: Optional[str] = None
    
    # Scraping settings
    SCRAPING_TIMEOUT: int = 60
    MAX_RETRIES: int = 5
    HEADLESS_MODE: bool = False # for local debugging

    # GOOGLE_SHEETS_CREDENTIALS_JSON: Optional[str] = None
    # GOOGLE_SHEET_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()