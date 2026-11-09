from flask import Flask, render_template_string, jsonify, request
from file_manager import list_files, upload_file, delete_file
import subprocess
import shutil
import json
import os
from datetime import datetime

app = Flask(__name__)
HISTORY = os.path.join(os.path.dirname(__file__), "history.json")

def save_history(kind, result):
    try:
        data = []
        if os.path.exists(HISTORY):
            with open(HISTORY, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": kind,
            "result": result
        })
        with open(HISTORY, "w", encoding="utf-8") as f:
            json.dump(data[:100], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def hydra_status():
    path = shutil.which("hydra")
    if not path:
        return {
            "installed": False,
            "message": "Hydra غير مثبتة أو غير موجودة في PATH"
        }

    try:
        result = subprocess.run(
            [path, "-h"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        lines = [x.strip() for x in output.splitlines() if x.strip()]
        version = next(
            (x for x in lines if "Hydra" in x or "hydra" in x),
            "تعذر تحديد الإصدار"
        )
        return {
            "installed": True,
            "path": path,
            "version": version,
            "message": "تم اكتشاف Hydra بنجاح"
        }
    except Exception as e:
        return {
            "installed": True,
            "path": path,
            "message": "الأداة موجودة لكن تعذر قراءة معلوماتها: " + str(e)
        }

def wifi_scan():
    try:
        result = subprocess.run(
            ["termux-wifi-scaninfo"],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode != 0:
            return {"success": False, "message": result.stderr.strip()}

        networks = json.loads(result.stdout or "[]")
        save_history("Wi-Fi", "تم إجراء مسح للشبكات")
        return {
            "success": True,
            "count": len(networks),
            "networks": networks,
            "message": "اكتمل المسح"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "message": "لم يتم العثور على Termux:API أو أمر المسح"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FALCON Security</title>
<style>
*{box-sizing:border-box}
:root{color-scheme:dark}
body{
 margin:0;background:radial-gradient(circle at top,#123452,#07111f 55%);
 color:#edf5ff;font-family:Arial,sans-serif;padding:16px;
 max-width:850px;margin:auto
}
header{text-align:center;padding:28px 5px}
.logo{font-size:44px;font-weight:bold;color:#00c8ff;text-shadow:0 0 22px #008cff}
.sub{color:#9bb8d2;font-size:14px;margin-top:8px}
.card{
 background:linear-gradient(145deg,#122d47,#0b1d30);
 border:1px solid #20577e;border-radius:17px;
 padding:19px;margin:15px 0;
 box-shadow:0 8px 24px #0004
}
h3{margin-top:0;color:#48c4ff;font-size:18px}
button{
 width:100%;border:1px solid #159ee8;border-radius:11px;
 background:linear-gradient(90deg,#006fc4,#009fe8);
 color:white;padding:14px;font-size:16px;margin-top:10px;
 font-weight:bold
}
button:active{background:#00558f}
input{max-width:100%;margin-top:12px;color:white}
.status{
 padding:12px;border-radius:10px;background:#081a2b;
 margin:10px 0;overflow-wrap:anywhere;border:1px solid #183c59
}
.ok{color:#45e39a}.bad{color:#ff8585}
small{color:#9ab2ca;display:block;margin-top:10px}
.network{
 background:#091a2c;border:1px solid #183b57;
 border-radius:10px;padding:13px;margin:9px 0;
 text-align:right;overflow-wrap:anywhere
}
footer{text-align:center;color:#66839f;padding:24px;font-size:12px}
</style>
</head>
<body>
<header>
<div class="logo">🦅 FALCON</div>
<div class="sub">منصة الأمن السيبراني | PROFESSIONAL</div>
</header>

<div class="card">
<h3>لوحة التحكم</h3>
<div class="status">حالة المنصة: <span class="ok">تعمل محلياً</span></div>
<div class="status">اللغة: العربية</div>
<div class="status">بيئة التشغيل: Termux Android</div>
</div>

<div class="card">
<h3>🛡️ أداة Hydra</h3>
<div id="hydraStatus" class="status">جارٍ فحص الأداة...</div>
<button onclick="checkHydra()">فحص Hydra</button>
<small>يعرض حالة التثبيت ومعلومات الأداة فقط.</small>
</div>

<div class="card">
<h3>📡 ماسح Wi-Fi</h3>
<div id="wifiStatus" class="status">جاهز للمسح</div>
<button onclick="scanWifi()">ابدأ البحث عن الشبكات</button>
<div id="networks"></div>
</div>

<div class="card">
<h3>📋 سجل العمليات</h3>
<div id="history">لا توجد عمليات معروضة حالياً.</div>
<button onclick="loadHistory()">عرض السجل</button>
</div>

<div class="card">
<h3>📁 مدير الملفات</h3>
<div id="filesList" class="status">جارٍ تحميل الملفات...</div>
<input type="file" id="fileInput" accept=".txt,.log,.json,.csv,.md">
<button onclick="uploadFile()">رفع ملف</button>
</div>

<footer>FALCON SECURITY SYSTEM</footer>

<script>
async function checkHydra(){
 const box=document.getElementById("hydraStatus");
 box.textContent="جارٍ فحص Hydra...";
 try{
  const r=await fetch("/api/hydra");
  const d=await r.json();
  if(d.installed){
   box.innerHTML='<span class="ok">الأداة مثبتة</span><br>'+d.message+
   '<br>المسار: '+d.path+'<br>المعلومات: '+(d.version||"غير متاحة");
  }else{
   box.innerHTML='<span class="bad">الأداة غير موجودة</span><br>'+d.message;
  }
 }catch(e){box.textContent="تعذر الاتصال بالخادم";}
}

async function scanWifi(){
 const box=document.getElementById("wifiStatus");
 const list=document.getElementById("networks");
 box.textContent="جارٍ البحث...";
 list.innerHTML="";
 try{
  const r=await fetch("/api/wifi");
  const d=await r.json();
  if(!d.success){box.textContent=d.message;return;}
  box.textContent="تم العثور على "+d.count+" شبكة";
  if(d.count===0){
   list.textContent="لم تظهر شبكات. تأكد من تشغيل Wi-Fi والموقع وإذن Termux:API.";
  }
  d.networks.forEach(n=>{
   const item=document.createElement("div");
   item.className="network";
   item.textContent="الشبكة: "+(n.ssid||"مخفية")+
   " | الإشارة: "+(n.rssi??"غير متاحة")+
   " | التردد: "+(n.frequency_mhz??"غير متاح")+" MHz"+
   " | BSSID: "+(n.bssid||"غير متاح");
   list.appendChild(item);
  });
 }catch(e){box.textContent="حدث خطأ أثناء المسح";}
}

async function loadHistory(){
 const box=document.getElementById("history");
 try{
  const r=await fetch("/api/history");
  const d=await r.json();
  box.textContent="";
  if(!d.length){box.textContent="لا توجد عمليات محفوظة.";return;}
  d.forEach(x=>{
   const item=document.createElement("div");
   item.className="network";
   item.textContent=x.time+" | "+x.type+" | "+x.result;
   box.appendChild(item);
  });
 }catch(e){box.textContent="تعذر تحميل السجل";}
}


async function loadFiles(){
 const box=document.getElementById("filesList");
 try{
  const r=await fetch("/api/files");
  const files=await r.json();
  box.innerHTML="";
  if(!files.length){
   box.textContent="لا توجد ملفات حالياً";
   return;
  }
  files.forEach(f=>{
   const item=document.createElement("div");
   item.className="network";
   const name=document.createElement("span");
   name.textContent=f.name+" ("+f.size+" بايت)";
   const del=document.createElement("button");
   del.textContent="حذف";
   del.onclick=()=>deleteFile(f.name);
   item.appendChild(name);
   item.appendChild(del);
   box.appendChild(item);
  });
 }catch(e){
  box.textContent="تعذر تحميل الملفات";
 }
}

async function uploadFile(){
 const input=document.getElementById("fileInput");
 if(!input.files.length){
  alert("اختر ملفاً أولاً");
  return;
 }
 const data=new FormData();
 data.append("file",input.files[0]);
 try{
  const r=await fetch("/api/files",{method:"POST",body:data});
  const result=await r.json();
  alert(result.message||result.error);
  input.value="";
  loadFiles();
 }catch(e){
  alert("تعذر رفع الملف");
 }
}

async function deleteFile(name){
 if(!confirm("هل تريد حذف الملف؟"))return;
 try{
  const r=await fetch("/api/files/"+encodeURIComponent(name),{method:"DELETE"});
  const result=await r.json();
  alert(result.message||result.error);
  loadFiles();
 }catch(e){
  alert("تعذر حذف الملف");
 }
}

loadFiles();

checkHydra();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/hydra")
def api_hydra():
    return jsonify(hydra_status())

@app.route("/api/wifi")
def api_wifi():
    return jsonify(wifi_scan())

@app.route("/api/history")
def api_history():
    try:
        with open(HISTORY, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify([])


@app.route("/api/files", methods=["GET"])
def api_files():
    return jsonify(list_files())

@app.route("/api/files", methods=["POST"])
def api_upload():
    result, status = upload_file(request.files.get("file"))
    return jsonify(result), status

@app.route("/api/files/<name>", methods=["DELETE"])
def api_delete(name):
    result, status = delete_file(name)
    return jsonify(result), status

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
