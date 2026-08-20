import asyncio
import logging
import sys

from app.core.logging import configure_logging
from app.db.pool import create_pool
from app.pipeline import run_monitor

logger = logging.getLogger(__name__)


async def main() -> None:
    configure_logging()
    mode = sys.argv[1] if len(sys.argv) > 1 else "digest"
    if mode not in {"morning", "digest"}:
        raise SystemExit("Usage: python -m app.jobs.digest [morning]")

    pool = await create_pool()
    try:
        created = await run_monitor(pool, mode=mode)
        logger.info("%s digest completed created=%s", mode, created)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
