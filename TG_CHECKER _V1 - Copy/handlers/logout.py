import os
from aiogram import Router, F
from aiogram.types import Message
from utils.keyboard import main_keyboard
from utils.logger import log_user_action
from utils.session_utils import (
    remove_session,
    reset_user_check_count,
    get_checks_done
)

router = Router()

@router.message(F.text == "📤 Logout My Session")
async def handle_logout(message: Message):
    user_id = message.from_user.id
    
    try:
        # Get current check count before logout (for logging)
        checks_done = get_checks_done(user_id)
        
        # Perform logout operations
        remove_session(user_id)
        reset_user_check_count(user_id)
        
        # Send success message
        await message.answer(
            "✅ <b>Successfully logged out!</b>\n\n"
            f"📊 Checks performed this session: {checks_done}\n"
            "🔐 Session data has been cleared.",
            reply_markup=main_keyboard,
            parse_mode="HTML"
        )
        log_user_action(user_id, f"Logged out (checks done: {checks_done})")
        
    except FileNotFoundError:
        await message.answer(
            "ℹ️ <b>No active session found</b>\n"
            "You're already logged out or never logged in.",
            reply_markup=main_keyboard,
            parse_mode="HTML"
        )
        log_user_action(user_id, "Tried to logout with no active session")
        
    except Exception as e:
        await message.answer(
            "⚠️ <b>Logout failed!</b>\n"
            "Please try again or contact support.",
            reply_markup=main_keyboard,
            parse_mode="HTML"
        )
        log_user_action(user_id, f"Logout error: {str(e)}")
        raise  # Re-raise for proper error tracking