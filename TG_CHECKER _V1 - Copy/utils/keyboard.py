# utils/keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Add My Session ⚙️")],
        [KeyboardButton(text="📊 My Status"), KeyboardButton(text="📤 Logout My Session")],
        [KeyboardButton(text="🤖 Developer Info")]
    ],
    resize_keyboard=True,
    is_persistent=True
)

def get_main_keyboard_with_fallback():
    fallback_text = (
        "⚠️ Your Telegram app might not show the menu buttons.\n"
        "Use these commands manually:\n"
        "Add My Session ⚙️\n"
        "📊 My Status"
        "📤 Logout My Session\n"
        "🤖 Developer Info"
    )
    return main_keyboard, fallback_text
