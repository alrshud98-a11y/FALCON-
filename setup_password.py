import getpass, sys
import auth
if auth.is_configured():
    print("⚠️  كلمة المرور موجودة")
    if input("تغييرها؟ (y/N): ").strip().lower() != "y":
        sys.exit(0)
while True:
    pwd = getpass.getpass("كلمة المرور (6+ أحرف): ")
    if len(pwd) < 6:
        print("❌ قصيرة"); continue
    if pwd != getpass.getpass("أعد الإدخال: "):
        print("❌ غير متطابقتين"); continue
    ok, msg = auth.setup_password(pwd)
    print(("✅ " if ok else "❌ ") + msg)
    sys.exit(0 if ok else 1)
