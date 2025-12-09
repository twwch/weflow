import os
import time
import re
import json
from collections import defaultdict
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime, timedelta

# Load environment variables
env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(dotenv_path=env_path, override=True)

from weflow.core.rss import GenericRSS
from weflow.core.crawler import FirecrawlCrawler
from weflow.core.llm import DeepSeekLLM
from weflow.core.image import MockImageProvider, QwenImageProvider, GeminiImageProvider
from weflow.core.storage import PostgresStorage
from weflow.core.wechat import WeChatPublisher
from weflow.core.formatter import WeChatFormatter
from weflow.core.vision import QwenVisionProvider, MockVisionProvider
from weflow.core.notifier import FeishuNotifier

DEFAULT_RSS_FEEDS = [
    "https://openai.com/blog/rss.xml",
    "http://bair.berkeley.edu/blog/feed.xml", # BAIR
    "https://deepmind.com/blog/feed/basic/", # DeepMind
    "https://distill.pub/rss.xml", # Distill
    "https://www.technologyreview.com/feed/", # MIT Tech Review
    "https://huggingface.co/blog/feed.xml", # Hugging Face
    "https://www.ai-shift.co.jp/techblog/feed", # AI Shift
    "https://ethicsandsociety.org/feed", # Ethics
    "https://thegradient.pub/rss/", # The Gradient
    "https://machinelearningmastery.com/feed/", # ML Mastery
    "https://kdnuggets.com/feed",
    "https://www.artificialintelligence-news.com/feed/rss/"
]

def extract_image_urls(markdown_content: str) -> list[str]:
    if not markdown_content:
        return []
    return re.findall(r'!\[.*?\]\((.*?)\)', markdown_content)

def crawl_article(article, crawler, storage):
    """Step 1: Crawl single article"""
    try:
        # Check storage
        if storage.article_exists(article.url):
             # For now, skip re-crawling if exists, but we need the content for analysis
             pass

        content = crawler.crawl(article.url)
        if not content:
            return None
        article.content = content
        article.status = "crawled"
        storage.save_article(article)
        return article
    except Exception as e:
        print(f"Error crawling {article.title}: {e}")
        return None

def analyze_article(article, llm):
    """Step 2: Analyze topic and relevance"""
    if not article.content:
        return None
    
    try:
        # analyze returns JSON string
        analysis_json = llm.analyze(article.content)
        data = json.loads(analysis_json)
        
        # Attach analysis to article object (dynamically)
        article.analysis = data
        return article
    except Exception as e:
        print(f"Error analyzing {article.title}: {e}")
        return None

def synthesize_topic(topic, articles, llm, image_gen, vision, wechat, storage, used_images):
    """Step 3: Synthesize report for a topic cluster (Markdown + Multimodal)"""
    print(f"Synthesizing topic: {topic} ({len(articles)} articles)...")
    
    # Prepare data for LLM
    articles_data = []
    image_candidates = [] # list of {url, description}
    
    for art in articles:
        articles_data.append({
            "title": art.title,
            "source_name": getattr(art, 'source_name', 'Unknown Source'),
            "content": art.content
        })
        # Extract images
        imgs = extract_image_urls(art.content)
        for img_url in imgs:
            if not img_url.startswith("http"): continue
            
            # Global Deduplication check
            if img_url in used_images:
                continue
            
            used_images.add(img_url)
            
            # Limit to top 2 images per article to save time/cost
            if len(image_candidates) >= 5: break
            
            print(f"Analyzing image: {img_url}")
            desc = vision.describe_image(img_url)
            if desc:
                image_candidates.append({"url": img_url, "description": desc})
                print(f"-> Desc: {desc[:50]}...")

    # Synthesize (Markdown)
    report_md = llm.synthesize_report(articles_data, topic, images=image_candidates)
    
    # Process Images in Markdown: Download and Upload to WeChat
    def replace_image_url(match):
        alt = match.group(1)
        original_url = match.group(2)
        try:
            print(f"Uploading embedded image to WeChat: {original_url}")
            new_url = wechat.upload_article_image(original_url)
            return f"![{alt}]({new_url})"
        except Exception as e:
            print(f"Failed to upload embedded image {original_url}: {e}")
            return match.group(0) # Keep original if failed

    # Find all images and replace
    report_md = re.sub(r'!\[(.*?)\]\((http.*?)\)', replace_image_url, report_md)
    
    # Image Strategy for Topic Header
    wechat_header_url = None
    for img_obj in image_candidates:
        img_url = img_obj['url']
        # Check against body images to avoid duplicate visual
        if img_url in report_md or wechat.upload_article_image(img_url) in report_md:
             continue 

        try:
            wechat_header_url = wechat.upload_article_image(img_url)
            if wechat_header_url:
                print(f"[{topic}] Using original image for header: {img_url}")
                break
        except:
            continue
            
    # Fallback to AI for header image if no suitable original found
    if not wechat_header_url:
        print(f"[{topic}] Generating AI illustration for header...")
        try:
            gen_url = image_gen.generate_image(f"Abstract tech illustration for {topic}: {articles[0].title}")
            wechat_header_url = wechat.upload_article_image(gen_url)
        except Exception as e:
            print(f"[{topic}] Image generation for header failed: {e}")
            wechat_header_url = "https://via.placeholder.com/600x300?text=No+Image" # Placeholder if AI fails too
            
    return report_md, wechat_header_url


