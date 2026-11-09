import urllib.request
import urllib.parse
from html.parser import HTMLParser
from .base import BaseEngine

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href' and value:
                    self.links.add(value)

class CrawlerEngine(BaseEngine):
    name = "crawler"
    description = "محرك الزحف العنكبوتي"

    def status(self):
        return {"name": self.name, "ready": True}

    def crawl(self, url, max_depth=2):
        try:
            base_domain = urllib.parse.urlparse(url).netloc
            visited_urls = set()
            urls_with_params = set()
            to_visit = [(url, 0)]

            while to_visit:
                current_url, depth = to_visit.pop(0)
                if current_url in visited_urls: continue
                visited_urls.add(current_url)

                try:
                    req = urllib.request.Request(current_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=8) as response:
                        html = response.read().decode('utf-8', errors='ignore')
                    
                    parsed = urllib.parse.urlparse(current_url)
                    if parsed.query:
                        urls_with_params.add(current_url)

                    if depth >= max_depth: continue

                    parser = LinkExtractor()
                    parser.feed(html)
                    
                    for link in parser.links:
                        full_url = urllib.parse.urljoin(current_url, link)
                        parsed_link = urllib.parse.urlparse(full_url)
                        if parsed_link.netloc == base_domain and parsed_link.scheme in ('http', 'https'):
                            clean_url = urllib.parse.urlunparse(parsed_link._replace(fragment=''))
                            if clean_url not in visited_urls:
                                to_visit.append((clean_url, depth + 1))
                except Exception:
                    continue

            return {
                "success": True, 
                "url": url, 
                "total_scanned": len(visited_urls),
                "count": len(urls_with_params), 
                "urls": list(urls_with_params)[:20]
            }
        except Exception as e:
            return {"success": False, "message": f"خطأ: {str(e)}"}
