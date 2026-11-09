import shutil, subprocess, json, socket
from .base import BaseEngine

class NetworkEngine(BaseEngine):
    name = "network"
    description = "محرك فحص الشبكة المحلية المصرح به"

    def status(self):
        api = shutil.which("termux-wifi-scaninfo")
        return {"name": self.name, "ready": bool(api), "termux_api": bool(api)}

    def scan_wifi(self):
        if not shutil.which("termux-wifi-scaninfo"):
            return {"success": False, "message": "ثبّت termux-api"}
        try:
            r = subprocess.run(["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=15)
            if r.returncode != 0:
                return {"success": False, "message": r.stderr.strip()}
            nets = json.loads(r.stdout or "[]")
            return {"success": True, "count": len(nets), "networks": nets}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def arp_scan(self):
        try:
            r = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=10)
            devices = []
            for line in r.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[1] == "dev":
                    ip = parts[0]
                    mac = "?"
                    for i, p in enumerate(parts):
                        if p == "lladdr":
                            mac = parts[i+1]
                    devices.append({"ip": ip, "mac": mac})
            return {"success": True, "count": len(devices), "devices": devices}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def local_ips(self):
        ips = []
        try:
            for item in socket.getaddrinfo(socket.gethostname(), None):
                a = item[4][0]
                if a not in ("127.0.0.1", "::1") and a not in ips:
                    ips.append(a)
        except Exception:
            pass
        return ips
