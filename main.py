import asyncio
import logging

from run.bot import Bot
from utils.logger import setup_logging


async def main():
    setup_logging()
    try:
        await Bot.initialize()
        await Bot.run()
    except Exception as exc:
        logging.getLogger(__name__).exception("Bot ishga tushmadi")
        raise SystemExit(f"Botni ishga tushirib bo'lmadi: {exc}") from exc


if __name__ == "__main__":
    asyncio.run(main())
