import os, sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "data", "falcon.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, type TEXT, target TEXT,
        result TEXT, user TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS ip_lookups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, ip TEXT,
        country TEXT, city TEXT, isp TEXT, asn TEXT,
        lat REAL, lon REAL, whois TEXT, abuse TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS hydra_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, target TEXT, service TEXT,
        status TEXT, output TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, password_hash TEXT,
        role TEXT DEFAULT 'user', created TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, username TEXT, action TEXT, details TEXT)""")
    conn.commit()
    conn.close()

def log_scan(scan_type, target, result, user="system"):
    conn = get_conn()
    conn.execute("INSERT INTO scans (timestamp, type, target, result, user) VALUES (?,?,?,?,?)",
                 (datetime.now().isoformat(), scan_type, target, str(result), user))
    conn.commit(); conn.close()

def log_ip(ip, info):
    conn = get_conn()
    conn.execute("""INSERT INTO ip_lookups
        (timestamp, ip, country, city, isp, asn, lat, lon, whois, abuse)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (datetime.now().isoformat(), ip,
         info.get("country",""), info.get("city",""),
         info.get("isp",""), info.get("asn",""),
         info.get("lat",0), info.get("lon",0),
         info.get("whois",""), info.get("abuse","")))
    conn.commit(); conn.close()

def log_audit(username, action, details=""):
    conn = get_conn()
    conn.execute("INSERT INTO audit_log (timestamp, username, action, details) VALUES (?,?,?,?)",
                 (datetime.now().isoformat(), username, action, str(details)))
    conn.commit(); conn.close()

def recent_scans(limit=50):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def recent_ips(limit=50):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM ip_lookups ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def stats():
    conn = get_conn()
    total_scans = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
    total_ips = conn.execute("SELECT COUNT(*) FROM ip_lookups").fetchone()[0]
    total_hydra = conn.execute("SELECT COUNT(*) FROM hydra_runs").fetchone()[0]
    conn.close()
    return {"scans": total_scans, "ips": total_ips, "hydra": total_hydra}
