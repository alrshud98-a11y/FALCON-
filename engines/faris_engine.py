import platform, socket, shutil
from .base import BaseEngine

class FarisEngine(BaseEngine):
    name = "faris"
    description = "محرك الفارس — فحص شامل"

    def status(self):
        return {
            "name": self.name,
            "ready": True,
            "python": platform.python_version(),
            "hydra": bool(shutil.which("hydra")),
            "termux_api": bool(shutil.which("termux-wifi-scaninfo")),
            "whois": bool(shutil.which("whois")),
        }
