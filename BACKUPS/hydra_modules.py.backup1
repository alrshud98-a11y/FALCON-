import shutil
import subprocess
import re

def discover_modules():
    path = shutil.which("hydra")
    if not path:
        return {
            "success": False,
            "message": "Hydra غير موجودة",
            "available": [],
            "unavailable": []
        }

    try:
        result = subprocess.run(
            [path, "-h"],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + "\n" + result.stderr

        supported = re.search(
            r"Supported services:\s*(.+)",
            output
        )
        missing = re.search(
            r"These services were not compiled in:\s*(.+)",
            output
        )

        if not supported:
            return {
                "success": False,
                "message": "تعذر استخراج قائمة الخدمات",
                "available": [],
                "unavailable": []
            }

        available = supported.group(1).split()
        unavailable = missing.group(1).split() if missing else []

        return {
            "success": True,
            "version": next(
                (x.strip() for x in output.splitlines()
                 if "Hydra v" in x),
                "غير معروف"
            ),
            "available": available,
            "unavailable": unavailable,
            "count": len(available)
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "available": [],
            "unavailable": []
        }


def module_info(name):
    data = discover_modules()

    if not data.get("success"):
        return data

    if name not in data["available"]:
        return {
            "success": False,
            "message": "هذه الوحدة ليست ضمن الخدمات المدعومة"
        }

    path = shutil.which("hydra")

    try:
        result = subprocess.run(
            [path, "-U", name],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = (result.stdout + "\n" + result.stderr).strip()

        return {
            "success": "Help for module" in output,
            "module": name,
            "details": output[:12000],
            "message": "تم جلب معلومات الوحدة من Hydra"
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
