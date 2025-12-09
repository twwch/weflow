# WeFlow

这是一个全自动化的内容工作流 SDK：自动发现热门技术文章、使用 Firecrawl 抓取内容、通过 DeepSeek 进行深度总结与融合、调用 Qwen-VL 理解图片、生成 AI 配图，并最终将图文并茂的“每日技术精选”推送到微信公众号草稿箱与飞书群。

## 核心功能

- **多模态智能 (Multimodal)**:
    - **视觉分析**: 集成 **Qwen-VL** 模型，自动“看懂”文章中的图片并生成描述，用于 Markdown 插图。
    - **AI 配图**: 支持通过 **Qwen (Wanx)** 或 **Gemini** 生成高质量封面图与插图。
- **统一日报风 (Unified Digest)**:
    - **Tech Crunch 风格**: 不是简单的文章堆砌，而是将多篇同类文章融合为一篇连贯、专业的深度报道。
    - **AI 标题生成**: 根据当日热点自动生成吸引人的中文标题 (e.g., "AI 日报: GPT-5 传闻与 Qwen 新突破")。
- **稳健发布 (Robust Publishing)**:
    - **图片本地化**: 自动下载原文图片并上传至微信服务器，解决防盗链导致的图片裂开问题。
    - **全局去重**: 智能追踪图片使用情况，确保整篇日报中没有重复图片。
- **智能通知**:
    - **飞书卡片**: 推送成功后，自动向飞书群发送包含状态、摘要和草稿 ID 的精美卡片。

## 架构概览

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

## RSS 配置详解

WeFlow 采用以下**优先级逻辑**加载 RSS 源：

1. **优先级最高**：环境变量 `RSS_FEEDS`。如果 `.env` 中配置了此项（非空），系统将**仅使用**这里指定的源，忽略默认列表。
2. **默认回退**：内置源列表。如果 `.env` 中未配置 `RSS_FEEDS` 或为空，系统将自动加载以下内置的高质量技术源：
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

### 自定义配置示例

在 `.env` 文件中配置，使用逗号分隔多个 URL：

```env
# 覆盖默认源，仅抓取以下列表
RSS_FEEDS=https://tech.meituan.com/feed/,https://www.solidot.org/index.rss,https://feeds.feedburner.com/PythonInsider
```

## 效果展示

![Demo 1](images/demo1.png)
<br>
![Demo 2](images/demo2.png)

## 环境要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (推荐)
- PostgreSQL 数据库

## 安装指南

1. **克隆代码库**
   ```bash
   git clone <repository_url>
   cd message-topai
   ```

2. **安装依赖**
   ```bash
   uv sync
   ```

## 数据库设置 (Docker 快速启动)

如果你本地没有 PostgreSQL，可以使用 Docker 快速启动一个：

```bash
docker run -d \
  --name weflow-db \
  -e POSTGRES_USER=weflow \
  -e POSTGRES_PASSWORD=weflow \
  -e POSTGRES_DB=weflow \
  -p 5432:5432 \
  postgres:15
```

## 配置指南

1. **初始化环境变量**
   ```bash
   cp .env.example .env
   ```


2. **编辑 `.env` 文件**:

   > **API Key 获取地址**:
   > - **Firecrawl**: [firecrawl.dev](https://firecrawl.dev/)
   > - **DeepSeek**: [platform.deepseek.com](https://platform.deepseek.com/)
   > - **DashScope (Qwen)**: [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/)

   ```env
   # 核心服务
   FIRECRAWL_API_KEY=fc_...      # 网页抓取 (Firecrawl)
   DEEPSEEK_API_KEY=sk-...       # LLM (深度总结与融合)
   # 数据库连接 (对应上述 Docker 配置)
   DATABASE_URL=postgresql://weflow:weflow@localhost:5432/weflow
   
   # 微信公众号
   WECHAT_APP_ID=wx...
   WECHAT_APP_SECRET=...
   WECHAT_AUTHOR="WeFlow Bot"    # 文章作者名
   
   # 多模态配置 (视觉分析与绘图)
   # 提供商: 'qwen' (推荐) 或 'gemini'
   IMAGE_PROVIDER=qwen
   DASHSCOPE_API_KEY=sk-...      # 阿里云 DashScope (Qwen-VL & Wanx)
   
   # 通知 (可选)
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/... # 飞书机器人 Webhook
   ```

## 使用方法

运行每日自动流：

```bash
uv run python src/weflow/main.py
```

系统将自动执行以下步骤：
1. **抓取**: 获取 **昨天** (T-1) 发布的所有技术文章。
2. **分析**: 使用 Vision 模型理解图片，使用 LLM 分析文本。
3. **融合**: 生成一篇统一风格的 Markdown 日报 (Unified Daily Digest)。
4. **上传**: 将文中所有嵌入图片上传至微信素材库。
5. **发布**: 推送最终草稿至公众号，并发送飞书通知。
