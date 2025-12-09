import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def test_imports():
    from weflow.core.rss import MeituanRSS
    from weflow.core.crawler import FirecrawlCrawler
    from weflow.core.llm import DeepSeekLLM
    from weflow.core.storage import PostgresStorage
    from weflow.core.image import MockImageProvider, QwenImageProvider, GeminiImageProvider
    from weflow.core.wechat import WeChatPublisher
    from weflow.core.models import Article
    
    print("All imports successful.")
    
    a = Article(title="Test", url="http://example.com")
    assert a.title == "Test"
    print("Article model verified.")

if __name__ == "__main__":
    test_imports()
