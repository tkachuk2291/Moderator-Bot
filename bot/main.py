import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from .config import BOT_TOKEN
from .handlers import help_router, moderation_router, report_router, karma_router
from .handlers.text_moderation import text_moderation_router
from .middlewares import StoreMiddleware
from .data_store import DataStore


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(help_router)
    dp.include_router(text_moderation_router)
    dp.include_router(moderation_router)
    dp.include_router(report_router)
    dp.include_router(karma_router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    # Inject shared DataStore via middleware
    store = DataStore()
    dp.update.outer_middleware(StoreMiddleware(store))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

