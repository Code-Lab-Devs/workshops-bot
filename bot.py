import os
import json

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from fastapi import FastAPI, Request
import asyncio
import aiohttp

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
TOKEN = os.getenv("BOT_TOKEN")

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

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=w["title"])]
            for w in workshops
        ],
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
            f"⚙️ {w['title']}\nاختر:",
            reply_markup=keyboard
        )
        return

    # جلب الورشة الحالية
    wid = next((x["id"] for x in workshops if x["title"] in message.text), None)
    w = next((x for x in workshops if x["id"] == wid), None)

    if not w:
        return

    # الملخص
    if text == "📝 الملخص":
        await message.answer(w.get("summary", "لا يوجد ملخص"))

    # الملفات
    elif text == "📁 الملفات":
        files = w.get("files", [])
        if files:
            for f in files:
                await message.answer_document(f)
        else:
            await message.answer("لا توجد ملفات")

    # المصادر
    elif text == "🎥 المصادر":
        resources = w.get("resources", [])
        if resources:
            await message.answer("\n".join(resources))
        else:
            await message.answer("لا توجد مصادر")

    # الخطوات
    elif text == "🚀 الخطوات التالية":
        steps = w.get("next_steps", [])
        if steps:
            await message.answer("\n".join(steps))
        else:
            await message.answer("لا توجد خطوات")
            # await callback.message.edit_text(
            #     f"⚙️ {w['title']}\n\n{w.get('description', '')}",
            #     reply_markup=keyboard
            # )

    # except Exception as e:
    #     print("CALLBACK ERROR:", e)


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