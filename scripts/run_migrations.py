import asyncio
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from app.core.config import get_settings


async def main() -> None:
    load_dotenv()
    settings = get_settings()
    conn = await asyncpg.connect(dsn=settings.database_url)
    try:
        for path in sorted(Path("migrations").glob("*.sql")):
            await conn.execute(path.read_text(encoding="utf-8"))
            print(f"applied {path}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

