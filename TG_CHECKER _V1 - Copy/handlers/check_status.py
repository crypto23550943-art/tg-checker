from utils.session_utils import get_checks_done
from aiogram import Router, F
from aiogram.types import Message
from utils.keyboard import main_keyboard

router = Router()

@router.message(F.text == "📊 My Status")
async def handle_status(message: Message):
    user_id = message.from_user.id
    count = get_checks_done(user_id)
    remaining = max(0, 120 - count)
    
    await message.answer(
        f"📊 <b>Your Status</b>\n\n"
        f"✅ <b>Checked:</b> {count}/120\n"
        f"⏳ <b>Remaining:</b> {remaining}",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )
