import json
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# 🔐 Token va Admin ID
API_TOKEN = '7876159184:AAG52HCggAT0P77eSKN6B-28UQhFNsxcVjU'
ADMIN_ID = 5160827060

# 📢 Obuna kerak bo‘lgan kanallar
REQUIRED_CHANNELS = ['@xjxjcjcjzkzic', '@ggivxjdijdd', '@ddkgxtycfhvhgc']

# 🔧 Logging
logging.basicConfig(level=logging.INFO)

# 🧠 Bot yaratish
application = Application.builder().token(API_TOKEN).build()

# ✅ Obuna tekshirish
async def get_unsubscribed_channels(user_id):
    unsubscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await application.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "creator", "administrator"]:
                unsubscribed.append(channel)
        except:
            unsubscribed.append(channel)
    return unsubscribed

# 🚀 /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    unsubscribed = await get_unsubscribed_channels(user_id)

    # Foydalanuvchini ro'yxatga olish
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = []

    if user_id not in users:
        users.append(user_id)
        with open("users.json", "w") as f:
            json.dump(users, f)

    if unsubscribed:
        buttons = [[InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{ch[1:]}")] for ch in unsubscribed]
        buttons.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs")])
        await update.message.reply_text("👋 Salom! Iltimos, quyidagi kanallarga obuna bo‘ling:",
                                        reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text("✅ Barcha kanallarga obuna bo‘lgansiz! Endi kino kodini yuboring.")

# ✅ Tekshirish tugmasi
async def check_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    unsubscribed = await get_unsubscribed_channels(user_id)

    if unsubscribed:
        buttons = [[InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{ch[1:]}")] for ch in unsubscribed]
        buttons.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs")])
        await query.edit_message_text("❗️ Hali ham quyidagi kanallarga obuna emassiz:", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.edit_message_text("✅ Obuna tasdiqlandi! Endi kino kodini yuboring.")

# 🎮 Admin fayl yuboradi va saqlaydi
async def save_film(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Siz admin emassiz.")
        return

    if update.message.caption:
        text = update.message.caption
        if "Kod:" in text:
            code = text.split("Kod:")[1].strip()
        else:
            await update.message.reply_text("❗ Caption ichida 'Kod: 123' yozilishi kerak.")
            return
    else:
        await update.message.reply_text("❗ Caption yozilmagan.")
        return

    if update.message.video:
        file_id = update.message.video.file_id
        file_type = "video"
    elif update.message.document and update.message.document.mime_type.startswith("video"):
        file_id = update.message.document.file_id
        file_type = "document"
    else:
        await update.message.reply_text("❗ Faqat video yoki video-fayl yuboring.")
        return

    try:
        with open("films.json", "r") as f:
            films = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        films = {}

    films[code] = {"file_id": file_id, "type": file_type}

    with open("films.json", "w") as f:
        json.dump(films, f, indent=4)

    await update.message.reply_text(f"✅ Kino saqlandi!\n🎮 Kod: {code}")

# 🎮 Kod orqali foydalanuvchiga kino yuborish
async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    unsubscribed = await get_unsubscribed_channels(user_id)
    if unsubscribed:
        await update.message.reply_text("❗️ Avval barcha kanallarga obuna bo‘ling.")
        return

    code = update.message.text.strip()
    try:
        with open("films.json", "r") as f:
            films = json.load(f)
    except:
        films = {}

    film = films.get(code)
    if not film:
        await update.message.reply_text("🚫 Kod bo‘yicha kino topilmadi.")
        return

    if film["type"] == "video":
        await update.message.reply_video(video=film["file_id"])
    else:
        await update.message.reply_document(document=film["file_id"])

# 🛠 Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Siz admin emassiz.")
        return

    try:
        with open("films.json", "r") as f:
            films = json.load(f)
    except:
        films = {}

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = []

    total_films = len(films)
    total_users = len(users)

    await update.message.reply_text(
        f"🔧 Admin panel:\n"
        f"🎬 Jami kinolar: {total_films}\n"
        f"👥 Foydalanuvchilar: {total_users}"
    )

async def delete_film(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    args = context.args
    if not args:
        await update.message.reply_text("❗ Iltimos, kodni yozing. Masalan: /delete 123")
        return

    code = args[0]
    try:
        with open("films.json", "r") as f:
            films = json.load(f)
    except:
        films = {}

    if code in films:
        del films[code]
        with open("films.json", "w") as f:
            json.dump(films, f, indent=4)
        await update.message.reply_text(f"🗑 Kino o‘chirildi! Kod: {code}")
    else:
        await update.message.reply_text("🚫 Bunday kod topilmadi.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    text = update.message.text.split(" ", 1)
    if len(text) < 2:
        await update.message.reply_text("❗ Foydalanuvchilarga yuboriladigan xabarni yozing. Masalan:\n/broadcast Salom hammaga!")
        return

    message = text[1]

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = []

    count = 0
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            count += 1
        except:
            continue

    await update.message.reply_text(f"📤 {count} ta foydalanuvchiga yuborildi.")


# 🔌 Handlerlar
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(check_subs, pattern="check_subs"))
application.add_handler(CommandHandler("admin", admin_panel))
application.add_handler(CommandHandler("delete", delete_film))
application.add_handler(CommandHandler("broadcast", broadcast))
application.add_handler(MessageHandler((filters.VIDEO | filters.Document.VIDEO) & filters.Caption(), save_film))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code))

# ▶️ Botni ishga tushurish
if __name__ == '__main__':
    if not os.path.exists("films.json"):
        with open("films.json", "w") as f:
            f.write("{}")
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            f.write("[]")
    application.run_polling()
