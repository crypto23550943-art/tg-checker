# handlers/add_session.py
import asyncio
import os
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError
)
from utils.keyboard import main_keyboard
from utils.logger import log_user_action
from data.config import API_ID, API_HASH

load_dotenv()
router = Router()

class SessionState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()

HIDE_KB = ReplyKeyboardRemove()

# 📌 Start session creation
@router.message(F.text == "Add My Session ⚙️")
async def add_session_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    log_user_action(user_id, "⚙️ Add My Session clicked")
    await message.answer(
        "☎️ Please send your phone number (e.g. +1234567890):",
        reply_markup=HIDE_KB
    )
    await state.set_state(SessionState.waiting_for_phone)

    # ⏳ Timeout for phone input
    async def timeout():
        await asyncio.sleep(120)
        if await state.get_state() == SessionState.waiting_for_phone:
            await message.answer(
                "⌛️ Timeout: You took too long to enter your phone number.",
                reply_markup=main_keyboard
            )
            await state.clear()
            log_user_action(user_id, "⏰ Timeout at phone input")

    asyncio.create_task(timeout())

# 📌 Handle phone number input
@router.message(SessionState.waiting_for_phone)
async def process_phone_number(message: Message, state: FSMContext):
    phone = message.text.strip()
    user_id = message.from_user.id

    # Validate format
    if not phone.startswith("+") or not phone[1:].isdigit():
        await message.answer("❌ Invalid phone number format. Use +1234567890")
        return

    session_path = f"sessions/{user_id}"
    client = TelegramClient(session_path, API_ID, API_HASH)

    try:
        await client.connect()
        result = await client.send_code_request(phone)
        await state.update_data(phone=phone, phone_code_hash=result.phone_code_hash, retry_code=0)
        await message.answer("📩 Code sent! Please enter the code (e.g. 12345):", reply_markup=HIDE_KB)
        await state.set_state(SessionState.waiting_for_code)
        log_user_action(user_id, "📩 Waiting for code")

        # Timeout for code entry
        async def code_timeout():
            await asyncio.sleep(60)
            if await state.get_state() == SessionState.waiting_for_code:
                await message.answer(
                    "⌛️ Timeout: You didn’t enter the code in time.",
                    reply_markup=main_keyboard
                )
                await state.clear()
                log_user_action(user_id, "⏰ Timeout at code input")

        asyncio.create_task(code_timeout())

    except Exception as e:
        await message.answer("⚠️ Failed to send code. Please try again.", reply_markup=main_keyboard)
        log_user_action(user_id, f"❌ Failed to send code: {e}")
        await client.disconnect()
        await state.clear()

# 📌 Handle code input
@router.message(SessionState.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    phone = data.get("phone")
    phone_code_hash = data.get("phone_code_hash")
    retry_code = data.get("retry_code", 0)
    session_path = f"sessions/{user_id}"
    client = TelegramClient(session_path, API_ID, API_HASH)

    try:
        await client.connect()
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        await client.disconnect()
        await message.answer("✅ <b>Session added successfully!</b>", reply_markup=main_keyboard)
        log_user_action(user_id, "✅ Session added (no 2FA)")
        await state.clear()

    except PhoneCodeInvalidError:
        retry_code += 1
        await state.update_data(retry_code=retry_code)
        await message.answer(f"❌ Invalid code. Attempt {retry_code}/3")
        log_user_action(user_id, f"❌ Invalid code attempt {retry_code}")
        await client.disconnect()
        if retry_code >= 3:
            await message.answer("🚫 Too many invalid attempts. Please start over.", reply_markup=main_keyboard)
            log_user_action(user_id, "❌ Too many wrong codes")
            await state.clear()

    except PhoneCodeExpiredError:
        await message.answer("⏰ Code expired. Please restart login.", reply_markup=main_keyboard)
        log_user_action(user_id, "❌ Code expired")
        await client.disconnect()
        await state.clear()

    except SessionPasswordNeededError:
        await message.answer("🔐 2FA is enabled. Please enter your Telegram password:", reply_markup=HIDE_KB)
        await state.update_data(code=code, retry_password=0)
        await state.set_state(SessionState.waiting_for_password)
        log_user_action(user_id, "🔐 Waiting for 2FA password")
        await client.disconnect()

    except Exception as e:
        await message.answer("❌ Something went wrong during login. Please try again.", reply_markup=main_keyboard)
        log_user_action(user_id, f"❌ Login error: {e}")
        await client.disconnect()
        await state.clear()

# 📌 Handle 2FA password
@router.message(SessionState.waiting_for_password)
async def process_2fa_password(message: Message, state: FSMContext):
    password = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    phone = data.get("phone")
    code = data.get("code")
    phone_code_hash = data.get("phone_code_hash")
    retry_password = data.get("retry_password", 0)
    session_path = f"sessions/{user_id}"
    client = TelegramClient(session_path, API_ID, API_HASH)

    try:
        await client.connect()
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        await client.sign_in(password=password)
        await client.disconnect()
        await message.answer("✅ <b>Session with 2FA added successfully!</b>", reply_markup=main_keyboard)
        log_user_action(user_id, "✅ 2FA session created")
        await state.clear()

    except PasswordHashInvalidError:
        retry_password += 1
        await state.update_data(retry_password=retry_password)
        await message.answer(f"❌ Wrong password. Attempt {retry_password}/3")
        log_user_action(user_id, f"❌ Wrong 2FA password attempt {retry_password}")
        await client.disconnect()
        if retry_password >= 3:
            await message.answer("🚫 Too many wrong 2FA attempts. Please start over.", reply_markup=main_keyboard)
            await state.clear()

    except Exception as e:
        await message.answer("❌ Failed to login with 2FA. Please try again from the beginning.", reply_markup=main_keyboard)
        log_user_action(user_id, f"❌ 2FA login error: {e}")
        await client.disconnect()
        await state.clear()
