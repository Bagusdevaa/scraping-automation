import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import List, Dict, Any
import logging
import json
import math
import numpy as np
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
    
    def _sanitize_data(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sanitize data to ensure JSON compliance and Google Sheets compatibility"""
        sanitized_properties = []
        
        for prop in properties:
            sanitized_prop = {}
            for key, value in prop.items():
                try:
                    # Handle None values
                    if value is None:
                        sanitized_prop[key] = ""
                        continue
                    
                    # Handle numeric values (fix inf, -inf, NaN)
                    if isinstance(value, (int, float)):
                        if math.isnan(value) or math.isinf(value):
                            sanitized_prop[key] = ""  # Convert invalid numbers to empty string
                        else:
                            sanitized_prop[key] = value
                        continue
                    
                    # Handle numpy numeric types
                    if hasattr(value, 'dtype') and np.issubdtype(value.dtype, np.number):
                        if np.isnan(value) or np.isinf(value):
                            sanitized_prop[key] = ""
                        else:
                            sanitized_prop[key] = float(value) if '.' in str(value) else int(value)
                        continue
                    
                    # Handle lists and dicts (convert to string)
                    if isinstance(value, (list, dict)):
                        sanitized_prop[key] = str(value)
                        continue
                    
                    # Handle strings (ensure they're proper strings)
                    if isinstance(value, str):
                        # Remove any non-printable characters that might cause issues
                        sanitized_prop[key] = ''.join(char for char in value if char.isprintable() or char.isspace())
                        continue
                    
                    # For other types, convert to string
                    sanitized_prop[key] = str(value)
                    
                except Exception as e:
                    logger.warning(f"Error sanitizing field '{key}' with value '{value}': {e}")
                    sanitized_prop[key] = str(value) if value is not None else ""
            
            sanitized_properties.append(sanitized_prop)
        
        return sanitized_properties

    def save_properties(self, properties: List[Dict[str, Any]], sheet_name: str = "Properties"):
        """Save properties to Google Sheets"""
        try:
            if not self.gc or not self.sheet_id:
                logger.warning("Google Sheets not configured")
                return "Google Sheets not configured"
            
            # Sanitize data first to ensure JSON compliance
            logger.info(f"Sanitizing {len(properties)} properties for Google Sheets")
            sanitized_properties = self._sanitize_data(properties)
            
            # Open spreadsheet
            spreadsheet = self.gc.open_by_key(self.sheet_id)
            
            # Try to get existing worksheet or create new one
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=50)
            
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(sanitized_properties)
            
            # Additional DataFrame sanitization
            for col in df.columns:
                # Replace any remaining NaN, inf values in DataFrame
                df[col] = df[col].replace([float('inf'), float('-inf')], '')
                df[col] = df[col].fillna('')  # Replace NaN with empty string
                
                # Ensure all values are JSON serializable
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (list, dict)) else x)
            
            # Clear existing data
            worksheet.clear()
            
            # Prepare data for sheets (header + rows)
            headers = df.columns.tolist()
            data_rows = df.values.tolist()
            
            # Ensure all data is JSON serializable before sending
            sanitized_rows = []
            for row in data_rows:
                sanitized_row = []
                for cell in row:
                    if isinstance(cell, (float, int)) and (math.isnan(cell) if isinstance(cell, float) else False):
                        sanitized_row.append("")
                    elif isinstance(cell, float) and (math.isinf(cell)):
                        sanitized_row.append("")
                    else:
                        sanitized_row.append(cell)
                sanitized_rows.append(sanitized_row)
            
            all_data = [headers] + sanitized_rows
            
            # Update sheet
            worksheet.update('A1', all_data)
            
            logger.info(f"Successfully saved {len(sanitized_properties)} properties to sheet '{sheet_name}'")
            return f"Successfully saved {len(sanitized_properties)} properties to Google Sheets"
            
        except Exception as e:
            logger.error(f"Failed to save to Google Sheets: {e}")
            # Log more details for debugging
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
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