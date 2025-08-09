# handlers/developer.py
from aiogram import Router, F
from aiogram.types import Message
from utils.keyboard import main_keyboard
from utils.logger import log_user_action

router = Router()

@router.message(F.text == "🤖 Developer Info")
async def developer_info(message: Message):
    user_id = message.from_user.id
    log_user_action(user_id, "Opened Developer Info")

    dev_text = (
        "🤖 <b>Developer Info</b>\n"
        "📛 <b>Name:</b> None\n"
        "📬 <b>Contact:</b> None\n"
        "📢 <b>Channel:</b> <a href='https://t.me/xyz_channel'>xyz channel</a>\n\n"
        "💬 <i>Need Any Type of Functional Bot? Feel Free to Ask — Market Best Price 🔥</i>"
    )

    await message.answer(dev_text, reply_markup=main_keyboard, disable_web_page_preview=True)
