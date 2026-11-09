import urllib.request
import urllib.parse
from .base import BaseEngine

class BrainEngine(BaseEngine):
    name = "brain"
    def status(self): return {"name": self.name, "ready": True}

    def ask_ai(self, prompt):
        system_prompt = "أنت العراب، مساعد أمن سيبراني ذكي. أجب بالعربية باختصار. السؤال: "
        full_prompt = f"{system_prompt}{prompt}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://text.pollinations.ai/{encoded_prompt}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=40) as response:
                return response.read().decode('utf-8').strip()
        except Exception:
            return "⚠️ الشبكة بطيئة. أعد المحاولة."

    def process_command(self, text):
        text_lower = text.lower().strip()
        
        # الأوامر المحلية (سريعة وبدون إنترنت)
        if "افحص النظام" in text_lower: return {"action": "chat", "reply": "✅ النظام يعمل."}
        if "nmap" in text_lower or "منافذ" in text_lower: return {"action": "navigate", "target": "/ports", "reply": "جاري فتح المنافذ..."}
        if "شبك" in text_lower or "wifi" in text_lower: return {"action": "navigate", "target": "/network", "reply": "جاري فتح الشبكة..."}
        if "هيدرا" in text_lower or "hydra" in text_lower: return {"action": "navigate", "target": "/hydra", "reply": "جاري فتح Hydra..."}
        
        # إذا لم يكن أمراً محلياً، استخدم الإنترنت
        return {"action": "chat", "reply": self.ask_ai(text)}
