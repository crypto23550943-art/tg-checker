# utils/client.py

from telethon import TelegramClient
from config import API_ID, API_HASH

def get_telethon_client(user_id: int) -> TelegramClient:
    session_path = f"sessions/{user_id}"
    return TelegramClient(session_path, API_ID, API_HASH)
