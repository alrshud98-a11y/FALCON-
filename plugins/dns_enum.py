PLUGIN_INFO = {
    "name": "dns_enum",
    "version": "1.0",
    "description": "تعداد DNS لعدة نطاقات فرعية"
}
import socket
SUBDOMAINS = ["www", "mail", "ftp", "admin", "api", "dev", "test", "blog", "shop", "app"]
def run(domain):
    found = []
    for sub in SUBDOMAINS:
        host = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(host)
            found.append({"host": host, "ip": ip})
        except Exception:
            pass
    return {"domain": domain, "found": found, "count": len(found)}
