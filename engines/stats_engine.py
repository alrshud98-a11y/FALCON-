from .base import BaseEngine
import database

class StatsEngine(BaseEngine):
    name = "stats"
    description = "إحصائيات"

    def status(self):
        return {"name": self.name, "ready": True, "stats": database.stats()}
