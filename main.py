import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG (ONLY ONE PLACE) =================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"
CHANNEL_USERNAME = "@e3hacker"
API_URL = "https://arslan-apis.vercel.app/more/database?number="
# ===========================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; Mobile)",
    "Accept": "application/json"
}


def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")]
    ])


async def is_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            update.effective_user.id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update, context):
        await update.message.reply_text(
            "⚠️ Bot use karne ke liye pehle channel join karein",
            reply_markup=join_keyboard()
        )
        return

    await update.message.reply_text(
        "📱 SIM Database Bot\n\n"
        "📌 Number send karein (without +92)\n\n"
        "Example: 3482265786"
    )


async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update, context):
        await update.message.reply_text(
            "❌ Pehle channel join karein",
            reply_markup=join_keyboard()
        )
        return

    number = update.message.text.strip()

    if not number.isdigit():
        await update.message.reply_text("❌ Sirf number send karein")
        return

    try:
        url = API_URL + number
        res = requests.get(url, headers=HEADERS, timeout=20)

        if res.status_code != 200:
            await update.message.reply_text("❌ API block ho rahi hai")
            return

        data = res.json()

        # 🔥 REAL SAFE PARSING
        info = {}

        if isinstance(data, dict):
            if "result" in data:
                info = data["result"]
            elif "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                info = data["data"][0]
            else:
                info = data

        name = info.get("name") or "Not Found"
        cnic = info.get("cnic") or "Not Found"
        address = info.get("address") or "Not Found"

        if name == "Not Found" and cnic == "Not Found":
            await update.message.reply_text("❌ Is number ka data available nahi")
            return

        msg = (
            "📊 SIM Information\n\n"
            f"📞 Number: {number}\n"
            f"👤 Name: {name}\n"
            f"🆔 CNIC: {cnic}\n"
            f"🏠 Address: {address}"
        )

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text("❌ API se data nahi aa raha")


def main():
    if not BOT_TOKEN or "PASTE_" in BOT_TOKEN:
        raise ValueError("BOT TOKEN set nahi kiya")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("🤖 Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
