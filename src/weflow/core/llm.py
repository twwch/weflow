from abc import ABC, abstractmethod
import os
from openai import OpenAI
from typing import Optional

class LLMProvider(ABC):
    @abstractmethod
    def analyze(self, content: str) -> str:
        """Returns JSON analysis of the content (topic, recommended, etc.)"""
        pass

    @abstractmethod
    def synthesize_report(self, articles_data: list[dict], topic: str) -> str:
        """Synthesizes multiple articles into a single HTML report"""
        pass

class DeepSeekLLM(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)

    def summarize(self, content: str) -> str:
        # Backward compatibility or simple usage
        return self.analyze(content)

    def analyze(self, content: str) -> str:
        prompt = f"""
        You are a Senior Technical Editor. Analyze the following article content.

        **Task**:
        1. Determine the primary **Topic** from this list: [Generative AI, Robotics, Hardware/Chips, Industry/Business, Programming/Dev, Science/Research, Agi/Safety]. If none fit, use 'Other'.
        2. Determine if it is **Recommended**: 
           - YES for deep tech, research, insights. 
           - NO for recruitment/jobs, generic ads, press releases without substance.
        3. Provide a brief **Summary** (plain text).

        **Output**: Strict JSON object.
        {{
            "topic": "...",
            "recommended": true/false,
            "reason": "...",
            "summary": "..."
        }}

        **Content**:
        {content[:15000]}
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                stream=False,
                response_format={ "type": "json_object" }
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error analyzing content: {e}")
            return "{}"

    def synthesize_report(self, articles_data: list[dict], topic: str, images: list[dict] = []) -> str:
        # articles_data: list of dicts with 'title', 'source_name', 'content' (or summary)
        # images: list of dicts with 'url', 'description'

        combined_text = ""
        for i, art in enumerate(articles_data):
            combined_text += f"--- Article {i+1} ---\nTitle: {art.get('title')}\nSource: {art.get('source_name')}\nContent: {art.get('content')[:8000]}\n\n"

        image_context = ""
        if images:
            image_context = "Available Images:\n"
            for img in images:
                image_context += f"- Link: {img['url']}\n  Description: {img['description']}\n"

        prompt = f"""
        You are a Senior Technical Editor. 
        **Goal**: Write a **cohesive, synthesized deep-dive report** on the topic **"{topic}"**, integrating information from the following source articles.
        
        **Requirements**:
        1. **Language**: Chinese (Simplified). Strict no-English rule unless for technical terms.
        2. **Fusion**: Weave information into a single narrative. Do NOT list articles.
        3. **Visuals**: Review "Available Images". If matches, **insert using Markdown**: `![Description](original_url)`.
        4. **Structure**:
           - **Introduction**: Context.
           - **Core Developments**: Main body (### Subheadings).
           - **Key Insights**: Bullet points.
        5. **Output Format**: **Markdown ONLY**.
           - **CRITICAL**: Do NOT output "Okay", "Here is the report", or any conversational text.
           - Start directly with the first header or paragraph.
        
        **Available Images**:
        {image_context}

        **Source Material**:
        {combined_text}
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a specific technical writer. You output ONLY Markdown content. No conversational fillers."},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content.strip() # Strip to remove any potential whitespace
        except Exception as e:
            print(f"Error synthesizing report: {e}")
            return f"Error generating report for {topic}."

    def generate_digest_title(self, topics: list[str]) -> str:
        prompt = f"""
        Generate a catchy, professional, and concise title for a daily AI technology digest covering the following topics:
        {', '.join(topics)}
        
        Requirements:
        1. Language: Chinese (Simplified).
        2. Style: Tech-forward, professional, engaging.
        3. Length: Maximum 20 characters.
        4. Format: Plain text, no quotes, no markdown.
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a creative editor."},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            title = response.choices[0].message.content.strip()
            # Remove quotes if present
            title = title.replace('"', '').replace('”', '').replace('“', '')
            return title
        except Exception as e:
            print(f"Error generating title: {e}")
            return f"WeFlow Daily - {datetime.now().strftime('%Y-%m-%d')}"

    def unify_daily_digest(self, combined_markdown: str) -> str:
        prompt = f"""
        You are a Chief Editor for a top-tier tech publication.
        **Goal**: Re-write and polish the following collection of topic reports into a single, cohesive Daily Digest.
        
        **Requirements**:
        1. **Tone**: Unified, professional, "Tech Crunch" or "Hacker News" style. Chinese (Simplified).
        2. **Structure**: Keep the main topics as H2 or H1 headers. Use `---` to separate major sections.
        3. **Images**: **CRITICAL**: You MUST preserve all image links `![Alt](url)` exactly as they are. Do NOT remove or modify URLs. Do NOT change position if it makes sense.
        4. **Flow**: Smooth out transitions between topics. Remove repetitive intros if they sound redundant.
        5. **Output**: **Markdown ONLY**. No conversational fillers.
        
        **Draft Content**:
        {combined_markdown}
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a Chief Editor. Output Markdown only."},
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error unifying report: {e}")
            return combined_markdown # Return original if failure
