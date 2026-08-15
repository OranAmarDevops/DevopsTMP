import json
import os
import threading
from settings import load_settings

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
storage_settings = load_settings()["storage"]

configured_data_dir = storage_settings["data_dir"]
DATA_DIR = (
    configured_data_dir
    if os.path.isabs(configured_data_dir)
    else os.path.join(PROJECT_ROOT, configured_data_dir)
)

os.makedirs(DATA_DIR, exist_ok=True)

_locks = {}
_locks_lock = threading.Lock()

def _get_lock(username):
    with _locks_lock:
        if username not in _locks:
            _locks[username] = threading.Lock()
        return _locks[username]

def _get_domains_file(username):
    return os.path.join(
        DATA_DIR,
        f"{username}_domains.json"
    )

def _load_domains(username):
    file = _get_domains_file(username)
    if not os.path.exists(file):
        return []
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_domains(username, domains):
    file = _get_domains_file(username)
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(domains, f, indent=2)

def remove_all_domains(username):
    with _get_lock(username):
        _save_domains(username, [])
        return True

def remove_domain(username, domain):
    with _get_lock(username):
        domains = _load_domains(username)
        new_domains = [d for d in domains if d["domain"] != domain]
        if len(new_domains) == len(domains):
            return False
        _save_domains(username, new_domains)
        return True

def add_domain(username, domain):
    with _get_lock(username):
        domains = _load_domains(username)
        if any(d["domain"] == domain for d in domains):
            return False
        domains.append({
            "domain": domain,
            "status": "Pending",
            "ssl_expiration": "N/A",
            "ssl_issuer": "N/A"
        })
        _save_domains(username, domains)
        return True
