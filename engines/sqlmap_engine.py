import subprocess
import shutil
from .base import BaseEngine

class SqlmapEngine(BaseEngine):
    name = "sqlmap"
    description = "محرك فحص واستغلال ثغرات SQL"

    def status(self):
        path = shutil.which("sqlmap")
        return {"name": self.name, "ready": bool(path)}

    def scan(self, url, level=1, action="scan"):
        sqlmap = shutil.which("sqlmap")
        if not sqlmap:
            return {"success": False, "message": "SQLMap غير مثبتة."}

        # الأوامر الأساسية
        cmd = [sqlmap, "-u", url, "--batch", "--level", str(level), "--risk", "1",
               "--output-dir", "/data/data/com.termux/files/home/FALCON/data/sqlmap_output"]

        # إضافة أوامر الاستغلال
        if action == "tables":
            cmd.append("--tables")
        elif action == "dump":
            cmd.append("--dump")
        elif action == "passwords":
            cmd.append("--passwords")
        elif action == "dbs":
            cmd.append("--dbs")
        else:
            cmd.append("--flush-session") # فحص عادي

        try:
            # زيادة وقت المهلة لأن سحب البيانات يطول
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            output = result.stdout + "\n" + result.stderr
            vulnerable = "vulnerable" in output.lower() or "injectable" in output.lower() or "fetched data" in output.lower()
            
            return {
                "success": True,
                "url": url,
                "vulnerable": vulnerable,
                "action": action,
                "raw_output": output
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "العملية استغرقت وقتاً طويلاً (تجاوزت 5 دقائق)."}
        except Exception as e:
            return {"success": False, "message": str(e)}
