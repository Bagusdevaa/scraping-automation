from pydantic import BaseModel
from typing import Optional, List

class ScrapingResponse(BaseModel):
    job_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    status: str
    progress: int = 0
    total_urls: int = 0
    scraped_properties: int = 0
    message: str

class PropertyResponse(BaseModel):
    urls: List[str]
    total_count: int
    message: str