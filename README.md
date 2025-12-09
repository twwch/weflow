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
- **Core Workflow**:
    - **RSS Monitoring**: Tracks top tech blogs (OpenAI, DeepMind, MIT Tech Review, etc.).
    - **Firecrawl**: Extracts clean markdown from complex web pages.
    - **PostgreSQL**: Tracks processed URLs to prevent duplicates.

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

## Configuration

1. **Environment Variables**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`**:

   ```env
   # Core
   FIRECRAWL_API_KEY=fc_...      # Web Crawling
   DEEPSEEK_API_KEY=sk-...       # LLM (Summarization & Unification)
   DATABASE_URL=postgres://...   # State Tracking
   
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
