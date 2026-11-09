import urllib.request
import urllib.parse
from .base import BaseEngine

class SqliEngine(BaseEngine):
    name = "sqli"
    description = "محرك فحص ثغرات حقن SQL"

    def status(self):
        return {"name": self.name, "ready": True}

    def scan(self, url):
        payloads = [
            "'", "\"", "' OR '1'='1", "' OR 1=1--", "1' ORDER BY 1--", "1' UNION SELECT null--"
        ]
        errors = {
            "mysql": ["you have an error in your sql syntax", "warning: mysql"],
            "sqlite": ["sqlite error", "sql logic error"],
            "postgres": ["postgresql", "syntax error at or near"],
            "mssql": ["microsoft odbc", "sql server", "unclosed quotation mark"]
        }
        results = []
        for p in payloads:
            try:
                test_url = url + p
                req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    body = response.read().decode('utf-8', errors='ignore').lower()
                    for db_type, keywords in errors.items():
                        for kw in keywords:
                            if kw in body:
                                results.append({"payload": p, "db": db_type, "evidence": kw, "status": "vulnerable"})
                                break
            except Exception as e:
                if "500" in str(e):
                    results.append({"payload": p, "db": "unknown", "evidence": "HTTP 500 Error", "status": "suspicious"})
                continue
        unique_results = []
        seen = set()
        for r in results:
            key = str(r["payload"]) + r["db"]
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        return {"success": True, "url": url, "vulnerable": len(unique_results) > 0, "count": len(unique_results), "details": unique_results}
