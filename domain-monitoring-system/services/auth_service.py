import json
import os
import threading
from settings import load_settings


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
storage_settings = load_settings()["storage"]

configured_users_file = storage_settings["users_file"]
USERS_FILE = (
    configured_users_file
    if os.path.isabs(configured_users_file)
    else os.path.join(PROJECT_ROOT, configured_users_file)
)

os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
_file_lock = threading.Lock()

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)


def _load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

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
