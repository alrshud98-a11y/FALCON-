import json, urllib.request, socket, subprocess
from .base import BaseEngine
import config

class IPTracker(BaseEngine):
    name = "ip_tracker"
    description = "تتبع معلومات IP العامة (مصرح)"

    def status(self):
        return {"name": self.name, "ready": True}

    def lookup(self, ip):
        result = {"ip": ip, "success": True}

        # 1. GeoIP عبر ip-api.com (مجاني)
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as,lat,lon,query"
            timeout = config.get("ip_api_timeout", 8)
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                result.update({
                    "country": data.get("country", ""),
                    "city": data.get("city", ""),
                    "isp": data.get("isp", ""),
                    "org": data.get("org", ""),
                    "asn": data.get("as", ""),
                    "lat": data.get("lat", 0),
                    "lon": data.get("lon", 0),
                })
            else:
                result["geo_error"] = "فشل الاستعلام"
        except Exception as e:
            result["geo_error"] = str(e)

        # 2. Reverse DNS
        try:
            host, aliases, _ = socket.gethostbyaddr(ip)
            result["reverse_dns"] = host
        except Exception:
            result["reverse_dns"] = None

        # 3. WHOIS (إن توفر)
        try:
            r = subprocess.run(["whois", ip], capture_output=True, text=True, timeout=15)
            result["whois"] = r.stdout[:2000] if r.stdout else ""
        except Exception:
            result["whois"] = ""

        return result
