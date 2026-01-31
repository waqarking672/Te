import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"   # 🔴 Sirf yahan token lagana hai
CHANNEL_USERNAME = "@e3hacker"  # 🔴 @ ke sath
API_URL = "https://arslan-apis.vercel.app/more/database?number="
# ============================================


async def is_user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined = await is_user_joined(update, context)

    if not joined:
        keyboard = [
            [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton("✅ Joined Channel", callback_data="check_join")]
        ]
        await update.message.reply_text(
            "🚫 *Access Denied*\n\n"
            "Bot use karne ke liye pehle channel join karo 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(
        "🇵🇰 *PAK SIM INFO*\n\n"
        "📱 Phone number bhejo (03XXXXXXXXX)",
        parse_mode="Markdown"
    )


async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    joined = await is_user_joined(update, context)

    if joined:
        await query.message.edit_text(
            "✅ *Channel Joined Successfully!*\n\n"
            "📱 Ab phone number bhejo",
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ Abhi channel join nahi kiya", show_alert=True)


async def sim_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()

    if not number.isdigit():
        await update.message.reply_text("❌ Sirf number likho (digits only)")
        return

    joined = await is_user_joined(update, context)
    if not joined:
        await start(update, context)
        return

    response = requests.get(API_URL + number)
    data = response.json()

    if not data.get("status"):
        await update.message.reply_text("❌ Koi data nahi mila")
        return

    # 🔒 Creator / Credit remove
    data.pop("creator", None)

    msg = "🇵🇰 *PAK SIM INFO*\n\n"
    for key, value in data.items():
        msg += f"🔹 *{key.capitalize()}*: `{value}`\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sim_info))
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, lambda u, c: None))
    app.add_handler(CommandHandler("check_join", check_join))

    app.run_polling()


if __name__ == "__main__":
    main()
