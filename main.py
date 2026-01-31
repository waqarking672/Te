import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ============ BOT CONFIG (ONLY ONE PLACE) ============
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"
CHANNEL_USERNAME = "@e3hacker"
API_URL = "https://arslan-apis.vercel.app/more/database?number="
# ====================================================


# 🔹 Force Join Keyboard
def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("✅ Joined", callback_data="joined")]
    ])


# 🔹 Check Join
async def is_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            update.effective_user.id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# 🔹 Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update, context):
        await update.message.reply_text(
            "⚠️ Bot use karne ke liye pehle channel join karein",
            reply_markup=join_keyboard()
        )
        return

    await update.message.reply_text(
        "📱 *SIM Database Bot*\n\n"
        "📌 Number send karein (without +92)\n\n"
        "Example:\n3482265786",
        parse_mode="Markdown"
    )


# 🔹 Handle Number
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
        res = requests.get(API_URL + number, timeout=10)
        data = res.json()

        # Clean output (NO CREDIT)
        name = data.get("name", "Not Found")
        cnic = data.get("cnic", "Not Found")
        address = data.get("address", "Not Found")

        msg = (
            f"📊 *SIM Information*\n\n"
            f"📞 *Number:* {number}\n"
            f"👤 *Name:* {name}\n"
            f"🆔 *CNIC:* {cnic}\n"
            f"🏠 *Address:* {address}"
        )

        await update.message.reply_text(msg, parse_mode="Markdown")

    except:
        await update.message.reply_text("❌ Data fetch failed")


# 🔹 Main
def main():
    if not BOT_TOKEN or "PASTE_" in BOT_TOKEN:
        raise ValueError("❌ BOT TOKEN set nahi kiya")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("🤖 Bot Running Successfully...")
    app.run_polling()


if __name__ == "__main__":
    main()
