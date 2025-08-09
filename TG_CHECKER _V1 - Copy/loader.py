# loader.py
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN missing in .env")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

def get_bot_info_summary() -> str:
    token_preview = BOT_TOKEN[:6] + "..." + BOT_TOKEN[-4:] if BOT_TOKEN else "N/A"
    return f"🤖 Bot running with token: {token_preview}"
