import os
import requests
import json
from typing import Optional

class FeishuNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL")

    def send_card(self, title: str, summary: str, article_url: str, cover_image_key: str = "") -> bool:
        """
        Sends a card message to Feishu.
        """
        if not self.webhook_url:
            print("Feishu webhook not configured. Skipping notification.")
            return False

        # Simplified Card Structure
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**Status**: Draft Pushed ✅\n**Summary**: {summary}"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "View Article"
                            },
                            "url": article_url,
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
        
        payload = {
            "msg_type": "interactive",
            "card": card
        }

        try:
            response = requests.post(
                self.webhook_url, 
                headers={"Content-Type": "application/json"}, 
                data=json.dumps(payload)
            )
            response.raise_for_status()
            res_data = response.json()
            if res_data.get("code") == 0:
                print("Feishu notification sent successfully.")
                return True
            else:
                print(f"Feishu API error: {res_data}")
                return False
        except Exception as e:
            print(f"Failed to send Feishu notification: {e}")
            return False
