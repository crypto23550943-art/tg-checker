# data/config.py
import os
from dotenv import load_dotenv

load_dotenv()

def get_env(var_name, default=None, required=False):
    value = os.getenv(var_name, default)
    if required and not value:
        raise EnvironmentError(f"Required env variable '{var_name}' is missing.")
    return value

BOT_TOKEN = get_env("BOT_TOKEN", default=None, required=False)
API_ID = int(get_env("API_ID", 0))
API_HASH = get_env("API_HASH", "")
MAX_CHECKS_PER_SESSION = int(get_env("MAX_CHECKS_PER_SESSION", 120))
