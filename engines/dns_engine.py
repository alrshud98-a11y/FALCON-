import socket
from .base import BaseEngine

class DnsEngine(BaseEngine):
    name = "dns"
    description = "استعلامات DNS"

    def status(self):
        return {"name": self.name, "ready": True}

    def resolve(self, hostname):
        results = {"success": True, "hostname": hostname, "a": [], "aaaa": [], "cname": None}
        try:
            for family, _, _, _, sockaddr in socket.getaddrinfo(hostname, None):
                ip = sockaddr[0]
                if family == socket.AF_INET and ip not in results["a"]:
                    results["a"].append(ip)
                elif family == socket.AF_INET6 and ip not in results["aaaa"]:
                    results["aaaa"].append(ip)
        except Exception as e:
            results = {"success": False, "message": str(e), "hostname": hostname}
        return results

    def reverse(self, ip):
        try:
            host, aliases, _ = socket.gethostbyaddr(ip)
            return {"success": True, "ip": ip, "hostname": host, "aliases": aliases}
        except Exception as e:
            return {"success": False, "ip": ip, "message": str(e)}
