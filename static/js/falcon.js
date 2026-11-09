async function api(url, options={}){
  try{
    const r = await fetch(url, options);
    if(r.redirected && r.url.includes("/login")){
      window.location.href = "/login"; return null;
    }
    if(!r.ok && r.status === 503){
      const d = await r.json(); alert(d.error || "خدمة غير متاحة"); return null;
    }
    return await r.json();
  }catch(e){
    console.error("API error:", e); return {error: String(e)};
  }
}
function setText(id, txt){ const el=document.getElementById(id); if(el) el.textContent=txt; }
function setHTML(id, html){ const el=document.getElementById(id); if(el) el.innerHTML=html; }
function setLoading(id, msg="جارٍ..."){
  setHTML(id, '<span class="spinner"></span>'+msg);
}
async function getHydra(){
  setLoading("hydraResult","جارٍ فحص Hydra...");
  const d = await api("/api/hydra");
  if(!d) return;
  const el = document.getElementById("hydraResult");
  if(!el) return;
  if(d.installed){
    el.innerHTML = '<span class="badge ok">✅ مثبتة</span><br>'+
      'المسار: '+d.path+'<br>الإصدار: '+(d.version||"—");
  }else{
    el.innerHTML = '<span class="badge bad">❌ غير مثبتة</span><br>'+d.message;
  }
}
async function scanWifi(){
  setLoading("wifiResult","جارٍ المسح...");
  const d = await api("/api/wifi");
  if(!d) return;
  const el = document.getElementById("wifiResult");
  if(!d.success){
    el.innerHTML = '<span class="alert err">'+d.message+'</span>'; return;
  }
  el.innerHTML = '<span class="badge ok">'+d.count+' شبكة</span>';
  let html = "";
  d.networks.forEach(n=>{
    html += '<div class="list-item">📶 '+(n.ssid||"مخفية")+
      ' | إشارة: '+(n.rssi??"—")+
      ' | تردد: '+(n.frequency_mhz??"—")+' MHz</div>';
  });
  setHTML("wifiList", html);
}
async function scanArp(){
  setLoading("arpResult","جارٍ فحص الأجهزة...");
  const d = await api("/api/arp");
  if(!d || !d.success){ setText("arpResult", d?.message || "فشل"); return; }
  setHTML("arpResult", '<span class="badge ok">'+d.count+' جهاز</span>');
  let html = "";
  d.devices.forEach(x=>{
    html += '<div class="list-item">💻 IP: '+x.ip+' | MAC: '+x.mac+'</div>';
  });
  setHTML("arpList", html);
}
async function scanPorts(){
  const host = document.getElementById("portHost").value.trim();
  if(!host){ alert("أدخل عنوان IP أو hostname"); return; }
  setLoading("portResult","جارٍ فحص المنافذ (قد يستغرق دقيقة)...");
  const d = await api("/api/ports?host="+encodeURIComponent(host));
  if(!d || !d.success){ setText("portResult", d?.message || "فشل"); return; }
  if(d.count === 0){
    setHTML("portResult", '<span class="badge">لا منافذ مفتوحة</span>'); return;
  }
  let html = '<span class="badge ok">'+d.count+' منفذ مفتوح</span><br>';
  d.open_ports.forEach(p => { html += '<span class="badge ok">'+p+'</span> '; });
  setHTML("portResult", html);
}
async function lookupIP(){
  const ip = document.getElementById("ipInput").value.trim();
  if(!ip){ alert("أدخل عنوان IP"); return; }
  setLoading("ipResult","جارٍ البحث...");
  const d = await api("/api/ip?ip="+encodeURIComponent(ip));
  if(!d){ setText("ipResult","فشل"); return; }
  let html = '<div class="list-item"><b>'+d.ip+'</b></div>';
  if(d.country) html += '<div class="list-item">🌍 '+d.country+' — '+(d.city||"")+'</div>';
  if(d.isp) html += '<div class="list-item">🏢 '+d.isp+'</div>';
  if(d.asn) html += '<div class="list-item">🔗 '+d.asn+'</div>';
  if(d.reverse_dns) html += '<div class="list-item">🔙 '+d.reverse_dns+'</div>';
  if(d.lat && d.lon) html += '<div class="list-item">📍 '+d.lat+', '+d.lon+'</div>';
  if(d.whois) html += '<details><summary class="list-item">📄 WHOIS</summary><pre style="font-size:11px;overflow:auto;max-height:200px">'+d.whois.substring(0,1500)+'</pre></details>';
  setHTML("ipResult", html);
}
async function loadHistory(){
  setLoading("historyResult");
  const d = await api("/api/history");
  if(!Array.isArray(d)){ setText("historyResult","لا يوجد سجل"); return; }
  if(d.length===0){ setHTML("historyResult",'<span class="badge">لا توجد عمليات</span>'); return; }
  let html = "";
  d.forEach(x=>{
    html += '<div class="list-item">🕐 '+x.time+' | '+x.type+' | '+x.result+'</div>';
  });
  setHTML("historyResult", html);
}
async function loadFiles(){
  setLoading("filesResult");
  const d = await api("/api/files");
  if(!Array.isArray(d)) return;
  if(d.length===0){ setHTML("filesResult",'<span class="badge">لا توجد ملفات</span>'); return; }
  let html = "";
  d.forEach(f=>{
    html += '<div class="list-item">📁 '+f.name+' ('+f.size+' بايت) '+
      '<button class="danger" style="padding:4px 10px;font-size:11px" onclick="deleteFile(\''+f.name+'\')">حذف</button></div>';
  });
  setHTML("filesResult", html);
}
async function uploadFile(){
  const input = document.getElementById("fileInput");
  if(!input.files.length){ alert("اختر ملفاً"); return; }
  const fd = new FormData();
  fd.append("file", input.files[0]);
  const d = await api("/api/files", {method:"POST", body:fd});
  if(d) alert(d.message || d.error || "");
  input.value = "";
  loadFiles();
}
async function deleteFile(name){
  if(!confirm("حذف "+name+"؟")) return;
  const d = await api("/api/files/"+encodeURIComponent(name), {method:"DELETE"});
  if(d) alert(d.message || d.error || "");
  loadFiles();
}
async function generateReport(){
  const d = await api("/api/report");
  if(d && d.success) alert("✅ تم إنشاء التقرير: "+d.path);
  else alert("❌ فشل");
}
async function loadDashboard(){
  const d = await api("/api/stats");
  if(!d) return;
  setText("statScans", d.scans ?? "—");
  setText("statIps", d.ips ?? "—");
  setText("statHydra", d.hydra ?? "—");
  setText("dashTime", "آخر تحديث: "+new Date().toLocaleTimeString("ar"));
}
setInterval(()=>{ if(document.getElementById("statScans")) loadDashboard(); }, 30000);
