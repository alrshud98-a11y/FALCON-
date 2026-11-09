import socket
import ipaddress
import concurrent.futures
from .base import BaseEngine

class DiscoveryEngine(BaseEngine):
    name = "discovery"
    description = "محرك الاكتشاف الشامل وبصمات الخدمات"

    def status(self):
        return {"name": self.name, "ready": True}

    def scan_host(self, ip, ports=[21, 22, 23, 25, 80, 443, 445, 3306, 3389, 8080]):
        """فحص جهاز واحد: هل هو حي؟ وما هي منافذه المفتوحة؟"""
        open_ports = []
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((str(ip), port)) == 0:
                    open_ports.append(port)
                s.close()
            except:
                pass
        if open_ports:
            return {"ip": str(ip), "open_ports": open_ports}
        return None

    def discover_subnet(self, cidr):
        """اكتشاف كل الأجهزة الحية في نطاق شبكة (شبيه بـ Netdiscover)"""
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except Exception as e:
            return {"success": False, "message": "نطاق IP غير صحيح. استخدم مثلاً 192.168.1.0/24"}

        hosts = list(network.hosts())
        if len(hosts) > 256:
            hosts = hosts[:256] # حماية من الفحص الزائد

        discovered = []
        # استخدام الخيوط (Threads) لفحص سريع
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(self.scan_host, ip): ip for ip in hosts}
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res:
                    discovered.append(res)

        return {"success": True, "network": cidr, "alive_count": len(discovered), "devices": discovered}

    def grab_banner(self, ip, port):
        """سحب شعار الخدمة (Banner Grabbing) لمعرفة نوع السيرفر"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((ip, port))
            s.send(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
            banner = s.recv(1024).decode('utf-8', errors='ignore')
            s.close()
            
            # تنظيف الشعار
            server = "غير معروف"
            for line in banner.split("\n"):
                if line.lower().startswith("server:"):
                    server = line.strip()
                    break
            return {"success": True, "ip": ip, "port": port, "banner": banner[:500], "server": server}
        except Exception as e:
            return {"success": False, "message": "تعذر سحب الشعار (الخدمة قد تكون لا تدعم HTTP)"}
