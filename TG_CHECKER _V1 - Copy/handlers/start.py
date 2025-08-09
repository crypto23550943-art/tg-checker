# handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from utils import check_number  # Relative import
from utils.logger import log_user_action
from utils.keyboard import get_main_keyboard_with_fallback
from utils.db import has_session  # ✅ Added for session check

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Handles /start command: clears state, sends welcome message, and shows main menu.
    """
    await state.clear()

    user_id = message.from_user.id

    # Detect new vs returning
    if has_session(user_id):
        log_user_action(user_id, "🚀 Restarted bot (session exists)")
        session_note = (
            "📌 *You can now send phone numbers* (one per line) to check if they are active on Telegram.\n"
            "💡 Example:\n"
            "`+1234567890`\n"
            "`+1987654321`\n"
        )
    else:
        log_user_action(user_id, "✨ Started bot (new user, no session yet)")
        session_note = (
            "⚠️ *No active session found!*\n"
            "➡️ Please tap *➕ Add My Session* below before sending numbers."
        )

    # Get main menu + fallback text
    keyboard, fallback = get_main_keyboard_with_fallback()

    # Send main welcome message
    try:
        await message.answer(
            f"👋 *Hi Bebzz, what's up?*\n\n"
            f"{session_note}\n\n"
            "👇 Use the menu below to manage your session or explore more options.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        # Extra fallback message (just in case)
        await message.answer(f"_If the menu is not visible, type_ /start _again._", parse_mode="Markdown")
    except Exception as e:
        log_user_action(user_id, f"❌ Error sending start message: {e}")
