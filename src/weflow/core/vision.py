from abc import ABC, abstractmethod
import os
import dashscope
from dashscope import MultiModalConversation
from typing import Optional

class VisionProvider(ABC):
    @abstractmethod
    def describe_image(self, image_url: str) -> str:
        """Returns a concise description of the image content."""
        pass

class QwenVisionProvider(VisionProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DashScope API key is required for QwenVisionProvider")
        dashscope.api_key = self.api_key

    def describe_image(self, image_url: str) -> str:
        """Uses Qwen-VL to describe the image."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": image_url},
                        {"text": "Briefly describe this image for a technical article caption. Keep it under 20 words."}
                    ]
                }
            ]
            
            response = MultiModalConversation.call(
                model='qwen-vl-max',
                messages=messages
            )
            
            if response.status_code == 200:
                if 'output' in response and 'choices' in response.output:
                    content = response.output.choices[0]['message']['content']
                    # Sometimes content is a list of dicts, sometimes string depending on SDK version?
                    # DashScope VL usually returns text in content list or direct string.
                    # Let's handle list just in case, but usually it's a struct.
                    if isinstance(content, list):
                        text = "".join([c.get('text', '') for c in content])
                        return text.strip()
                    return str(content).strip()
                return ""
            else:
                print(f"Qwen Vision API failed: {response.code} {response.message}")
                return ""
                
        except Exception as e:
            print(f"Error describing image {image_url}: {e}")
            return ""

class MockVisionProvider(VisionProvider):
    def describe_image(self, image_url: str) -> str:
        return "A placeholder description for the image."
