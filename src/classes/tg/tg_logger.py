import sys

import httpx
from httpx import AsyncClient, Response


class TGLogger:

    def __init__(self, token: str, chat_id: int):
        self.token: str = token
        self.chat_id: int = chat_id
        self.client: AsyncClient = httpx.AsyncClient(timeout=15.0)
        self.url: str = f"https://api.telegram.org/bot{self.token}/sendMessage"


    async def send_message(self, message: str):
        """Sends a message to a Telegram chat using the Bot API."""

        if not self.token:
            print("🚨Telegram token not configured. Cannot log.", file=sys.stderr)
            return
        if not self.chat_id:
            print("🚨Telegram chat ID not set. Cannot log.", file=sys.stderr)
            return

        payload = {
            "chat_id": int(self.chat_id),
            "text": message,
            "parse_mode": "Markdown"  # Optional: Use HTML for basic formatting like bold, italics
        }
        try:
            response: Response = await self.client.post(self.url, data=payload)
            if response.status_code != 200:
                print(f"🚨TG API Error. Cannot log. {response.json()}")
        except httpx.HTTPError as e:
            print(f"🚨TG API Error. Cannot log.")
