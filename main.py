import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ===================== BOT CONFIG =====================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"          # 👈 YAHAN APNA BOT TOKEN PASTE KARO
CHANNEL_USERNAME = "@e3hacker"  # 👈 YAHAN APNA CHANNEL USERNAME
API_URL = "https://arslan-apis.vercel.app/more/database?number="
# =====================================================


async def user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_USERNAME,
            update.effective_user.id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await user_joined(update, context):
        await update.message.reply_text(
            f"❌ Bot use karne ke liye pehle channel join karein:\n\n"
            f"{CHANNEL_USERNAME}\n\n"
            f"Join karne ke baad /start likhein."
        )
        return

    await update.message.reply_text(
        "✅ Channel verified!\n\n"
        "📱 SIM information ke liye number bhejein:\n\n"
        "Examples:\n"
        "3491111111\n"
        "923491111111"
    )


async def fetch_sim_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await user_joined(update, context):
        await update.message.reply_text(
            f"❌ Pehle channel join karein:\n{CHANNEL_USERNAME}"
        )
        return

    number = update.message.text.strip()
    if not number.isdigit():
        await update.message.reply_text("⚠️ Sirf valid numbers bhejein.")
        return

    loading = await update.message.reply_text("⏳ Data fetch ho raha hai...")

    try:
        response = requests.get(API_URL + number, timeout=15)
        data = response.json()

        if not data:
            await loading.edit_text("❌ Koi data nahi mila.")
            return

        text = "📡 SIM INFORMATION\n\n"

        for key, value in data.items():
            # ❌ Creator aur credit waghera hide
            if key.lower() in ["creator", "credit", "owner", "source"]:
                continue

            # ❌ Agar value me bhi creator likha ho
            if isinstance(value, str) and "arslan-md" in value.lower():
                continue

            text += f"• {key} : {value}\n"

        # ✅ Footer (hamesha last me)
        text += (
            "\n━━━━━━━━━━━━━━\n"
            "Powered By E3 HACKER:\n"
            "https://whatsapp.com/channel/0029VajnN629RZAbp8aZAa1E"
        )

        await loading.edit_text(text)

    except:
        await loading.edit_text("⚠️ API error. Baad mein try karein.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_sim_info))

    print("🤖 Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
