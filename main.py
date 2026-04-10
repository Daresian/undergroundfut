import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import start, play, results, admin

async def main():
    init_db()

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(play.router)
    dp.include_router(results.router)
    dp.include_router(admin.router)

    print("Bot iniciado.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
