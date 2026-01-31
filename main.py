from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"   # 🔴 Sirf yahan token lagana
CHANNEL_USERNAME = "@e3hacker"  # 🔴 @ ke sath
# ============================================

# ================= MOCK DATABASE =================
intelligenceDB = {
    '3336678955': [
        {'full_name': 'John Alexander', 'phone': '3336678955', 'cnic': '42101-1234567-8', 'address': 'Lahore, Pakistan'},
        {'full_name': 'John A. Smith', 'phone': '3336678955', 'cnic': '42101-9876543-2', 'address': 'Karachi, Pakistan'}
    ],
    '3105551234': [
        {'full_name': 'Sarah Johnson', 'phone': '3105551234', 'cnic': '35202-4567890-1', 'address': 'Islamabad, Pakistan'}
    ],
    '4155557890': [
        {'full_name': 'Michael Williams', 'phone': '4155557890', 'cnic': '37303-5678901-2', 'address': 'Faisalabad, Pakistan'},
        {'full_name': 'Mike Williams', 'phone': '4155557890', 'cnic': '37303-8765432-1', 'address': 'Rawalpindi, Pakistan'}
    ],
    '923001234567': [
        {'full_name': 'Test User', 'phone': '923001234567', 'cnic': '42101-1122334-5', 'address': 'Karachi, Pakistan'}
    ],
    '3494545456': [
        {'full_name': 'Ali Khan', 'phone': '3494545456', 'cnic': '42101-5566778-9', 'address': 'Lahore, Pakistan'}
    ],
    '923135645789': [
        {'full_name': 'Zara Ahmed', 'phone': '923135645789', 'cnic': '35202-9988776-1', 'address': 'Islamabad, Pakistan'}
    ]
}
# =================================================

async def is_user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    joined = await is_user_joined(update, context)
    if not joined:
        await update.message.reply_text(f"🚫 Bot use karne ke liye pehle {CHANNEL_USERNAME} join karo.")
        return
    await update.message.reply_text("🇵🇰 *PAK SIM INFO*\n\n📱 Phone number bhejo (jaise 3494545456 ya 923135645789)", parse_mode="Markdown")

async def sim_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    
    if not number.isdigit():
        await update.message.reply_text("❌ Sirf digits ka number bhejo")
        return
    
    joined = await is_user_joined(update, context)
    if not joined:
        await start(update, context)
        return

    entries = intelligenceDB.get(number)
    if not entries:
        await update.message.reply_text("❌ Koi data nahi mila is number ke liye")
        return
    
    msg = f"🇵🇰 *PAK SIM INFO* ({number})\n\n"
    for idx, data in enumerate(entries, 1):
        msg += f"🔹 Entry {idx}:\n"
        msg += f"   *Full Name*: `{data['full_name']}`\n"
        msg += f"   *Phone*: `{data['phone']}`\n"
        msg += f"   *CNIC*: `{data['cnic']}`\n"
        msg += f"   *Address*: `{data['address']}`\n\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sim_info))
    app.run_polling()

if __name__ == "__main__":
    main()
