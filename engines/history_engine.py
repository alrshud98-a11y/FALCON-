import os, json
from datetime import datetime
from .base import BaseEngine
import config

class HistoryEngine(BaseEngine):
    name = "history"
    description = "سجل العمليات"

    def __init__(self):
        self.file = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "history.json")

    def status(self):
        return {"name": self.name, "ready": True, "file": self.file}

    def add(self, kind, result):
        try:
            data = self.list()
            data.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "type": kind, "result": str(result)})
            with open(self.file, "w", encoding="utf-8") as f:
                json.dump(data[:config.get("max_history", 100)], f,
                          ensure_ascii=False, indent=2)
        except Exception:
            pass

    def list(self):
        if not os.path.exists(self.file):
            return []
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
