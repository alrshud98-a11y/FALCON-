import subprocess
import shutil
from .base import BaseEngine

class PortEngine(BaseEngine):
    name = "port"
    description = "محرك فحص المنافذ والثغرات باستخدام Nmap"

    def status(self):
        nmap_path = shutil.which("nmap")
        return {"name": self.name, "ready": bool(nmap_path), "nmap": bool(nmap_path)}

    def scan(self, host, scan_mode="fast"):
        nmap = shutil.which("nmap")
        if not nmap:
            return {"success": False, "message": "أداة nmap غير مثبتة. شغّل: pkg install nmap"}

        cmd = [nmap]
        
        if scan_mode == "fast":
            cmd.extend(["-sV", "-T4", "--top-ports", "100", host])
        
        elif scan_mode == "aggressive":
            cmd.extend(["-A", "-T4", "-p-", host])
            
        elif scan_mode == "vuln":
            # فحص الثغرات الشائعة (Vulnerabilities) في المنافذ المكتشفة
            # نستخدم -sV لاكتشاف الإصدار، ثم سكريبتات vuln
            cmd.extend(["-sV", "--script", "vuln", "-T4", host])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stdout
            
            open_ports = []
            for line in output.splitlines():
                if "/tcp" in line and "open" in line:
                    parts = line.split()
                    if len(parts) > 0:
                        open_ports.append(parts[0])

            return {
                "success": True,
                "host": host,
                "open_ports": open_ports,
                "count": len(open_ports),
                "raw_output": output
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "الفحص استغرق وقتاً طويلاً (تجاوز 5 دقائق)."}
        except Exception as e:
            return {"success": False, "message": str(e)}
