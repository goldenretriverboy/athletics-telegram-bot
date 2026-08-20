from fastapi import FastAPI

from app.telegram.webhook import router as telegram_router
from app.web.admin import router as admin_router

app = FastAPI(title="Athletics Telegram Bot")
app.include_router(admin_router)
app.include_router(telegram_router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
