# utils/db.py
import sqlite3
import os

# Database file path
DB_PATH = "sessions.db"
CHECK_LIMIT = 120  # Max checks before session auto-removal


def has_session(user_id: int) -> bool:
    """
    Check if a Telegram session file exists for this user.
    """
    session_path = f"sessions/{user_id}.session"
    return os.path.exists(session_path)


def init_db():
    """
    Initialize the SQLite database and create the sessions table if it does not exist.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            user_id INTEGER PRIMARY KEY,
            session_file TEXT,
            checks_done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_session(user_id: int, session_file: str):
    """
    Add or replace a session for a user.
    Resets checks_done to 0 when a new session is added.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO sessions (user_id, session_file, checks_done)
        VALUES (?, ?, 0)
    """, (user_id, session_file))
    conn.commit()
    conn.close()


def get_session(user_id: int):
    """
    Retrieve the session file path for a given user_id.
    Returns None if not found.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT session_file FROM sessions WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def increment_checks(user_id: int, count: int):
    """
    Increment the checks_done count for a user by 'count'.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE sessions
        SET checks_done = checks_done + ?
        WHERE user_id = ?
    """, (count, user_id))
    conn.commit()
    conn.close()


def get_checks_done(user_id: int):
    """
    Get the number of checks already done by the user.
    Returns 0 if the user does not exist.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT checks_done FROM sessions WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def delete_session(user_id: int):
    """
    Delete the session for a user.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# === New Aliases for session_utils.py compatibility ===

def save_check_count(user_id: int, count: int):
    """
    Set the exact number of checks done for a user.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE sessions
        SET checks_done = ?
        WHERE user_id = ?
    """, (count, user_id))
    conn.commit()
    conn.close()


def increment_check_count(user_id: int, increment: int = 1):
    """
    Increment the check count by a given amount (default 1).
    """
    increment_checks(user_id, increment)


def get_check_count(user_id: int) -> int:
    """
    Retrieve the number of checks already done by the user.
    """
    return get_checks_done(user_id)


def has_reached_limit(user_id: int) -> bool:
    """
    Check if the user has reached the CHECK_LIMIT.
    """
    return get_check_count(user_id) >= CHECK_LIMIT


def reset_user_check_count(user_id: int):
    """
    Reset the user's check count to zero.
    """
    save_check_count(user_id, 0)

    init_db()
