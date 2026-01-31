import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A")  # 🔒 Token only here
API_URL = "https://arslan-apis.vercel.app/more/database?number="
CHANNEL_USERNAME = "@e3hacker"  # without https://t.me/
# =========================================


# 🔹 Check channel join
async def is_user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# 🔹 Force Join Message
async def force_join(update: Update):
    keyboard = [
        [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("✅ Joined", callback_data="joined")]
    ]
    return InlineKeyboardMarkup(keyboard)


# 🔹 Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined = await is_user_joined(update, context)

    if not joined:
        await update.message.reply_text(
            "⚠️ Bot use karne ke liye channel join karna zaroori hai",
            reply_markup=await force_join(update)
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
    joined = await is_user_joined(update, context)

    if not joined:
        await update.message.reply_text(
            "❌ Pehle channel join karein",
            reply_markup=await force_join(update)
        )
        return

    number = update.message.text.strip()

    if not number.isdigit():
        await update.message.reply_text("❌ Sirf number send karein")
        return

    try:
        response = requests.get(API_URL + number, timeout=15)
        data = response.json()

        # 🔹 Clean & format data
        name = data.get("name", "Not Found")
        cnic = data.get("cnic", "Not Found")
        address = data.get("address", "Not Found")

        result = (
            f"📊 *SIM Information*\n\n"
            f"📞 *Number:* {number}\n"
            f"👤 *Name:* {name}\n"
            f"🆔 *CNIC:* {cnic}\n"
            f"🏠 *Address:* {address}"
        )

        await update.message.reply_text(result, parse_mode="Markdown")

    except:
        await update.message.reply_text("❌ Data fetch nahi ho saka")


# 🔹 Main
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("🤖 Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
