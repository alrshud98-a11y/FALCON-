import subprocess, json
from .base import BaseEngine

class WifiEngine(BaseEngine):
    name = "wifi"
    description = "مركز قيادة الواي فاي"

    def status(self):
        return {"name": self.name, "ready": True}

    def scan_networks(self):
        try:
            res = subprocess.run(["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=15)
            if res.returncode != 0: 
                return {"success": False, "message": "فشل المسح. تأكد من صلاحيات الموقع."}
            
            networks = json.loads(res.stdout)
            result = []
            for net in networks:
                caps = net.get("capabilities", "")
                security = "مفتوحة 🔓" if "[WPA" not in caps and "[WEP" not in caps else "محمية 🔒"
                result.append({
                    "ssid": net.get("ssid", "مخفية") or "مخفية",
                    "bssid": net.get("bssid", "غير معروف"),
                    "signal": net.get("rssi", 0),
                    "security": security
                })
            return {"success": True, "count": len(result), "networks": result}
        except Exception as e:
            return {"success": False, "message": str(e)}
