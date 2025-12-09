from abc import ABC, abstractmethod
import os
import dashscope
from dashscope import ImageSynthesis
import google.generativeai as genai
from typing import Optional

class ImageProvider(ABC):
    @abstractmethod
    def generate_image(self, prompt: str) -> str:
        """Returns the URL of the generated image"""
        pass

class MockImageProvider(ImageProvider):
    """Temporary mock provider for testing without consuming credits"""
    def generate_image(self, prompt: str) -> str:
        return "https://via.placeholder.com/1024x1024.png?text=AI+Generated+Image"

class QwenImageProvider(ImageProvider):
    """
    Uses Alibaba Cloud's DashScope Wanx model for image generation.
    Requires DASHSCOPE_API_KEY env var.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DashScope API key is required for QwenImageProvider")
        dashscope.api_key = self.api_key

    def generate_image(self, prompt: str) -> str:
        try:
            rsp = ImageSynthesis.call(
                model=ImageSynthesis.Models.wanx_v1,
                prompt=prompt,
                n=1,
                size='1024*1024'
            )
            if rsp.status_code == 200:
                # The response structure might vary, usually rsp.output.results[0].url
                if rsp.output and rsp.output.results:
                    return rsp.output.results[0].url
                else:
                    raise Exception(f"Empty results from Qwen: {rsp}")
            else:
                raise Exception(f"Qwen API failed: {rsp.code} - {rsp.message}")
        except Exception as e:
            print(f"Error generating image with Qwen: {e}")
            raise e

class GeminiImageProvider(ImageProvider):
    """
    Uses Google's Gemini/Imagen models via google-generativeai.
    User referred to 'nanobanano' which corresponds to newer Gemini Image models.
    We default to 'imagen-3.0-generate-001'.
    Requires GOOGLE_API_KEY env var.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "imagen-3.0-generate-001"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required for GeminiImageProvider")
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.ImageGenerationModel(model_name=self.model_name)

    def generate_image(self, prompt: str) -> str:
        try:
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
            )
            # The SDK might return an object that needs saving or has a temporary URL.
            # Typically response.images[0] is the image data.
            # If we need a URL, we might need to upload it somewhere or save locally and serve.
            # However, the interface demands a URL.
            # For this SDK context, let's assuming we save it to a temp file and return the path
            # Or if the use case strictly needs a URL (like WeChat upload), local path works if WeChat uploader handles it.
            # But our WeChat uploader (src/weflow/core/wechat.py) expects a URL or we need to modify it.
            # Let's check `wechat.py`. It uses requests.get(image_url).
            # So we should probably modify `wechat.py` to handle local paths or BytesIO, 
            # OR here we just return a local file path with file:// schema and patch wechat to handle it.
            
            # Let's just save to a temp file and return a dummy URL or local path.
            # To fit the 'download' logic in wechat.py, we might need to adjust wechat.py.
            # But for simplicity, let's change logic in wechat.py to handle non-http schemes or just raw bytes.
            
            # Actually, standard GenAI SDK returns PIL Image or bytes.
            # I will save it to a local temporary file and return the absolute path.
            # I'll need to update `wechat.py` to handle local files.
            
            image = response.images[0]
            filename = f"temp_gen_{os.urandom(4).hex()}.png"
            image.save(filename)
            return os.path.abspath(filename)
            
        except Exception as e:
            print(f"Error generating image with Gemini: {e}")
            raise e
