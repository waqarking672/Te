import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("7787473053:AAFCg166nfOqQY6dJUJfQ3ct5Rfc66dxkrI")  # Telegram Bot Token (ENV)
API_URL = "https://arslan-apis.vercel.app/ai/blackboxv4?q="
BOT_NAME = "🤖 Worm GPT"
# =========================================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{BOT_NAME}\n\n"
        "🧠 AI Powered Assistant\n\n"
        "بس کوئی بھی سوال لکھیں اور بھیج دیں ✨"
    )

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = requests.get(API_URL + user_text, timeout=60)
        data = response.json()

        # API response handling
        if data.get("status") is True:
            reply = data.get("result") or data.get("response") or "⚠️ No response"
        else:
            reply = data.get("err", "❌ Error from AI API")

    except Exception as e:
        reply = f"❌ Error: {str(e)}"

    await update.message.reply_text(reply)

# Main function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Worm GPT Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
