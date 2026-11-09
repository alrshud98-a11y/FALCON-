#!/data/data/com.termux/files/usr/bin/bash
echo "🔄 جاري تثبيت FALCON (الأسطورة معتصم)..."
pkg update -y && pkg upgrade -y
pkg install python git nmap curl -y
pip install flask requests
termux-setup-storage
mkdir -p ~/FALCON/logs
echo "✅ تم التثبيت! شغّل: cd ~/FALCON && python app.py"
