import json
import os

FILE = "workshops.json"

def load():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_workshop():
    data = load()

    new = {
        "id": len(data) + 1,
        "title": input("Title: "),
        "description": input("Description: "),
        "summary": input("Summary: "),
        "files": [],
        "resources": [],
        "next_steps": []
    }

    # =========================
    # ملفات
    # =========================
    print("\n📁 أدخل الملفات (Enter فارغ للإيقاف):")
    while True:
        f = input("File ID: ").strip()
        if not f:
            break
        new["files"].append(f)

    # =========================
    # مصادر يوتيوب
    # =========================
    print("\n🎥 أدخل روابط يوتيوب (Enter فارغ للإيقاف):")
    while True:
        r = input("YouTube link: ").strip()
        if not r:
            break
        new["resources"].append(r)

    # =========================
    # الخطوات القادمة
    # =========================
    print("\n🚀 أدخل الخطوات القادمة (Enter فارغ للإيقاف):")
    while True:
        s = input("Step: ").strip()
        if not s:
            break
        new["next_steps"].append(s)

    # حفظ
    data.append(new)
    save(data)

    print("✅ Workshop added successfully!")

add_workshop()