from weflow.core.notifier import FeishuNotifier

def main():
    print("Starting WeFlow Service (Advanced Synthesis Mode)...")
    
    # Init Components
    try:
        crawler = FirecrawlCrawler() if os.getenv("FIRECRAWL_API_KEY") else None
        llm = DeepSeekLLM() if os.getenv("DEEPSEEK_API_KEY") else None
        storage = PostgresStorage() if os.getenv("DATABASE_URL") else None
        wechat = WeChatPublisher() if os.getenv("WECHAT_APP_ID") else None
        notifier = FeishuNotifier()
        
        image_provider_name = os.getenv("IMAGE_PROVIDER", "mock").lower()
        if image_provider_name == "qwen":
            image_gen = QwenImageProvider()
        elif image_provider_name == "gemini":
            image_gen = GeminiImageProvider()
        else:
            image_gen = MockImageProvider()
        
        # Init Vision
        if os.getenv("DASHSCOPE_API_KEY"):
            vision = QwenVisionProvider()
        else:
            vision = MockVisionProvider()

    except Exception as e:
        print(f"Init failed: {e}")
        return

    if not all([crawler, llm, storage, wechat]):
        print("Missing config (check .env).")
        return
        
    # RSS Feeds
    env_feeds = os.getenv("RSS_FEEDS", "")
    feed_urls = env_feeds.split(",") if env_feeds else DEFAULT_RSS_FEEDS
    rss_providers = [GenericRSS(url=url.strip()) for url in feed_urls if url.strip()]
    
    # 1. Fetch All Articles
    print("Fetching articles...")
    all_articles = []
    for rss in rss_providers:
        try:
            from urllib.parse import urlparse
            domain = urlparse(rss.url).netloc
            
            arts = rss.fetch_articles()
            for a in arts:
                a.source_name = domain 
            all_articles.extend(arts)
        except Exception as e:
            print(f"Error fetching {rss.url}: {e}")
            
    
    json.dump([a.__dict__ for a in all_articles], open("articles.json", "w"), indent=2, ensure_ascii=False)

    # Filter for yesterday
    today_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_articles = [a for a in all_articles if a.published_date == today_str]
    
    is_fallback = False
    if not today_articles:
        print("No articles for today. Switching to Fallback Strategy (Recent 20)...")
        # Fallback: take top 20 recent articles
        today_articles = all_articles[:20]
        is_fallback = True
    
    if not today_articles:
        print("No articles found even with fallback.")
        return
        
    print(f"Creating pipeline for {len(today_articles)} articles (Fallback: {is_fallback})...")
    
    # 2. Crawl & Analyze (Parallel)
    crawled_articles = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Step 2a: Crawl
        future_crawl = {executor.submit(crawl_article, a, crawler, storage): a for a in today_articles}
        for f in tqdm(as_completed(future_crawl), total=len(future_crawl), desc="Crawling"):
            res = f.result()
            if res: crawled_articles.append(res)
            
    analyzed_articles = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Step 2b: Analyze
        future_analyze = {executor.submit(analyze_article, a, llm): a for a in crawled_articles}
        for f in tqdm(as_completed(future_analyze), total=len(future_analyze), desc="Analyzing"):
            res = f.result()
            if res: analyzed_articles.append(res)
            
    # 3. Clustering
    TOPIC_MAP = {
        "Generative AI": "生成式 AI",
        "Robotics": "机器人技术",
        "Hardware/Chips": "芯片与硬件",
        "Industry/Business": "产业动态",
        "Programming/Dev": "编程与开发",
        "Science/Research": "科研前沿",
        "Agi/Safety": "AGI 与安全",
        "Other": "其他"
    }

    clusters = defaultdict(list)
    for art in analyzed_articles:
        if not hasattr(art, 'analysis') or not art.analysis:
            continue
            
        if not art.analysis.get('recommended'):
            print(f"Skipping noise: {art.title} ({art.analysis.get('reason')})")
            continue
            
        raw_topic = art.analysis.get('topic', 'Other')
        # Map to Chinese immediately
        topic = TOPIC_MAP.get(raw_topic, raw_topic)
        clusters[topic].append(art)
        
    print(f"Formed {len(clusters)} clusters: {list(clusters.keys())}")
    
    if not clusters:
        print("No relevant clusters found.")
        return

    # 4. Synthesize & Image & Format (Parallel by Topic)
    md_segments = []
    header_maps = {} # {topic: wechat_img_url}
    used_images = set() # Track used images to prevent duplicates across topics
    
    for topic, arts in tqdm(clusters.items(), desc="Synthesizing"):
        try:
             # Run synthesis sequentially to handle image dedupe correctly
            report_md, wechat_header_url = synthesize_topic(topic, arts, llm, image_gen, vision, wechat, storage, used_images)
            md_segments.append((topic, report_md, arts)) # Store articles for source links
            header_maps[topic] = wechat_header_url
        except Exception as e:
            print(f"Synthesis failed for {topic}: {e}")

    if not md_segments:
        print("No sections generated.")
        return
        
    # Combine all markdown segments
    combined_md_sections = []
    all_source_articles = []
    for topic, md_content, articles_in_topic in md_segments:
        section_md = f"## {topic}\n\n"
        if topic in header_maps and header_maps[topic]:
            section_md += f"![Header]({header_maps[topic]})\n\n"
        section_md += md_content
        combined_md_sections.append(section_md)
        all_source_articles.extend(articles_in_topic)

    combined_md = "\n\n".join(combined_md_sections)

    # Unify the daily digest with LLM
    print("Unifying daily digest with LLM...")
    unified_md = llm.unify_daily_digest(combined_md)

    # Convert unified MD to HTML
    report_html = WeChatFormatter.markdown_to_html(unified_md)

    # Add Source Links
    source_links_html = "<div style='margin-top:20px; font-size:12px; color:#999;'>Sources:<br>"
    for art in all_source_articles:
        source_links_html += f"<a href='{art.url}' style='color:#999; margin-right:10px; text-decoration: none;'>• {art.title}</a><br>"
    source_links_html += "</div>"
    
    final_html = report_html + source_links_html
    
    # Aggregate
    author_name = os.getenv("WECHAT_AUTHOR", "")
    full_html = WeChatFormatter.wrap_full_article(final_html, today_str, author=author_name)
    
    # Cover Image
    print("Generating cover...")
    try:
        topic_list = ", ".join(clusters.keys())
        cover_url = image_gen.generate_image(f"Futuristic collage for topics: {topic_list}")
        media_id = wechat.upload_image(cover_url)
        
        # Generate AI Title (Always, even for fallback)
        try:
             ai_title = llm.generate_digest_title(list(clusters.keys()))
             title = f"{ai_title} | WeFlow Daily"
        except:
             title = f"WeFlow Daily - {today_str}"
        
        res = wechat.push_draft(
            title=title,
            summary=f"Topics: {topic_list}",
            media_id=media_id,
            content=full_html,
            source_url="",
            author=author_name
        )
        print(f"Draft pushed: {res}")
        
        # Notify Feishu with real draft URL
        if res:
             draft_info = wechat.get_draft(res) if res != "Success" else None
             article_url = draft_info.get("url") if draft_info else "https://mp.weixin.qq.com"
             
             # Use AI Title and Topic List for summary
             s = f"Topics: {topic_list}"
             
             notifier.send_card(
                 title=title, 
                 summary=s, 
                 article_url=article_url 
             )

    except Exception as e:
        print(f"Push failed: {e}")

if __name__ == "__main__":
    main()
