class BaseEngine:
    name = "base"
    description = "محرك أساسي"
    def status(self):
        return {"name": self.name, "description": self.description, "ready": True}
