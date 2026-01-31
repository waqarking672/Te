from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"
CHANNEL_USERNAME = "@e3hacker"  # @ ke sath
# ==========================================

# ================ MOCK DATABASE =================
intelligenceDB = {
    '3336678955': [
        {'full_name': 'John Alexander', 'phone': '3336678955', 'cnic': '42101-1234567-8', 'address': 'Lahore, Pakistan'},
        {'full_name': 'John A. Smith', 'phone': '3336678955', 'cnic': '42101-9876543-2', 'address': 'Karachi, Pakistan'}
    ],
    '3494545456': [
        {'full_name': 'Ali Khan', 'phone': '3494545456', 'cnic': '42101-5566778-9', 'address': 'Lahore, Pakistan'}
    ],
    '923135645789': [
        {'full_name': 'Zara Ahmed', 'phone': '923135645789', 'cnic': '35202-9988776-1', 'address': 'Islamabad, Pakistan'}
    ]
}
# =================================================

# ========= Channel Join Check =========
async def is_user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        # Agar error aaye to assume joined (testing)
        return True

# ============= /start =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇵🇰 *PAK SIM INFO*\n\n"
        "📱 Please type a phone number (e.g. 3494545456 or 923135645789)",
        parse_mode="Markdown"
    )

# ============= SIM INFO =============
async def sim_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    
    if not number.isdigit():
        await update.message.reply_text("❌ Please enter digits only")
        return

    entries = intelligenceDB.get(number)
    if not entries:
        await update.message.reply_text("❌ No data found for this number")
        return
    
    msg = f"🇵🇰 *PAK SIM INFO* ({number})\n\n"
    for idx, data in enumerate(entries, 1):
        msg += f"🔹 Entry {idx}:\n"
        msg += f"   *Full Name*: `{data['full_name']}`\n"
        msg += f"   *Phone*: `{data['phone']}`\n"
        msg += f"   *CNIC*: `{data['cnic']}`\n"
        msg += f"   *Address*: `{data['address']}`\n\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

# ============= MAIN =============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sim_info))
    app.run_polling()

if __name__ == "__main__":
    main()
