import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== ONLY CHANGE HERE ==================
BOT_TOKEN = "7787473053:AAFCg166nfOqQY6dJUJfQ3ct5Rfc66dxkrI"
# =====================================================

API_URL = "https://arslan-apis.vercel.app/ai/blackboxv4?q="
BOT_NAME = "🤖 Worm GPT"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{BOT_NAME}\n\n"
        "🧠 AI Chat Bot Ready\n"
        "✍️ Kuch bhi likho, main jawab doon ga"
    )

# Handle messages
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        res = requests.get(API_URL + user_text, timeout=60)
        data = res.json()

        if data.get("status") is True:
            reply = data.get("result") or data.get("response") or "No response"
        else:
            reply = data.get("err", "API error")

    except Exception as e:
        reply = f"Error: {e}"

    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🤖 Worm GPT Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
