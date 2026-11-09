import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".txt", ".log", ".json", ".csv", ".md"}

def list_files():
    result = []
    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(path):
            result.append({
                "name": name,
                "size": os.path.getsize(path)
            })
    return result

def upload_file(file):
    if not file or not file.filename:
        return {"error": "لم يتم اختيار ملف"}, 400

    name = secure_filename(file.filename)
    ext = os.path.splitext(name)[1].lower()

    if not name or ext not in ALLOWED_EXTENSIONS:
        return {"error": "نوع الملف غير مسموح"}, 400

    path = os.path.join(UPLOAD_DIR, name)

    if os.path.exists(path):
        return {"error": "الملف موجود مسبقاً"}, 409

    file.save(path)
    return {"message": "تم رفع الملف بنجاح"}, 200

def delete_file(name):
    name = secure_filename(name)
    path = os.path.join(UPLOAD_DIR, name)

    if not name or not os.path.isfile(path):
        return {"error": "الملف غير موجود"}, 404

    os.remove(path)
    return {"message": "تم حذف الملف"}, 200
