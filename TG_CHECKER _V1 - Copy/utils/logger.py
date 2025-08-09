# utils/logger.py

import logging
import os
from datetime import datetime

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure the logger
logging.basicConfig(
    filename=os.path.join("logs", "bot.log"),
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def log_user_action(user_id: int, message: str):
    """
    Logs a message with the user ID.
    """
    log_msg = f"[User {user_id}] {message}"
    print(log_msg)
    logging.info(log_msg)

def log_error(user_id: int, error: str):
    """
    Logs an error with the user ID.
    """
    log_msg = f"[User {user_id}] ❌ ERROR: {error}"
    print(log_msg)
    logging.error(log_msg)

# =============================
#  New batch-related functions
# =============================

def log_batch_start(user_id: int, batch_index: int, total_batches: int):
    """
    Logs the start of a batch.
    """
    log_user_action(user_id, f"🚀 Starting batch {batch_index}/{total_batches}")

def log_batch_complete(user_id: int, batch_index: int, total_batches: int, success: bool):
    """
    Logs the completion of a batch.
    """
    status = "✅ Completed" if success else "⚠️ Failed"
    log_user_action(user_id, f"{status} batch {batch_index}/{total_batches}")

def log_batch_retry(user_id: int, batch_index: int, attempt: int):
    """
    Logs a retry attempt for a batch.
    """
    log_user_action(user_id, f"🔄 Retrying batch {batch_index}, attempt {attempt}/3")

def log_session_cleanup(user_id: int):
    """
    Logs when a user's session is deleted after reaching the limit.
    """
    log_user_action(user_id, "🧹 Session auto-removed after limit reached")
