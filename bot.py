import os
import json

from aiogram import Bot, Dispatcher, types
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

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=w["title"], callback_data=f"w_{w['id']}")]
            for w in workshops
        ]
    )

    await message.answer(
        "📚 أرشيف ورش النادي البرمجي\nاختر ورشة:",
        reply_markup=keyboard
    )


# =========================
# callback handler
# =========================
@dp.callback_query()
async def workshop_handler(callback: types.CallbackQuery):

    try:

        try:
            await callback.answer()
        except TelegramBadRequest:
            pass

        data = callback.data

        # عرض الورشة
        if data.startswith("w_"):

            wid = int(data.split("_")[1])

            w = next(
                (x for x in workshops if x["id"] == wid),
                None
            )

            if not w:
                await callback.message.answer("الورشة غير موجودة")
                return

            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="📝 الملخص",
                        callback_data=f"sum_{wid}"
                    )],
                    [types.InlineKeyboardButton(
                        text="📁 الملفات",
                        callback_data=f"files_{wid}"
                    )],
                    [types.InlineKeyboardButton(
                        text="🎥 المصادر",
                        callback_data=f"res_{wid}"
                    )],
                    [types.InlineKeyboardButton(
                        text="🚀 الخطوات التالية",
                        callback_data=f"steps_{wid}"
                    )],
                    [types.InlineKeyboardButton(
                        text="🔙 رجوع",
                        callback_data="home"
                    )]
                ]
            )

            await callback.message.edit_text(
                f"⚙️ {w['title']}\n\n{w.get('description', '')}",
                reply_markup=keyboard
            )

        # الملخص
        elif data.startswith("sum_"):

            wid = int(data.split("_")[1])

            w = next(
                (x for x in workshops if x["id"] == wid),
                None
            )

            if not w:
                return

            await callback.message.answer(
                w.get("summary", "لا يوجد ملخص")
            )

        # الملفات
        elif data.startswith("files_"):

            wid = int(data.split("_")[1])

            w = next(
                (x for x in workshops if x["id"] == wid),
                None
            )

            if not w:
                return

            files = w.get("files", [])

            if files:
                for file_id in files:
                    try:
                        await callback.message.answer_document(file_id)
                    except Exception as e:
                        print("FILE SEND ERROR:", e)
            else:
                await callback.message.answer("لا توجد ملفات")

        # المصادر
        elif data.startswith("res_"):

            wid = int(data.split("_")[1])

            w = next(
                (x for x in workshops if x["id"] == wid),
                None
            )

            if not w:
                return

            resources = w.get("resources", [])

            if resources:
                await callback.message.answer(
                    "\n".join(resources)
                )
            else:
                await callback.message.answer("لا توجد مصادر")

        # الخطوات التالية
        elif data.startswith("steps_"):

            wid = int(data.split("_")[1])

            w = next(
                (x for x in workshops if x["id"] == wid),
                None
            )

            if not w:
                return

            steps = w.get("next_steps", [])

            if steps:
                await callback.message.answer(
                    "\n".join(steps)
                )
            else:
                await callback.message.answer("لا توجد خطوات")

        # رجوع
        elif data == "home":

            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text=w["title"],
                        callback_data=f"w_{w['id']}"
                    )]
                    for w in workshops
                ]
            )

            await callback.message.edit_text(
                "📚 أرشيف ورش النادي البرمجي\nاختر ورشة:",
                reply_markup=keyboard
            )

    except Exception as e:
        print("CALLBACK ERROR:", e)


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