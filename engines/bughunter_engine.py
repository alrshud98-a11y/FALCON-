import urllib.request
import urllib.parse
from html.parser import HTMLParser
from .base import BaseEngine

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()
        self.forms = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href' and value:
                    self.links.add(value)
        elif tag == 'form':
            form = {"action": "", "method": "get"}
            for attr, value in attrs:
                if attr == 'action': form["action"] = value
                if attr == 'method': form["method"] = value.lower()
            self.forms.append(form)
            self.links.add(form["action"])

class BugHunterEngine(BaseEngine):
    name = "bughunter"
    def status(self): return {"name": self.name, "ready": True}

    def crawl_and_scan(self, base_url):
        # 1. جلب الصفحة الرئيسية
        try:
            req = urllib.request.Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as res:
                html = res.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return {"success": False, "message": f"فشل الاتصال: {str(e)}"}
        
        parser = LinkExtractor()
        parser.feed(html)
        
        base_domain = urllib.parse.urlparse(base_url).netloc
        candidate_urls = set()
        forms = parser.forms
        
        # إضافة الروابط التي تحتوي على متغيرات
        for link in parser.links:
            full_url = urllib.parse.urljoin(base_url, link)
            parsed = urllib.parse.urlparse(full_url)
            if parsed.netloc == base_domain and parsed.query:
                candidate_urls.add(full_url)
                
        # 2. محاولة الزحف إلى العمق (مستوى إضافي)
        deeper_links = list(candidate_urls)[:5] # أول 5 روابط فقط لتوفير الوقت
        for url in deeper_links:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as res:
                    sub_html = res.read().decode('utf-8', errors='ignore')
                sub_parser = LinkExtractor()
                sub_parser.feed(sub_html)
                for link in sub_parser.links:
                    full_url = urllib.parse.urljoin(url, link)
                    parsed = urllib.parse.urlparse(full_url)
                    if parsed.netloc == base_domain and parsed.query:
                        candidate_urls.add(full_url)
            except: pass

        if not candidate_urls and not forms:
            return {"success": False, "message": "لم يتم العثور على روابط أو نماذج قابلة للفحص."}

        results = []
        
        # 3. فحص الروابط (XSS و LFI)
        for url in candidate_urls:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            
            for param in params:
                # فحص XSS
                xss_payload = "<script>alert(1)</script>"
                test_params = params.copy()
                test_params[param] = [xss_payload]
                test_query = urllib.parse.urlencode(test_params, doseq=True)
                test_url = urllib.parse.urlunparse(parsed._replace(query=test_query))
                try:
                    req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as res:
                        body = res.read().decode('utf-8', errors='ignore')
                        if xss_payload in body:
                            results.append({"type": "XSS", "url": url, "param": param})
                except: pass
                
                # فحص LFI
                lfi_payload = "../../../../etc/passwd"
                test_params[param] = [lfi_payload]
                test_query = urllib.parse.urlencode(test_params, doseq=True)
                test_url = urllib.parse.urlunparse(parsed._replace(query=test_query))
                try:
                    req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as res:
                        body = res.read().decode('utf-8', errors='ignore')
                        if "root:x:0:0" in body:
                            results.append({"type": "LFI", "url": url, "param": param})
                except: pass

        # 4. فحص النماذج (POST) - محاكاة إرسال
        for form in forms:
            if form["action"] and form["method"] == "post":
                action_url = urllib.parse.urljoin(base_url, form["action"])
                # إرسال بيانات وهمية
                data = urllib.parse.urlencode({"test": "<script>alert(1)</script>"}).encode()
                try:
                    req = urllib.request.Request(action_url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as res:
                        body = res.read().decode('utf-8', errors='ignore')
                        if "<script>alert(1)</script>" in body:
                            results.append({"type": "XSS (POST)", "url": action_url, "param": "form"})
                except: pass

        return {
            "success": True, 
            "scanned_links": len(candidate_urls),
            "scanned_forms": len(forms),
            "vulnerable": len(results) > 0,
            "count": len(results),
            "details": results
        }
