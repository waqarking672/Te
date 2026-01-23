import asyncio, aiohttp, phonenumbers
from phonenumbers import geocoder, carrier, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================= CONFIG =================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"
BOT_USERNAME = "siminfodata_pk_bot"   # without @
CHANNEL_USERNAME = "@e3hacker"
CHANNEL_LINK = "https://t.me/e3hacker"

ADMIN_ID = 7763525520  # your Telegram numeric ID

NEW_USER_POINTS = 5
REFERRAL_POINTS = 5

# ================= DATABASE (MEMORY) =================
users = {}  # user_id: {"points": int, "referrals": int}

# ================= MENUS =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 My Points", callback_data="points")],
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 User Stats", callback_data="stats")],
        [InlineKeyboardButton("➕ Add Points", callback_data="add_points")],
        [InlineKeyboardButton("➖ Remove Points", callback_data="remove_points")]
    ])

def join_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✔ I Joined", callback_data="joined")]
    ])

# ================= UTILS =================
async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

def add_user(user_id):
    if user_id not in users:
        users[user_id] = {"points": NEW_USER_POINTS, "referrals": 0}

# ================= START + REFERRAL =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not await is_member(context.bot, user_id):
        await update.message.reply_text(
            "❌ Please join the channel first",
            reply_markup=join_menu()
        )
        return

    if user_id not in users:
        add_user(user_id)

        # Referral logic
        if args:
            ref_id = int(args[0])
            if ref_id != user_id and ref_id in users:
                users[ref_id]["points"] += REFERRAL_POINTS
                users[ref_id]["referrals"] += 1

    await update.message.reply_text(
        "✨ Welcome! Choose an option:",
        reply_markup=main_menu()
    )

# ================= BUTTON HANDLER =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "joined":
        await start(update, context)

    elif q.data == "points":
        user = users.get(uid)
        ref_link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await q.message.reply_text(
            f"🎁 Your Points: {user['points']}\n"
            f"👥 Referrals: {user['referrals']}\n\n"
            f"🔗 Your Referral Link:\n{ref_link}"
        )

    elif q.data == "admin":
        if uid != ADMIN_ID:
            await q.message.reply_text("❌ Admin access only")
            return
        await q.message.reply_text("👑 Admin Panel", reply_markup=admin_menu())

    elif q.data == "stats" and uid == ADMIN_ID:
        await q.message.reply_text(f"📊 Total Users: {len(users)}")

    elif q.data in ("add_points", "remove_points") and uid == ADMIN_ID:
        context.user_data["admin_mode"] = q.data
        await q.message.reply_text("Send the User ID")

# ================= TEXT HANDLER =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    # Admin actions
    if context.user_data.get("admin_mode") and uid == ADMIN_ID:
        target = int(text)
        if target not in users:
            await update.message.reply_text("❌ User not found")
            return

        if context.user_data["admin_mode"] == "add_points":
            users[target]["points"] += 10
            await update.message.reply_text("✅ 10 points added")
        else:
            users[target]["points"] = max(0, users[target]["points"] - 10)
            await update.message.reply_text("✅ 10 points removed")

        context.user_data.clear()
        return

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
