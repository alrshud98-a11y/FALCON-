import subprocess, json
from .base import BaseEngine

class SigintEngine(BaseEngine):
    name = "sigint"
    description = "محرك الاستطلاع الراديوي (Serving Cell)"

    def status(self):
        return {"name": self.name, "ready": True}

    def analyze_towers(self):
        try:
            # نستخدم cellinfo-brief لأنها أسرع وأقل طلباً للصلاحيات
            result = subprocess.run(["termux-telephony-cellinfo", "--brief"], capture_output=True, text=True, timeout=15)
            
            if result.returncode != 0 or not result.stdout.strip():
                # محاولة أخرى بدون brief
                result = subprocess.run(["termux-telephony-cellinfo"], capture_output=True, text=True, timeout=15)
                
            if result.returncode != 0:
                return {"success": False, "message": "فشل الاتصال بـ Termux:API أو لا توجد بيانات."}
            
            data = json.loads(result.stdout)
            anomalies = []
            normal_towers = []
            
            for cell in data:
                # في الإصدارات الحديثة، قد يكون البرج المسجل فقط هو المتاح
                mcc = str(cell.get("mcc", "—"))
                mnc = str(cell.get("mnc", "—"))
                dbm = cell.get("dbm", "—")
                registered = cell.get("registered", False)
                ctype = cell.get("type", "unknown")
                
                # تحليل بسيط: إذا كانت الإشارة قوية جداً (أقل من -30) فهي مشبوهة
                is_anomaly = False
                reasons = []
                
                if isinstance(dbm, (int, float)) and dbm > -30:
                    is_anomaly = True
                    reasons.append(f"إشارة قوية جداً ({dbm} dBm) - قد يكون جهاز اعتراض")
                
                # تحقق من MCC (السودان 602، مصر 602، إلخ)
                if mcc not in ["602", "603", "604", "605", "606", "—"]:
                    is_anomaly = True
                    reasons.append(f"كود دولة غريب (MCC: {mcc})")
                
                tower_info = {
                    "type": ctype,
                    "mcc": mcc, "mnc": mnc,
                    "lac": cell.get("lac", cell.get("tac", "—")),
                    "cid": cell.get("cid", cell.get("ci", "—")),
                    "dbm": dbm,
                    "registered": registered
                }
                
                if is_anomaly:
                    tower_info["reasons"] = reasons
                    anomalies.append(tower_info)
                else:
                    normal_towers.append(tower_info)
            
            return {
                "success": True,
                "total": len(data),
                "anomalies": anomalies,
                "normal": normal_towers,
                "status": "⚠️ تم اكتشاف شذوذ!" if anomalies else "✅ البيئة الراديوية آمنة"
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
