from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class Article(BaseModel):
    title: str
    url: str
    published_date: Optional[str] = None
    source_name: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    media_id: Optional[str] = None  # WeChat media ID
    status: str = "pending" # pending, crawled, summarized, image_generated, uploaded, published
