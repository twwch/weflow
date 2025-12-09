import requests
import os
import json
from typing import Optional

class WeChatPublisher:
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or os.getenv("WECHAT_APP_ID")
        self.app_secret = app_secret or os.getenv("WECHAT_APP_SECRET")
        if not self.app_id or not self.app_secret:
            raise ValueError("WeChat App ID and Secret are required")
        self.access_token = None
        self.token_expiry = 0

    def _get_access_token(self) -> str:
        # Simple implementation, ideally should cache properly checking expiry time
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        response = requests.get(url)
        data = response.json()
        if "access_token" in data:
            self.access_token = data["access_token"]
            return self.access_token
        else:
            raise Exception(f"Failed to get access token: {data}")

    def upload_image(self, image_url: str) -> str:
        """Downloads image from URL and uploads to WeChat, returns media_id"""
        token = self._get_access_token()
        
        import uuid
        # Use tmp directory
        tmp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        
        unique_name = os.path.join(tmp_dir, f"temp_{uuid.uuid4().hex}.jpg")
        
        if os.path.exists(image_url):
            # Local file
            filepath = image_url
            temp_file = False
        else:
            # Remote URL
            img_resp = requests.get(image_url)
            img_resp.raise_for_status()
            filepath = unique_name
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
            temp_file = True

        upload_url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
        
        try:
            with open(filepath, "rb") as f:
                files = {'media': f}
                response = requests.post(upload_url, files=files)
        finally:
            if temp_file and os.path.exists(filepath):
                os.remove(filepath)
        data = response.json()
        if "media_id" in data:
            return data["media_id"]
        else:
            raise Exception(f"Failed to upload image: {data}")

    def upload_article_image(self, image_url: str) -> str:
        """Uploads an image to be used inside an article (not cover), returns URL"""
        token = self._get_access_token()
        
        import uuid
        # Use tmp directory
        tmp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        
        unique_name = os.path.join(tmp_dir, f"temp_art_{uuid.uuid4().hex}.jpg")
        
        if os.path.exists(image_url):
            filepath = image_url
            temp_file = False
        else:
            img_resp = requests.get(image_url)
            img_resp.raise_for_status()
            filepath = unique_name
            with open(filepath, "wb") as f:
                f.write(img_resp.content)
            temp_file = True

        upload_url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
        
        try:
            with open(filepath, "rb") as f:
                files = {'media': f}
                response = requests.post(upload_url, files=files)
        finally:
            if temp_file and os.path.exists(filepath):
                os.remove(filepath)
                
        data = response.json()
        if "url" in data:
            return data["url"]
        else:
            raise Exception(f"Failed to upload article image: {data}")

    def push_draft(self, title: str, summary: str, media_id: str, content: str, source_url: str, author: str = "") -> str:
        """Pushes a draft to WeChat, returns draft_id or status"""
        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
        
        article = {
            "title": title,
            "author": author,
            "digest": summary,
            "content": content, # This expects HTML content usually
            "content_source_url": source_url,
            "thumb_media_id": media_id,
        }
        
        payload = {"articles": [article]}
        # Ensure proper encoding for Chinese characters
        response = requests.post(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        
        data = response.json()
        if "media_id" in data: # Draft API returns media_id/article_id? Draft API vs News API differ. 
            # Recent WeChat API changes: 'draft/add' returns media_id usually.
            return data.get("media_id") or str(data)
        elif "errcode" in data and data["errcode"] == 0:
            return "Success" 
        else:
            raise Exception(f"Failed to push draft: {data}")

    def get_draft(self, media_id: str) -> Optional[dict]:
        """Fetches draft details including URL"""
        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}"
        payload = {"media_id": media_id}
        
        try:
            response = requests.post(url, data=json.dumps(payload))
            data = response.json()
            if "news_item" in data and len(data["news_item"]) > 0:
                return data["news_item"][0] # Return the first item
            return None
        except Exception as e:
            print(f"Error fetching draft: {e}")
            return None
