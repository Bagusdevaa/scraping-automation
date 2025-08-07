import logging
import sys
import io
from datetime import datetime

def setup_logging():
    """Setup logging configuration with Unicode support"""
    
    # Create handlers with explicit UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # For Windows, use UTF-8 encoding explicitly
    file_handler = logging.FileHandler(
        f'scraping_{datetime.now().strftime("%Y%m%d")}.log', 
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Create formatter that handles Unicode properly
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add new handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set specific loggers to reduce noise
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("gspread").setLevel(logging.WARNING)
    
    # Test Unicode logging
    logger = logging.getLogger(__name__)
    logger.info("Logging setup complete with Unicode support")