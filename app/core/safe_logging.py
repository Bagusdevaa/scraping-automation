"""
Logging utilities for Windows-safe logging
"""

import re
import logging

def safe_log_message(message: str) -> str:
    """
    Convert log message to Windows console-safe format
    Replaces Unicode emojis and special characters with ASCII equivalents
    """
    emoji_replacements = {
        '✅': '[SUCCESS]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]', 
        '🧪': '[TEST]',
        '🎯': '[TARGET]',
        '📊': '[STATS]',
        '🔧': '[TOOL]',
        'ℹ️': '[INFO]',
        '🚀': '[LAUNCH]',
        '🔍': '[SEARCH]',
        '💾': '[SAVE]',
        '⏱️': '[TIME]',
        '🌐': '[WEB]',
        '📋': '[LIST]',
        '🎉': '[COMPLETE]',
        '🏠': '[HOME]',
        '⚙️': '[CONFIG]'
    }
    
    safe_message = str(message)
    
    # Replace emojis
    for emoji, replacement in emoji_replacements.items():
        safe_message = safe_message.replace(emoji, replacement)
    
    # Remove any remaining non-ASCII characters that might cause issues
    # Keep common accented characters but remove problematic Unicode
    safe_message = re.sub(r'[^\x00-\x7F\u00C0-\u017F]', '?', safe_message)
    
    return safe_message

class SafeLogger:
    """
    Wrapper for logging that ensures Windows console compatibility
    """
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
    
    def info(self, message: str):
        """Safe info logging"""
        self.logger.info(safe_log_message(message))
    
    def warning(self, message: str):
        """Safe warning logging"""
        self.logger.warning(safe_log_message(message))
    
    def error(self, message: str):
        """Safe error logging"""
        self.logger.error(safe_log_message(message))
    
    def debug(self, message: str):
        """Safe debug logging"""
        self.logger.debug(safe_log_message(message))
    
    def critical(self, message: str):
        """Safe critical logging"""
        self.logger.critical(safe_log_message(message))

def get_safe_logger(name: str) -> SafeLogger:
    """Get a Windows-safe logger instance"""
    return SafeLogger(name)
