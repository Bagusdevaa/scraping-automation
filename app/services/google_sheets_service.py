import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import List, Dict, Any
import logging
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.gc = None
        self.sheet_id = settings.GOOGLE_SHEET_ID
        self._setup_client()
    
    def _setup_client(self):
        """Setup Google Sheets client"""
        try:
            logger.info(f"Sheet ID configured: {bool(settings.GOOGLE_SHEET_ID)}")
            logger.info(f"Credentials JSON configured: {bool(settings.GOOGLE_SHEETS_CREDENTIALS_JSON)}")
            logger.info(f"Credentials File configured: {bool(settings.GOOGLE_SHEETS_CREDENTIALS_FILE)}")
            scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            if settings.GOOGLE_SHEETS_CREDENTIALS_JSON:
                # JSON method
                creds_info = json.loads(settings.GOOGLE_SHEETS_CREDENTIALS_JSON)
                credentials = Credentials.from_service_account_info(creds_info, scopes=...)
            elif settings.GOOGLE_SHEETS_CREDENTIALS_FILE:
                credentials = Credentials.from_service_account_file(
                    settings.GOOGLE_SHEETS_CREDENTIALS_FILE, 
                    scopes = scopes
                )
            else:
                logger.warning("Google Sheets credentials not configured")
                return
                
            self.gc = gspread.authorize(credentials)
        except Exception as e:
            logger.error(f"Failed to setup Google Sheets: {e}")
    
    def save_properties(self, properties: List[Dict[str, Any]], sheet_name: str = "Properties"):
        """Save properties to Google Sheets"""
        try:
            if not self.gc or not self.sheet_id:
                logger.warning("Google Sheets not configured")
                return "Google Sheets not configured"
            
            # Open spreadsheet
            spreadsheet = self.gc.open_by_key(self.sheet_id)
            
            # Try to get existing worksheet or create new one
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=50)
            
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(properties)
            
            # Flatten complex fields (lists, dicts) to strings
            for col in df.columns:
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare data for sheets (header + rows)
            all_data = [df.columns.tolist()] + df.values.tolist()
            
            # Update sheet
            worksheet.update('A1', all_data)
            
            logger.info(f"Saved {len(properties)} properties to sheet '{sheet_name}'")
            return f"Successfully saved {len(properties)} properties to Google Sheets"
            
        except Exception as e:
            logger.error(f"Failed to save to Google Sheets: {e}")
            raise Exception(f"Failed to save to Google Sheets: {e}")
    
    def append_properties(self, properties: List[Dict[str, Any]], sheet_name: str = "Properties"):
        """Append properties to existing sheet data"""
        try:
            spreadsheet = self.gc.open_by_key(self.sheet_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Convert to DataFrame
            df = pd.DataFrame(properties)
            
            # Flatten complex fields
            for col in df.columns:
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)
            
            # Append rows
            for _, row in df.iterrows():
                worksheet.append_row(row.tolist())
            
            logger.info(f"Appended {len(properties)} properties to sheet '{sheet_name}'")
            return f"Successfully appended {len(properties)} properties"
            
        except Exception as e:
            logger.error(f"Failed to append to Google Sheets: {e}")
            raise Exception(f"Failed to append to Google Sheets: {e}")