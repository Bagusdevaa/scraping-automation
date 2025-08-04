from abc import ABC, abstractmethod
from typing import List, Dict, Any
from bs4 import BeautifulSoup

class BaseExtractor(ABC):
    """Abstract base class for category-specific extraction logic"""
    
    @abstractmethod
    def extract_urls_from_page(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract property URLs from listing page"""
        pass
    
    @abstractmethod
    def navigate_to_next_page(self, driver, current_page: int) -> bool:
        """Navigate to next page"""
        pass
    
    @abstractmethod
    def extract_property_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract property details from detail page"""
        pass
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Get base URL for this category"""
        pass
    
    @abstractmethod
    def get_endpoint(self) -> str:
        """Get endpoint for this category"""
        pass