
# ================= البحث عن الثغرات (SearchSploit) =================
import subprocess


# ================= البحث عن الثغرات (SearchSploit) =================
import subprocess



import sqlite3
import os

def search_exploits(service_name):
    try:
        db_path = os.path.expanduser("~/exploitdb/exploitdb.db")
        if not os.path.exists(db_path):
            return [{"error": "قاعدة البيانات غير موجودة"}]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title, path FROM exploits WHERE title LIKE ? LIMIT 5", ('%' + service_name + '%',))
        rows = cursor.fetchall()
        conn.close()
        exploits = []
        for row in rows:
            exploits.append({"title": row[0], "path": row[1]})
        return exploits
    except Exception as e:
        return [{"error": str(e)}]

import os
import json
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "brain_memory.json")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")  # <--- تأكد من وضع مفتاحك هنا

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"target": "", "steps": [], "discoveries": []}

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ask_brain(prompt):
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": "أنت عقل مدبر لأداة أمنية. مهمتك تحليل المعلومات واقتراح الخطوة التالية. أجب بصيغة JSON فقط: {\"next_action\": \"nmap|sqlmap|curl|report\", \"reason\": \"...\", \"command\": \"...\"}"},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30)
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return json.dumps({"next_action": "error", "reason": str(e)})

def planner_agent(target):
    memory = load_memory()
    memory["target"] = target
    memory["steps"].append({"time": datetime.now().strftime("%H:%M:%S"), "agent": "Planner", "action": f"بدء التحقيق على {target}"})
    save_memory(memory)
    return memory

def scanner_agent(target):
    import subprocess
    memory = load_memory()
    try:
        result = subprocess.run(["nmap", "-p", "21,22,23,80,443,8080", "-T4", target], capture_output=True, text=True, timeout=30)
        open_ports = [line.split("/")[0] for line in result.stdout.splitlines() if "/tcp" in line and "open" in line]
        memory["discoveries"].append({"target": target, "ports": open_ports, "source": "Scanner"})
        memory["steps"].append({"time": datetime.now().strftime("%H:%M:%S"), "agent": "Scanner", "action": f"اكتشف {len(open_ports)} منفذ مفتوح"})
        save_memory(memory)
        return open_ports
    except Exception as e:
        return [str(e)]
