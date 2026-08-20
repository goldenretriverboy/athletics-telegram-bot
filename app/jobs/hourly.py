import asyncio
import logging

from app.core.logging import configure_logging
from app.db.pool import create_pool
from app.pipeline import run_monitor

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging()
    pool = await create_pool()
    try:
        created = await run_monitor(pool, mode="hourly")
        logger.info("hourly monitor completed created=%s", created)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())

