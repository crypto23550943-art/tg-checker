import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher
from data.config import BOT_TOKEN
from handlers import start, add_session, check_status, logout, developer
from utils import check_number  # import your utils/check_number.py
from utils.logger import log_user_action

# Bot & Dispatcher setup
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Register routers
dp.include_router(start.router)
dp.include_router(add_session.router)
dp.include_router(check_number.router)
dp.include_router(check_status.router)
dp.include_router(logout.router)
dp.include_router(developer.router)

async def on_startup():
    log_user_action("SYSTEM", "🚀 Bot is starting")

async def on_shutdown():
    log_user_action("SYSTEM", "🛑 Bot is shutting down")
    await bot.session.close()

async def main():
    await on_startup()
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log_user_action("SYSTEM", "❗ Bot stopped manually")
