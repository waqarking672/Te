import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ===================== BOT CONFIG =====================
# Yahan sirf ek jagah token aur channel username paste karo
BOT_TOKEN = "8486268251:AAGWgp2Vz_cOg2hIl7W2Fe-gFHMas5_zEo8"          # <-- Yahan apna bot token paste karo
CHANNEL_USERNAME = "@e3hacker"  # <-- Yahan apna channel username paste karo
API_URL = "https://arslan-apis.vercel.app/more/database?number="
# =======================================================

async def user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await user_joined(update, context):
        await update.message.reply_text(
            f"❌ Pehle channel join karein:\n{CHANNEL_USERNAME}\n\n"
            f"Join karne ke baad /start likhein."
        )
        return

    await update.message.reply_text(
        "✅ Channel verified!\n\n"
        "📱 SIM info ke liye number bhejein:\n"
        "Examples:\n"
        "3491111111\n"
        "923491111111"
    )

async def fetch_sim_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await user_joined(update, context):
        await update.message.reply_text(f"❌ Pehle channel join karein: {CHANNEL_USERNAME}")
        return

    number = update.message.text.strip()
    if not number.isdigit():
        await update.message.reply_text("⚠️ Sirf valid numbers bhejein.")
        return

    msg = await update.message.reply_text("⏳ Data fetch ho raha hai...")

    try:
        r = requests.get(API_URL + number, timeout=15)
        data = r.json()

        if not data or data.get("status") is False:
            await msg.edit_text("❌ Koi data nahi mila.")
            return

        result = "📡 **SIM INFORMATION**\n\n"
        for key, value in data.items():
            if key.lower() in ["credit", "owner", "source"]:
                continue
            result += f"• {key.capitalize()} : {value}\n"

        await msg.edit_text(result)

    except Exception as e:
        await msg.edit_text("⚠️ API error. Baad mein try karein.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_sim_info))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
