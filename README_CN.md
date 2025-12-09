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
- **核心流程**:
    - **RSS 监控**: 默认追踪 OpenAI, DeepMind, MIT Tech Review 等顶级技术源。
    - **智能抓取**: 使用 Firecrawl 提取干净的 Markdown 内容。
    - **状态追踪**: 使用 PostgreSQL 记录已处理链接，防止重复抓取。

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

## 配置指南

1. **初始化环境变量**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**:

   ```env
   # 核心服务
   FIRECRAWL_API_KEY=fc_...      # 网页抓取 (Firecrawl)
   DEEPSEEK_API_KEY=sk-...       # LLM (深度总结与融合)
   DATABASE_URL=postgres://...   # 数据库连接
   
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
