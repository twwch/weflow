from abc import ABC, abstractmethod
from typing import List
import feedparser
from datetime import datetime
import time
from .models import Article

class RSSProvider(ABC):
    @abstractmethod
    def fetch_articles(self) -> List[Article]:
        pass

class GenericRSS(RSSProvider):
    def __init__(self, url: str, source_name: str = "Unknown"):
        self.url = url
        self.source_name = source_name

    def fetch_articles(self) -> List[Article]:
        print(f"Fetching RSS from: {self.url}")
        feed = feedparser.parse(self.url)
        articles = []
        for entry in feed.entries:
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = time.strftime("%Y-%m-%d", entry.published_parsed)
            
            articles.append(Article(
                title=entry.title,
                url=entry.link,
                published_date=published_date
            ))
        return articles

class MeituanRSS(GenericRSS):
    def __init__(self):
        super().__init__("https://tech.meituan.com/feed/", "Meituan Tech")
