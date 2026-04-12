import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from handlers import start, play, results, admin

async def main():
    # Inicializar base de datos
    init_db()

    # Crear bot con parse_mode correcto (Aiogram 3.13)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Dispatcher
    dp = Dispatcher(storage=MemoryStorage())

    # Routers
    dp.include_router(start.router)
    dp.include_router(play.router)
    dp.include_router(results.router)
    dp.include_router(admin.router)

    print("Bot iniciado.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

