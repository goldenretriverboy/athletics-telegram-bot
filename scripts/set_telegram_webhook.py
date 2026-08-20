import asyncio

import httpx
from dotenv import load_dotenv

from app.core.config import get_settings


async def main() -> None:
    load_dotenv()
    settings = get_settings()
    webhook_url = f"{settings.public_base_url.rstrip('/')}/api/telegram/webhook"
    api_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            api_url,
            json={
                "url": webhook_url,
                "secret_token": settings.telegram_webhook_secret,
                "allowed_updates": ["callback_query"],
            },
        )
        response.raise_for_status()
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())

