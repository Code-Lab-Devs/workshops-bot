import os
import json
from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI()

# تحميل الورش
def load_workshops():
    with open("workshops.json", "r", encoding="utf-8") as f:
        return json.load(f)

workshops = load_workshops()


# /start
@dp.message()
async def start(message: types.Message):
    if message.text == "/start":
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=w["title"], callback_data=f"w_{w['id']}")]
                for w in workshops
            ]
        )

        await message.answer("📚 أرشيف ورش النادي البرمجي\nاختر ورشة:", reply_markup=keyboard)


# اختيار ورشة
@dp.callback_query()
async def workshop_handler(callback: types.CallbackQuery):
    data = callback.data

    if data.startswith("w_"):
        wid = int(data.split("_")[1])
        w = next((x for x in workshops if x["id"] == wid), None)

        if not w:
            await callback.message.answer("الورشة غير موجودة")
            return

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="📝 الملخص", callback_data=f"sum_{wid}")],
                [types.InlineKeyboardButton(text="📄 السلايدات", callback_data=f"slides_{wid}")],
                [types.InlineKeyboardButton(text="📁 الملفات", callback_data=f"files_{wid}")],
            ]
        )

        await callback.message.answer(
            f"⚙️ {w['title']}\n\n{w['description']}",
            reply_markup=keyboard
        )

    elif data.startswith("sum_"):
        wid = int(data.split("_")[1])
        w = next(x for x in workshops if x["id"] == wid)
        await callback.message.answer(w["summary"])

    elif data.startswith("slides_"):
        wid = int(data.split("_")[1])
        w = next(x for x in workshops if x["id"] == wid)

        if w["slides_file_id"]:
            await callback.message.answer_document(w["slides_file_id"])
        else:
            await callback.message.answer("لا يوجد سلايدات")

    elif data.startswith("files_"):
        wid = int(data.split("_")[1])
        w = next(x for x in workshops if x["id"] == wid)

        if w["files"]:
            for f in w["files"]:
                await callback.message.answer_document(f)
        else:
            await callback.message.answer("لا توجد ملفات")


# Webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    await dp.feed_raw_update(bot, update)
    return {"ok": True}


# تشغيل محلي (اختياري)
@app.get("/")
def home():
    return {"status": "bot running"}