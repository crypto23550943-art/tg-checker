# utils/session_utils.py
import sqlite3
import os
import logging
from telethon import TelegramClient
from data.config import API_ID, API_HASH

# Initialize logging
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "sessions.db"
os.makedirs("sessions", exist_ok=True)

def init_db():
    """Initialize the database with proper schema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                session_file TEXT,
                checks_done INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()

# Initialize database on import
init_db()

def get_telethon_client(user_id: int) -> TelegramClient:
    """Create a Telethon client for the user"""
    session_path = f"sessions/{user_id}.session"
    if not os.path.exists(session_path):
        raise FileNotFoundError(f"No session file for user {user_id}")
    return TelegramClient(
        session=session_path,
        api_id=API_ID,
        api_hash=API_HASH,
        connection_retries=3
    )

def increment_checks(user_id: int, count: int = 1):
    """Safely increment the check count"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions SET 
            checks_done = checks_done + ?,
            last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (count, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to increment checks: {e}")
        raise
    finally:
        conn.close()

def get_checks_done(user_id: int) -> int:
    """Get the current check count"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT checks_done FROM sessions WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        logger.error(f"Failed to get check count: {e}")
        return 0
    finally:
        conn.close()

def reset_user_check_count(user_id: int):
    """Reset the user's check count"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sessions SET 
            checks_done = 0,
            last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to reset check count: {e}")
        raise
    finally:
        conn.close()

def remove_session(user_id: int):
    """Remove the session file with error handling"""
    session_path = f"sessions/{user_id}.session"
    try:
        if os.path.exists(session_path):
            os.remove(session_path)
            logger.info(f"Removed session for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to remove session: {e}")
        raise