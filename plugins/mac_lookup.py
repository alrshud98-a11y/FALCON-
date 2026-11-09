PLUGIN_INFO = {
    "name": "mac_lookup",
    "version": "1.0",
    "description": "بحث عن مصنع MAC address"
}
import urllib.request, json
def run(mac):
    mac = mac.upper().replace("-", ":").replace(".", ":")
    if len(mac) < 8:
        return {"error": "MAC غير صحيح"}
    prefix = mac[:8]
    try:
        url = f"https://api.macvendors.com/{prefix}"
        with urllib.request.urlopen(url, timeout=8) as r:
            vendor = r.read().decode().strip()
        return {"mac": mac, "prefix": prefix, "vendor": vendor}
    except Exception as e:
        return {"mac": mac, "error": str(e)}
