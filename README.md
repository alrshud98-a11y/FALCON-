# 🦅 FALCON Security Framework

منصة أمن سيبراني شاملة تعمل على Termux (أندرويد) بواجهة ويب احترافية.

## ⚡ التثبيت السريع (لأي هاتف جديد)

افتح تطبيق Termux ونفذ الأوامر التالية بالترتيب:

```bash
# 1. تحديث الحزم وتثبيت المتطلبات
pkg update && pkg upgrade -y
pkg install git python -y

# 2. إنشاء مفتاح SSH (للاتصال الآمن بدون كلمة مرور)
ssh-keygen -t ed25519 -C "falcon@termux"
# (اضغط Enter في كل الأسئلة)

# 3. عرض المفتاح العام ونسخه
cat ~/.ssh/id_ed25519.pub
# (انسخ الناتج وأضفه في GitHub > Settings > SSH Keys)

# 4. تنزيل المشروع
git clone git@github.com:alrshud98-a11y/FALCON-.git

# 5. الدخول إلى المجلد وتثبيت المكتبات
cd FALCON-
pip install flask

# 6. تشغيل الأداة
python app.py
