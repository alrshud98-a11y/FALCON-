import shutil, subprocess, re
from .base import BaseEngine

class HydraEngine(BaseEngine):
    name = "hydra"
    description = "محرك Hydra للفحص المصرح به"

    def status(self):
        path = shutil.which("hydra")
        if not path:
            return {"name": self.name, "ready": False, "message": "Hydra غير مثبتة"}
        try:
            r = subprocess.run([path, "-h"], capture_output=True, text=True, timeout=5)
            out = (r.stdout + r.stderr).strip()
            version = next((l.strip() for l in out.splitlines() if "Hydra" in l), "غير معروف")
            return {"name": self.name, "ready": True, "path": path, "version": version}
        except Exception as e:
            return {"name": self.name, "ready": False, "error": str(e)}

    def discover_modules(self):
        path = shutil.which("hydra")
        if not path:
            return {"success": False, "available": [], "unavailable": []}
        try:
            r = subprocess.run([path, "-h"], capture_output=True, text=True, timeout=10)
            out = r.stdout + "\n" + r.stderr
            supported = re.search(r"Supported services:\s*(.+)", out)
            missing = re.search(r"These services were not compiled in:\s*(.+)", out)
            return {
                "success": True,
                "available": supported.group(1).split() if supported else [],
                "unavailable": missing.group(1).split() if missing else []
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
