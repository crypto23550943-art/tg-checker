from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio
import logging
import os
import sys
from data.config import BOT_TOKEN
from handlers import add_session, add_plus, logout, check_status
from utils.logger import log_user_action

# ✅ Ensure sessions folder exists
os.makedirs("sessions", exist_ok=True)

# ✅ Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)


def show_startup_banner():
    banner = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🚀 Telegram Checker Bot is Starting ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
    print(banner)


async def main():
    # ✅ Token check fallback
    if not BOT_TOKEN or "YOUR_BOT_TOKEN" in BOT_TOKEN:
        print("❌ ERROR: Bot token missing or invalid in .env file.")
        sys.exit(1)

    # ✅ Print banner
    show_startup_banner()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # ✅ Include all handlers
    dp.include_routers(
        add_session.router,
        add_plus.router,
        logout.router,
        check_status.router
    )

    # ✅ Drop any pending updates
    await bot.delete_webhook(drop_pending_updates=True)
    log_user_action("SYSTEM", "✅ Bot started polling.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log_user_action("SYSTEM", "🛑 Bot stopped by user (Ctrl+C)")
        print("\n👋 Exiting... Goodbye!")
