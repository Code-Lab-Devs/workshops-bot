import os
import json

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from fastapi import FastAPI, Request
import asyncio
import aiohttp

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
TOKEN = os.getenv("BOT_TOKEN")
def get_title(url) -> str :
    import requests
    from bs4 import BeautifulSoup
    
    response = requests.get(url, stream=True)

    content_type = response.headers.get("Content-Type", "").lower()

    if "text/html" in content_type:


        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        print("TITLE:", soup.title.string)
        return soup.title.string
    else:
        print("TITLE: No title found")
        return ""

    response.close()
bot = Bot(token=TOKEN)
dp = Dispatcher()

last_ping = datetime.now()

import re

def format_text(text: str) -> str:
    lines = text.split("\n")
    result = []

    for line in lines:
        line = line.strip()

        if not line:
            result.append("")
            continue

        # 🔹 عناوين رئيسية (تنتهي بـ :)
        if line.endswith(":"):
            result.append(f"\n<b>📌 {line[:-1]}</b>")
            continue

        # 🔹 عناوين مرقمة (1. 2. 3.)
        if re.match(r"^\d+\.\s+[A-Za-z\u0600-\u06FF]", line):
            result.append(f"\n<b>🔹 {line}</b>")
            continue

        # 🔹 نقاط
        if line.startswith("•"):
            result.append(f"• {line[1:].strip()}")
            continue

        # 🔹 روابط
        if line.startswith("http"):
            result.append(f"🔗 <a href='{line}'>{line}</a>")
            continue

        # 🔹 نص عادي
        result.append(f"{line}")

    return "\n".join(result)
async def keep_alive():

    global last_ping

    while True:

        try:

            now = datetime.now()

            if now >= last_ping + timedelta(minutes=10):

                async with aiohttp.ClientSession() as session:

                    async with session.get(
                        "https://workshops-bot.onrender.com/"
                    ) as response:

                        print(
                            "SELF PING:",
                            response.status
                        )

                last_ping = now

        except Exception as e:

            print("PING ERROR:", e)

        await asyncio.sleep(30)
        
@asynccontextmanager
async def lifespan(app: FastAPI):

    asyncio.create_task(
        keep_alive()
    )

    print("KEEP ALIVE STARTED")

    yield


app = FastAPI(lifespan=lifespan)


# =========================
# تحميل الورش
# =========================
def load_workshops():
    try:
        with open("workshops.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("JSON ERROR:", e)
        return []


workshops = load_workshops()


# =========================
# /start
# =========================
@dp.message(lambda message: message.text == "/start")
async def start(message: types.Message):
    keyboard_list = []

    for i in range(0, len(workshops), 2):
        row = [KeyboardButton(text=workshops[i]["title"])]

        if i + 1 < len(workshops):
            row.append(KeyboardButton(text=workshops[i + 1]["title"]))

        keyboard_list.append(row)
    keyboard = ReplyKeyboardMarkup(
    keyboard=keyboard_list,
    resize_keyboard=True
)

    await message.answer(
        "📚 أرشيف ورش النادي البرمجي\nاختر ورشة:",
        reply_markup=keyboard
    )


# =========================
# اختيار ورشة + قائمة المحتوى
# =========================
@dp.message()
async def handle_workshop(message: types.Message):

    text = message.text

    # الرجوع للبداية
    if text == "🔙 رجوع":
        await start(message)
        return

    # اختيار ورشة
    w = next((x for x in workshops if x["title"] == text), None)

    if w:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 الملخص"), KeyboardButton(text="📁 الملفات")],
                [KeyboardButton(text="🎥 المصادر"), KeyboardButton(text="🚀 الخطوات التالية")],
                [KeyboardButton(text="🔙 رجوع")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            f"⚙️ {w['title']}\n {w['description']}\n اختر:",
            reply_markup=keyboard
        )

        # نحفظ الورشة الحالية داخل المستخدم (حل بسيط)
        message.bot.current_workshop = w
        return

    # جلب الورشة الحالية
    w = getattr(message.bot, "current_workshop", None)

    if not w:
        return

    # =========================
    # الملخص
    # =========================
    if text == "📝 الملخص":
        await message.answer(w.get("summary", "لا يوجد ملخص"))

    # =========================
    # الملفات
    # =========================
    elif text == "📁 الملفات":
        files = w.get("files", [])
        if files:
            for f in files:
                await message.answer_document(f)
        else:
            await message.answer("لا توجد ملفات")

    # =========================
    # المصادر
    # =========================
    elif text == "🎥 المصادر":
        resources = w.get("resources", [])
        if resources:
            for i in range(len(resources)):
                await message.answer(f"\n {get_title(resources[i])} \n".join([resources[i]]))
        else:
            await message.answer("لا توجد مصادر")

    # =========================
    # الخطوات
    # =========================
    elif text == "🚀 الخطوات التالية":
        steps = w.get("next_steps", [])
        if steps:
            await message.answer("\n".join(steps))
        else:
            await message.answer("لا توجد خطوات")
# =========================
# webhook
# =========================
@app.post("/webhook")
async def webhook(request: Request):

    try:
        update = await request.json()
        await dp.feed_raw_update(bot, update)

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return {"ok": True}


# =========================
# channel file logger
# =========================
@dp.channel_post()
async def handle_channel_files(message: types.Message):

    try:

        if message.document:

            print("================================")
            print("FILE NAME:", message.document.file_name)
            print("FILE ID:", message.document.file_id)
            print("================================")

    except Exception as e:
        print("CHANNEL ERROR:", e)


# =========================
# health check
# =========================
@app.get("/")
def home():
    return {"status": "bot running"}