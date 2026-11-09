import os, json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
    "session_timeout": 3600,
    "log_level": "INFO",
    "password_min_length": 6,
    "max_history": 100,
    "theme": "dark",
    "admin_username": "admin",
    "ip_api_timeout": 8,
    "abuseipdb_key": "",
    "virustotal_key": "",
    "telegram_token": "",
    "telegram_chat_id": "",
    "email_smtp": "",
    "email_port": 587,
    "email_user": "",
    "email_password": "",
    "email_to": "",
}

def load():
    if not os.path.exists(CONFIG_FILE):
        save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        merged.update(data)
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass

def get(key, default=None):
    return load().get(key, default)
