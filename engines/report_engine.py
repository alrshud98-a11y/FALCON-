import os, json, csv
from datetime import datetime
from .base import BaseEngine
import database

class ReportEngine(BaseEngine):
    name = "report"
    description = "توليد التقارير"

    def __init__(self):
        self.dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "data", "reports")
        os.makedirs(self.dir, exist_ok=True)

    def status(self):
        return {"name": self.name, "ready": True}

    def json_report(self, scans=True, ips=True):
        data = {"generated": datetime.now().isoformat()}
        if scans:
            data["scans"] = database.recent_scans(500)
        if ips:
            data["ip_lookups"] = database.recent_ips(500)
        path = os.path.join(self.dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True, "path": path}

    def csv_report(self):
        path = os.path.join(self.dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["type", "timestamp", "target", "result", "user"])
            for r in database.recent_scans(500):
                w.writerow([r["type"], r["timestamp"], r["target"], r["result"], r["user"]])
        return {"success": True, "path": path}

    def list_reports(self):
        return sorted(os.listdir(self.dir), reverse=True)[:20]
