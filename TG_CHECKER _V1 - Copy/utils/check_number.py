# utils/check_number.py

import os
import re
import asyncio
from asyncio.exceptions import TimeoutError

from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact

from aiogram import Router, F
from aiogram.types import Message

from utils.db import (
    get_check_count,
    increment_check_count,
    has_reached_limit,
    reset_user_check_count,
)
from utils.logger import log_user_action
from utils.session_utils import get_telethon_client
from utils.session_utils import increment_checks



MAX_CHECKS_PER_SESSION = int(os.getenv("MAX_CHECKS_PER_SESSION", "120"))
BATCH_SIZE = 10
BATCH_TIMEOUT = 15  # seconds
MAX_RETRIES = 3

router = Router()

def is_valid_phone_number(number: str) -> bool:
    """
    Validate phone number format (E.164 style).
    Allows numbers with optional +, country code 1–3 digits,
    and total length 8–15 digits (excluding +).
    """
    cleaned = number.lstrip("+")
    return cleaned.isdigit() and 8 <= len(cleaned) <= 15

async def check_telegram_numbers(user_id: int, numbers_list: list[str], progress_callback=None) -> tuple[list[str], list[str]]:
    session_path = f"sessions/{user_id}.session"
    if not os.path.exists(session_path):
        log_user_action(user_id, "❌ No session file for user")
        raise FileNotFoundError("Session not found. Please add your session first.")

    client = get_telethon_client(user_id)
    await client.connect()

    registered, unregistered = [], []

    try:
        if not await client.is_user_authorized():
            log_user_action(user_id, "⚠️ Session unauthorized/expired")
            raise RuntimeError("Session unauthorized or expired. Please re-add session.")

        # Filter and tag invalid numbers before batching
        valid_numbers = []
        for num in numbers_list:
            if is_valid_phone_number(num):
                valid_numbers.append(num)
            else:
                unregistered.append(f"{num} (Invalid Format)")

        if progress_callback:
            try:
                await progress_callback("Processing... Please wait.")
            except Exception:
                pass

        chunks = [valid_numbers[i:i + BATCH_SIZE] for i in range(0, len(valid_numbers), BATCH_SIZE)]

        for batch_index, chunk in enumerate(chunks, start=1):
            current = get_check_count(user_id)
            remaining_allowed = MAX_CHECKS_PER_SESSION - current
            if remaining_allowed <= 0:
                log_user_action(user_id, "🚫 Max checks reached — stopping.")
                break

            if len(chunk) > remaining_allowed:
                chunk = chunk[:remaining_allowed]

            contacts = [
                InputPhoneContact(client_id=i, phone=p, first_name="Check", last_name="Bot")
                for i, p in enumerate(chunk)
            ]

            attempt, success = 0, False
            while attempt < MAX_RETRIES and not success:
                attempt += 1
                try:
                    result = await asyncio.wait_for(client(ImportContactsRequest(contacts)), timeout=BATCH_TIMEOUT)
                    users = result.users or []
                    tg_phones = {u.phone.lstrip('+') for u in users if getattr(u, "phone", None)}

                    for phone in chunk:
                        if phone.lstrip('+') in tg_phones:
                            registered.append(phone)
                        else:
                            unregistered.append(phone)

                    if users:
                        try:
                            await client(DeleteContactsRequest(id=users))
                        except Exception as e:
                            log_user_action(user_id, f"⚠️ Failed to delete imported contacts: {e}")

                    increment_check_count(user_id, len(chunk))
                    success = True
                except TimeoutError:
                    log_user_action(user_id, f"⏳ Batch {batch_index} attempt {attempt} timed out")
                except Exception as e:
                    log_user_action(user_id, f"⚠️ Batch {batch_index} attempt {attempt} failed: {e}")

            if not success:
                unregistered.extend(chunk)
                log_user_action(user_id, f"⚠️ Batch {batch_index} failed after {attempt} attempts")

            if has_reached_limit(user_id):
                if os.path.exists(session_path):
                    try:
                        os.remove(session_path)
                    except Exception:
                        pass
                reset_user_check_count(user_id)
                log_user_action(user_id, "🧹 Session auto-removed after limit reached")
                break

        total_checked = len(registered) + len(unregistered)
        log_user_action(user_id, f"📱 Checked {total_checked} numbers; valid={len(registered)} invalid={len(unregistered)}")
        
        return registered, unregistered

    finally:
        try:
            await client.disconnect()
        except Exception:
            pass

@router.message(F.text.regexp(r"^\+?\d+(?:[,\s]+\+?\d+)*$"))
async def handle_dropped_numbers(message: Message):
    user_id = message.from_user.id
    log_user_action(user_id, "📥 Dropped numbers for auto-check")

    raw_numbers = message.text.replace(",", " ").split()
    numbers_list = [num if num.startswith("+") else f"+{num}" for num in raw_numbers]

    try:
        registered, unregistered = await check_telegram_numbers(
            user_id, numbers_list,
            progress_callback=lambda txt: message.answer(txt)
        )
    except FileNotFoundError:
        await message.answer("⚠️ You need to add your session first.")
        return
    except Exception as e:
        await message.answer(f"❌ Error: {e}")
        return

    total_checked = len(registered) + len(unregistered)
    remaining_quota = MAX_CHECKS_PER_SESSION - get_check_count(user_id)

    total_checked = len(registered) + len(unregistered)

    result_msg = (
        "✨ <b>Check Complete! Here is your report:</b>\n\n"
        f"📦 <b>Total Checked:</b> {total_checked}\n\n"
        f"✅ <b>Registered Users ({len(registered)})</b>\n"
        f"{chr(10).join(registered) if registered else 'None'}\n\n"
        f"❌ <b>Not Registered ({len(unregistered)})</b>\n"
        f"{chr(10).join(unregistered) if unregistered else 'None'}"
    )


    await message.answer(result_msg, parse_mode="HTML")
