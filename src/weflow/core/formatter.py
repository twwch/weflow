class WeChatFormatter:
    @staticmethod
    def markdown_to_html(text: str) -> str:
        import markdown
        import re
        
        # 1. Convert Markdown to base HTML
        # extensions=['extra'] enables tables, fenced code blocks, etc.
        html = markdown.markdown(text, extensions=['extra'])
        
        # 2. Inject WeChat Inline Styles
        
        # H3
        html = re.sub(
            r'<h3>(.*?)</h3>', 
            r'<h3 style="font-size: 18px; font-weight: bold; margin-top: 25px; margin-bottom: 15px; color: #333; border-left: 4px solid #576b95; padding-left: 10px;">\1</h3>', 
            html
        )
        
        # H2
        html = re.sub(
            r'<h2>(.*?)</h2>', 
            r'<h2 style="font-size: 20px; font-weight: bold; margin-top: 30px; margin-bottom: 20px; color: #000;">\1</h2>', 
            html
        )
        
        # P (Standard Paragraphs)
        html = re.sub(
            r'<p>(.*?)</p>', 
            r'<p style="margin-bottom: 15px; line-height: 1.8; color: #444;">\1</p>', 
            html
        )
        
        # Lists (ul, ol, li)
        html = html.replace('<ul>', '<ul style="padding-left: 20px; color: #555; margin-bottom: 20px;">')
        html = html.replace('<ol>', '<ol style="padding-left: 20px; color: #555; margin-bottom: 20px;">')
        html = re.sub(r'<li>(.*?)</li>', r'<li style="margin-bottom: 8px; line-height: 1.6;">\1</li>', html)
        
        # Bold / Strong
        html = re.sub(r'<strong>(.*?)</strong>', r'<span style="font-weight: bold; color: #222;">\1</span>', html)
        
        # Horizontal Rule (Result of '---' in Markdown)
        html = html.replace('<hr />', '<div style="margin: 40px 0; border-bottom: 1px solid #eee;"></div>')
        html = html.replace('<hr>', '<div style="margin: 40px 0; border-bottom: 1px solid #eee;"></div>')
        
        # 3. Enhanced Image Handling
        # Markdown lib typically outputs: <p><img alt="Desc" src="Url" /></p>
        # We want to transform this into our styled <figure> structure.
        
        def img_repl(match):
            # match.group(1) is the inner content of <p>...</p>, which should be the img tag
            img_tag = match.group(1)
            # Extract src and alt from img tag
            m_src = re.search(r'src="(.*?)"', img_tag)
            m_alt = re.search(r'alt="(.*?)"', img_tag)
            
            url = m_src.group(1) if m_src else ""
            alt = m_alt.group(1) if m_alt else ""
            
            return f"""
            <figure style="margin: 20px 0;">
                <img src="{url}" style="width: 100%; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />
                <figcaption style="font-size: 12px; color: #999; text-align: center; margin-top: 5px;">{alt}</figcaption>
            </figure>
            """
            
        # Regex to find <p> tags that contain strictly an <img> tag (and maybe whitespace)
        # Pattern: <p style="...">\s*<img ... />\s*</p>
        # Note: We already styled <p> to <p style="...">.
        html = re.sub(
            r'<p style="[^"]+">\s*(<img [^>]+>)\s*</p>', 
            img_repl, 
            html, 
            flags=re.DOTALL
        )
        
        return html

    @staticmethod
    def format_article_section(title: str, summary: str, image_url: str, source_url: str) -> str:
        return f"""
        <section style="margin-bottom: 40px; border-bottom: 1px solid #eee; padding-bottom: 30px;">
            <h2 style="font-size: 22px; color: #333; margin-bottom: 15px; font-weight: bold; line-height: 1.4;">{title}</h2>
            
            <figure style="margin: 0 0 20px 0;">
                <img src="{image_url}" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" />
            </figure>
            
            <div style="font-size: 16px; color: #555; line-height: 1.8; text-align: justify;">
                {summary}
            </div>
        </section>
        """

    @staticmethod
    def wrap_full_article(sections_html: str, date_str: str, author: str = None) -> str:
        """Wraps the full article with a header and footer."""
        author_html = f'<p style="color: #888; font-size: 14px; margin-left: 10px;">Editor: {author}</p>' if author else ""
        return f"""
        <div style="padding: 15px; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', 'Source Han Sans SC', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', sans-serif;">
            <header style="margin-bottom: 30px; text-align: center;">
                <h1 style="font-size: 22px; font-weight: bold; margin-bottom: 5px;">每日技术精选</h1>
                <div style="display: flex; justify-content: center; align-items: center; margin-top: 5px;">
                    <p style="color: #888; font-size: 14px;">{date_str}</p>
                    {author_html}
                </div>
            </header>
            
            {sections_html}
        </div>
        """
