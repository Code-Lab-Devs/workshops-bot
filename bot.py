import os
import json
from aiogram import Bot, Dispatcher, types
from fastapi import FastAPI, Request

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()


# =========================
# تحميل الورش
# =========================
def load_workshops():
    with open("workshops.json", "r", encoding="utf-8") as f:
        return json.load(f)

workshops = load_workshops()


# =========================
# /start
# =========================
@dp.message(lambda message: message.text == "/start")
async def start(message: types.Message):

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=w["title"], callback_data=f"w_{w['id']}")]
        for w in workshops
    ])

    await message.answer(
        "📚 أرشيف ورش النادي البرمجي\nاختر ورشة:",
        reply_markup=keyboard
    )


# =========================
# callback handler
# =========================
@dp.callback_query()
async def workshop_handler(callback: types.CallbackQuery):

    await callback.answer()
    data = callback.data

    # عرض الورشة
    if data.startswith("w_"):
        wid = int(data.split("_")[1])
        w = next((x for x in workshops if x["id"] == wid), None)

        if not w:
            await callback.message.answer("الورشة غير موجودة")
            return

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📝 الملخص", callback_data=f"sum_{wid}")],
            [types.InlineKeyboardButton(text="📁 الملفات", callback_data=f"files_{wid}")],
            [types.InlineKeyboardButton(text="🎥 المصادر", callback_data=f"res_{wid}")],
            [types.InlineKeyboardButton(text="🚀 الخطوات", callback_data=f"steps_{wid}")],
            [types.InlineKeyboardButton(text="🔙 رجوع", callback_data="home")]
        ])

        await callback.message.edit_text(
            f"⚙️ {w['title']}\n\n{w.get('description','')}",
            reply_markup=keyboard
        )

    # ملخص
    elif data.startswith("sum_"):
        wid = int(data.split("_")[1])
        w = next(x for x in workshops if x["id"] == wid)
        await callback.message.answer(w.get("summary", "لا يوجد ملخص"))

    # ملفات (تشمل السلايدات)
    elif data.startswith("files_"):
        wid = int(data.split("_")[1])
        w = next(x for x in workshops if x["id"] == wid)

        files = w.get("files", [])

        if files:
            for f in files:
                await callback.message.answer_document(f)
        else:
            await callback.message.answer("لا توجد ملفات")

    # مصادر يوتيوب
    elif data.startswith("res_"):
        wid = int(data.split("_")[1])
        w = next(x for x in workshops if x["id"] == wid)

        resources = w.get("resources", [])

        if resources:
            await callback.message.answer("\n".join(resources))
        else:
            await callback.message.answer("لا توجد مصادر")

    # خطوات بعد الورشة
    elif data.startswith("steps_"):
        wid = int(data.split("_")[1])
        w = next(x for x in workshops if x["id"] == wid)

        steps = w.get("next_steps", [])

        if steps:
            await callback.message.answer("\n".join(steps))
        else:
            await callback.message.answer("لا توجد خطوات")

    # رجوع
    elif data == "home":
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=w["title"], callback_data=f"w_{w['id']}")]
            for w in workshops
        ])

        await callback.message.edit_text(
            "📚 أرشيف ورش النادي البرمجي\nاختر ورشة:",
            reply_markup=keyboard
        )


# =========================
# webhook
# =========================
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    await dp.feed_raw_update(bot, update)
    return {"ok": True}


# =========================
# channel file logger
# =========================
@dp.channel_post()
async def handle_channel_files(message: types.Message):

    if message.document:
        print("NEW FILE_ID:", message.document.file_id)


# =========================
# health check
# =========================
@app.get("/")
def home():
    return {"status": "bot running"}