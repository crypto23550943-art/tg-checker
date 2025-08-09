# handlers/check_limit.py
import os
from telethon import TelegramClient
from utils.session_utils import (
    is_limit_reached,
    session_exists,
    increment_user_check_count,
    reset_user_check_count
)
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact

from aiogram import Router, F
from aiogram.types import Message
from data.config import API_ID, API_HASH
from utils.logger import log_user_action
from utils.keyboard import main_keyboard

router = Router()

@router.message(F.text.startswith("+"))
async def handle_check_numbers(message: Message):
    user_id = message.from_user.id
    session_path = f"sessions/{user_id}.session"

    # ✅ Step 1: Check session exists
    if not os.path.exists(session_path):
        await message.answer("❌ No active session found. Use ➕ Add My Session first.")
        return

    # ✅ Step 2: Limit check
    if is_limit_reached(user_id):
        if os.path.exists(session_path):
            os.remove(session_path)
        reset_user_check_count(user_id)
        await message.answer(
            "🚫 Limit Reached!\n"
            "You've hit the <b>120 checks</b> limit.\n"
            "Session auto-logged out.\n\n"
            "🔄 Use ➕ Add My Session to re-login.",
            reply_markup=main_keyboard
        )
        log_user_action(user_id, "session auto-logged out after reaching 120 checks")
        return

    # ✅ Step 3: Clean numbers & format
    raw_numbers = message.text.strip().splitlines()
    cleaned_numbers = []
    for number in raw_numbers:
        n = number.strip()
        if not n:
            continue
        if not n.startswith("+"):
            n = "+" + n
        cleaned_numbers.append(n)

    numbers = cleaned_numbers
    if not numbers:
        await message.answer("❌ No valid phone numbers provided.")
        return

    log_user_action(user_id, f"Started checking {len(numbers)} numbers")

    # ✅ Step 4: Notify user
    progress_msg = await message.answer("Processing... 0% ➜ 100%", disable_web_page_preview=True)

    # ✅ Step 5: Connect Telethon
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.connect()

    # ✅ Step 6: Batch check
    valid_telegram_users = []
    total_batches = len(numbers) // 10 + (1 if len(numbers) % 10 != 0 else 0)
    for idx, chunk in enumerate([numbers[i:i + 10] for i in range(0, len(numbers), 10)]):
        contacts = [
            InputPhoneContact(client_id=i, phone=phone, first_name="User", last_name="")
            for i, phone in enumerate(chunk)
        ]
        try:
            result = await client(ImportContactsRequest(contacts))
            users = result.users
            for user in users:
                valid_telegram_users.append(user.phone)
            await client(DeleteContactsRequest(id=result.users))
        except Exception as e:
            log_user_action(user_id, f"Error checking batch: {str(e)}")
        percent = int(((idx + 1) / total_batches) * 100)
        await progress_msg.edit_text(f"Processing... {percent}% ➜ 100%")

    await client.disconnect()

    # ✅ Step 7: Update count
    increment_user_check_count(user_id, len(numbers))
    checked = get_user_check_count(user_id)
    remaining = max(0, 120 - checked)
    percent_left = round((remaining / 120) * 100)

    # ✅ Step 8: Separate valid and invalid
    invalid_numbers = [n for n in numbers if n not in valid_telegram_users]

    # ✅ Step 9: Send result
    await message.answer(
        f"✨ <b>Check Complete! Here is your report:</b>\n\n"
        f"✅ <b>Registered Users ({len(valid_telegram_users)})</b>\n"
        f"{chr(10).join(valid_telegram_users) if valid_telegram_users else 'None'}\n\n"
        f"❌ <b>Not Registered ({len(invalid_numbers)})</b>\n"
        f"{chr(10).join(invalid_numbers) if invalid_numbers else 'None'}\n\n"
        f"📈 <b>Quota Used:</b> {checked}/120\n"
        f"⏳ <b>Remaining:</b> {remaining} checks ({percent_left}% left)",
        reply_markup=main_keyboard
    )
    log_user_action(user_id, f"Checked {len(numbers)} numbers | {remaining} remaining")

    # ✅ Step 10: Auto logout if limit now reached
    if is_limit_reached(user_id):
        if os.path.exists(session_path):
            os.remove(session_path)
        reset_user_check_count(user_id)
        await message.answer(
            "🚫 You've now hit your <b>120 checks</b> limit.\n"
            "Session has been auto-logged out.\n\n"
            "🔄 Use ➕ Add My Session to re-login.",
            reply_markup=main_keyboard
        )
        log_user_action(user_id, "session auto-logged out after 120 checks")
