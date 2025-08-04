# app/scrapers/configs/scraper_config.py
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ScrapingEndpoint:
    name: str
    url: str
    category: str
    css_selectors: Dict[str, str]
    pagination_config: Dict[str, str]

class ScraperConfig:
    def __init__(self):
        self.configs = {
            "bali_exception": {
                "base_url": "https://baliexception.com",
                "endpoints": [
                    ScrapingEndpoint(
                        name="for_sale",
                        url="/properties",
                        category="for-sale",
                        css_selectors={
                            "property_cards": "h2.brxe-gzgohv.brxe-heading.propertyCard__title a",
                            "next_button": ".jet-filters-pagination__item[data-value=\"{page}\"]"
                        },
                        pagination_config={"type": "numbered"}
                    ),
                    ScrapingEndpoint(
                        name="for_rent", 
                        url="/properties?listing-type=for-rent",
                        category="for-rent",
                        css_selectors={
                            "property_cards": "h2.brxe-gzgohv.brxe-heading.propertyCard__title a",
                            "next_button": ".jet-filters-pagination__item[data-value=\"{page}\"]"
                        },
                        pagination_config={"type": "numbered"}
                    )
                ]
            }
            # "betterplace": {
            #     "base_url": "https://betterplace.cc", 
            #     "endpoints": [
            #         ScrapingEndpoint(
            #             name="sale",
            #             url="/properties/sale",
            #             category="sale",
            #             css_selectors={...},
            #             pagination_config={...}
            #         ),
            #         ScrapingEndpoint(
            #             name="rent",
            #             url="/properties/rent", 
            #             category="rent",
            #             css_selectors={...},
            #             pagination_config={...}
            #         )
            #     ]
            # }
        }
    
    def get_scraper_config(self, scraper_name: str):
        return self.configs.get(scraper_name, {})