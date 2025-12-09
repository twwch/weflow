# WeFlow

A Python SDK to automate the content workflow: identifying trending articles, crawling content, summarizing with AI, generating matching illustrations, and publishing drafts to WeChat Official Accounts.

## Features

- **Multimodal Intelligence**: 
    - **Vision Analysis**: Uses **Qwen-VL** to "see" and describe images from source articles.
    - **AI Illustrations**: Generates cover images via **Qwen (Wanx)** or **Gemini (Imagen)**.
- **Unified Daily Digest**: 
    - **Tech Crunch Style**: Aggregates multiple articles into a single, cohesive narrative with smooth transitions.
    - **AI Title Generation**: Creates professional, catchy titles daily.
- **Robust Publishing**:
    - **Host-First Images**: Automatically downloads original images and uploads them to WeChat to ensure valid hotlinking.
    - **Deduplication**: Global tracking prevents image repetition across the digest.
- **Smart Notifications**:
    - **Feishu Webhook**: Sends a status card to your Feishu group upon successful push.

## Architecture Overview

```mermaid
graph TD
    RSS[RSS Sources] -->|Fetch| Fetcher[Fetcher Service]
    Fetcher -->|URLs| DB[(PostgreSQL)]
    Fetcher -->|New Articles| Crawler[Firecrawl Scraper]
    Crawler -->|Markdown| Analyzer[LLM Analyzer]
    Analyzer -->|Topics| Cluster[Topic Clusterer]
    
    subgraph "Multimodal Synthesis"
        Cluster -->|Img URLs| Vision[Qwen-VL Vision]
        Vision -->|Descriptions| Synthesizer[DeepSeek Unifier]
        Cluster -->|Content| Synthesizer
        Synthesizer -->|Unified Draft| Formatter[WeChat Formatter]
    end
    
    Formatter -->|Assets| Uploader[WeChat Uploader]
    Uploader -->|Push| MP[WeChat Official Account]
    MP -.->|Callback| Feishu[Feishu Notification]
```

## RSS Configuration

WeFlow uses the following **Priority Logic** to load RSS feeds:

1. **Highest Priority**: Environment Variable `RSS_FEEDS`. If this is set in `.env` (and not empty), the system will **ONLY** use the feeds specified here, ignoring the default list.
2. **Default Fallback**: Built-in High-Quality List. If `RSS_FEEDS` is not set or empty, the system automatically loads the following feeds:
    - OpenAI Blog
    - BAIR (Berkeley AI Research)
    - DeepMind
    - Distill
    - MIT Technology Review
    - Hugging Face Blog
    - AI Shift
    - Ethics and Society
    - The Gradient
    - Machine Learning Mastery
    - KDnuggets
    - Artificial Intelligence News

### Custom Configuration Example

Configure in `.env` using commas to separate URLs:

```env
# Override default list, only fetch from these:
RSS_FEEDS=https://tech.meituan.com/feed/,https://www.solidot.org/index.rss,https://feeds.feedburner.com/PythonInsider
```

## Gallery

![Demo 1](images/demo1.png)
<br>
![Demo 2](images/demo2.png)
<br>
![Feishu Demo](images/demo3.png)
<br>
![Runtime Demo](images/demo4.png)

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended)
- PostgreSQL database

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd message-topai
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

## Database Setup (Docker Quickstart)

If you don't have local PostgreSQL, use Docker:

```bash
docker run -d \
  --name weflow-db \
  -e POSTGRES_USER=weflow \
  -e POSTGRES_PASSWORD=weflow \
  -e POSTGRES_DB=weflow \
  -p 5432:5432 \
  postgres:15
```

## Configuration

1. **Environment Variables**
   ```bash
   cp .env.example .env
   ```


2. **Edit `.env`**:

   > **Get API Keys**:
   > - **Firecrawl**: [firecrawl.dev](https://firecrawl.dev/)
   > - **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/)
   > - **DashScope (Qwen)**: [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/)

   ```env
   # Core
   FIRECRAWL_API_KEY=fc_...      # Web Crawling
   DEEPSEEK_API_KEY=sk-...       # LLM (Summarization & Unification)
   # Database (Matches Docker config above)
   DATABASE_URL=postgresql://weflow:weflow@localhost:5432/weflow
   
   # WeChat Official Account
   WECHAT_APP_ID=wx...
   WECHAT_APP_SECRET=...
   WECHAT_AUTHOR="WeFlow Bot"
   
   # Multimodal (Vision & Image Gen)
   # Provider: 'qwen' (recommended) or 'gemini'
   IMAGE_PROVIDER=qwen
   DASHSCOPE_API_KEY=sk-...      # Qwen-VL & Wanx
   
   # Notifications (Optional)
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/...
   ```

## Usage

Run the daily pipeline:

```bash
uv run python src/weflow/main.py
```

The system will:
1. Fetch articles from **Yesterday** (T-1 Day).
2. Analyze content and describe images using Vision models.
3. Synthesize a **Unified Daily Digest** in Markdown.
4. Upload all embedded images to WeChat.
5. Push the final draft and notify Feishu.

## Development

- **Run Tests**:
  ```bash
  uv run pytest
  ```
- **Verify Setup**:
  ```bash
  uv run python tests/verify_setup.py
  ```
