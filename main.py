# main.py



import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
import config
print(f"GROUP_ID cargado: {config.GROUP_ID}")
import utils.database as db
from handlers import start, payments, results, admin, group_events
from services.scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def main():
    db.init_db()
    logger.info("Base de datos lista.")

    bot = Bot(token=BOT_TOKEN)
    dp  = Dispatcher(storage=MemoryStorage())

    # Registrar handlers — el orden importa
    dp.include_router(group_events.router)
    dp.include_router(admin.router)
    dp.include_router(payments.router)
    dp.include_router(results.router)
    dp.include_router(start.router)

    scheduler = start_scheduler(bot)

    logger.info("Bot Underground FUT arrancando...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "chat_member"]
        )
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot detenido.")


if __name__ == "__main__":
    asyncio.run(main())
