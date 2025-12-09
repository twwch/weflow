from abc import ABC, abstractmethod
import os
import requests
from typing import Optional

class CrawlerProvider(ABC):
    @abstractmethod
    def crawl(self, url: str) -> Optional[str]:
        """Returns the markdown or text content of the page"""
        pass

class FirecrawlCrawler(CrawlerProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API key is required")
        self.base_url = "https://api.firecrawl.dev/v0/scrape"

    def crawl(self, url: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "pageOptions": {
                "onlyMainContent": True
            }
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Firecrawl v0 implementation usually returns markdown in `markdown` field or data object
            # Adjusting structure based on common firecrawl response patterns, verify if needed
            return data.get("data", {}).get("markdown") or data.get("markdown")
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None
