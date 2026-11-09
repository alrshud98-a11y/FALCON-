#!/data/data/com.termux/files/usr/bin/bash
cd ~/FALCON

echo "🔄 جاري إيقاف أي نسخ قديمة..."
pkill -f "python app.py" 2>/dev/null
pkill -f "cloudflared" 2>/dev/null
sleep 1

echo "🚀 جاري تشغيل سيرفر FALCON..."
python app.py > logs/server.log 2>&1 &
sleep 3

echo "🌐 جاري تشغيل Cloudflare Tunnel..."
cloudflared tunnel --url http://127.0.0.1:5000 > logs/cloudflare.log 2>&1 &

echo "⏳ في انتظار الرابط العام..."
for i in {1..20}; do
    URL=$(grep -o 'https://[a-zA-Z0-9.-]*trycloudflare.com' logs/cloudflare.log | head -1)
    if [ -n "$URL" ]; then
        echo ""
        echo "✅ تم التشغيل بنجاح!"
        echo "🔗 الرابط العام: $URL"
        echo "🏠 الرابط المحلي: http://127.0.0.1:5000"
        echo ""
        echo "📋 لمشاهدة سجل السيرفر: tail -f logs/server.log"
        echo "🛑 لإيقاف كل شيء: pkill -f 'python app.py' && pkill -f 'cloudflared'"
        exit 0
    fi
    sleep 2
done

echo "⚠️ لم يتم العثور على الرابط. تحقق من: cat logs/cloudflare.log"
