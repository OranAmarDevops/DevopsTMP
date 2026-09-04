import json
import logging
import os
import threading
from settings import load_settings


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
storage_settings = load_settings("backend")["storage"]
logger = logging.getLogger(__name__)

configured_users_file = storage_settings["users_file"]
USERS_FILE = (
    configured_users_file
    if os.path.isabs(configured_users_file)
    else os.path.join(PROJECT_ROOT, configured_users_file)
)

os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
_file_lock = threading.Lock()

if not os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except OSError:
        logger.exception(
            "Failed to initialize users file; file=%s",
            USERS_FILE
        )
        raise


def _load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        logger.exception(
            "Failed to read users JSON; file=%s",
            USERS_FILE
        )
        raise

def _save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except OSError:
        logger.exception(
            "Failed to write users JSON; file=%s",
            USERS_FILE
        )
        raise

def register_user(username, password):
    with _file_lock:
        users = _load_users()
        if any(u["username"] == username for u in users):
            return False
        users.append({"username": username, "password": password})
        _save_users(users)
        return True

def login_user(username, password):
    with _file_lock:
        users = _load_users()
        return any(u["username"] == username and u["password"] == password for u in users)
