import os, json, hashlib, secrets, time
from functools import wraps
from flask import session, redirect, url_for, jsonify
import config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_FILE = os.path.join(BASE_DIR, "auth.json")

def _hash(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${h.hex()}"

def _verify(password, stored):
    try:
        salt, _ = stored.split("$", 1)
        return _hash(password, salt) == stored
    except Exception:
        return False

def _load():
    if not os.path.exists(AUTH_FILE):
        return {}
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save(data):
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(AUTH_FILE, 0o600)
    except Exception:
        pass

def is_configured():
    return bool(_load().get("password_hash"))

def setup_password(password):
    min_len = config.get("password_min_length", 6)
    if len(password) < min_len:
        return False, f"كلمة المرور قصيرة (الحد {min_len})"
    _save({"password_hash": _hash(password), "created": int(time.time())})
    return True, "تم حفظ كلمة المرور"

def check_password(password):
    stored = _load().get("password_hash")
    return bool(stored and _verify(password, stored))

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not is_configured():
            return jsonify({"error": "لم يتم إعداد كلمة المرور"}), 503
        if not session.get("authenticated"):
            return redirect(url_for("login_page"))
        timeout = config.get("session_timeout", 3600)
        last = session.get("last_activity", 0)
        if time.time() - last > timeout:
            session.clear()
            return redirect(url_for("login_page"))
        session["last_activity"] = time.time()
        return f(*args, **kwargs)
    return wrapped

LOGIN_HTML = """<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FALCON — دخول</title>
<style>*{box-sizing:border-box}body{margin:0;min-height:100vh;
background:radial-gradient(circle at top,#123452,#07111f 55%);
color:#edf5ff;font-family:Arial,sans-serif;display:flex;
align-items:center;justify-content:center;padding:20px}
.box{width:100%;max-width:380px;background:linear-gradient(145deg,#122d47,#0b1d30);
border:1px solid #20577e;border-radius:17px;padding:30px;box-shadow:0 8px 24px #0008}
.eagle{text-align:center;font-size:64px;filter:drop-shadow(0 0 15px #00aaff)}
.logo{text-align:center;font-size:38px;font-weight:900;color:#00c8ff;
letter-spacing:4px;text-shadow:0 0 20px #008cff;margin:6px 0}
.sub{text-align:center;color:#9bb8d2;font-size:13px;margin-bottom:24px}
input{width:100%;padding:14px;border-radius:11px;border:1px solid #159ee8;
background:#081a2b;color:white;font-size:16px;margin-bottom:12px}
button{width:100%;padding:14px;border-radius:11px;border:none;
background:linear-gradient(90deg,#006fc4,#009fe8);color:white;
font-size:16px;font-weight:bold;cursor:pointer}
.err{color:#ff8585;text-align:center;margin-top:14px;min-height:20px}
.foot{text-align:center;color:#66839f;margin-top:20px;font-size:11px}</style>
</head><body><div class="box">
<div class="eagle">🦅</div><div class="logo">FALCON</div>
<div class="sub">أدخل كلمة المرور</div>
<form method="POST" action="/login">
<input type="password" name="password" placeholder="كلمة المرور" autofocus required>
<button type="submit">دخول</button></form>
<div class="err">{{ error }}</div>
<div class="foot">FALCON PROFESSIONAL</div>
</div></body></html>"""
