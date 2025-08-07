"""
Utility functions for safe data extraction and parsing
"""

import re
import math
from typing import Any, Union

def safe_float_parse(value: Any, default: float = 0.0) -> float:
    """Safely parse a value to float, handling edge cases"""
    if value is None:
        return default
    
    try:
        # Convert to string first to handle various input types
        str_value = str(value).strip()
        
        # Remove common currency symbols and separators
        str_value = re.sub(r'[,$€£¥₹]', '', str_value)
        str_value = str_value.replace(',', '').replace(' ', '')
        
        if not str_value or str_value == '':
            return default
        
        # Try to parse as float
        parsed_value = float(str_value)
        
        # Check for invalid values
        if math.isnan(parsed_value) or math.isinf(parsed_value):
            return default
        
        return parsed_value
        
    except (ValueError, TypeError):
        return default

def safe_int_parse(value: Any, default: int = 0) -> int:
    """Safely parse a value to int, handling edge cases"""
    if value is None:
        return default
    
    try:
        # Convert to string first
        str_value = str(value).strip()
        
        # Remove non-numeric characters except decimal point
        str_value = re.sub(r'[^\d.]', '', str_value)
        
        if not str_value or str_value == '':
            return default
        
        # Parse as float first, then convert to int
        float_value = float(str_value)
        
        if math.isnan(float_value) or math.isinf(float_value):
            return default
        
        return int(float_value)
        
    except (ValueError, TypeError):
        return default

def safe_string_parse(value: Any, default: str = "") -> str:
    """Safely parse a value to string, handling None and edge cases"""
    if value is None:
        return default
    
    try:
        # Convert to string and clean up
        str_value = str(value).strip()
        
        # Remove any non-printable characters that might cause JSON issues
        cleaned = ''.join(char for char in str_value if char.isprintable() or char.isspace())
        
        return cleaned if cleaned else default
        
    except Exception:
        return default

def extract_price_from_text(text: str, default: float = 0.0) -> float:
    """Extract price from text that might contain currency and formatting"""
    if not text:
        return default
    
    try:
        # Look for number patterns in the text
        # Matches patterns like: $1,500,000 or 1.500.000 or 1,500,000
        price_pattern = r'[\d,.\s]+(?:\.\d{2})?'
        matches = re.findall(price_pattern, text)
        
        if matches:
            # Get the largest number (assuming it's the price)
            prices = []
            for match in matches:
                cleaned = match.replace(',', '').replace(' ', '')
                try:
                    price = float(cleaned)
                    if not (math.isnan(price) or math.isinf(price)) and price > 0:
                        prices.append(price)
                except:
                    continue
            
            if prices:
                return max(prices)
    
    except Exception:
        pass
    
    return default

def extract_numbers_from_text(text: str, default: int = 0) -> int:
    """Extract the first number from text (useful for bedrooms, bathrooms, etc.)"""
    if not text:
        return default
    
    try:
        # Look for the first number in the text
        numbers = re.findall(r'\d+', str(text))
        if numbers:
            return safe_int_parse(numbers[0], default)
    except Exception:
        pass
    
    return default
