import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= CONFIG =================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"
CHANNEL_USERNAME = "@e3hacker"
ADMIN_ID = 7763525520   # your Telegram numeric ID
NEW_USER_POINTS = 5
REFERRER_POINTS = 5
# =========================================


# ---------- DATABASE ----------
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    referred_by INTEGER
)
""")
conn.commit()


def user_exists(user_id):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone() is not None


def add_user(user_id, referred_by=None):
    cur.execute(
        "INSERT INTO users (user_id, points, referred_by) VALUES (?, ?, ?)",
        (user_id, NEW_USER_POINTS, referred_by),
    )
    conn.commit()


def add_points(user_id, points):
    cur.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (points, user_id),
    )
    conn.commit()


def get_points(user_id):
    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    r = cur.fetchone()
    return r[0] if r else 0


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # referral handling
    if not user_exists(user_id):
        referred_by = None
        if args:
            ref_id = int(args[0])
            if ref_id != user_id and user_exists(ref_id):
                referred_by = ref_id
                add_points(ref_id, REFERRER_POINTS)

        add_user(user_id, referred_by)

    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("✅ Done", callback_data="check_join")]
    ]

    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "🔒 You must join our channel to use this bot.\n\n"
        "👉 Join channel then press **Done**.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ---------- FORCE JOIN CHECK ----------
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            points = get_points(user_id)
            await query.edit_message_text(
                f"✅ Access Granted!\n\n"
                f"⭐ Your Points: {points}\n\n"
                f"👥 Invite users using your referral link:\n"
                f"https://t.me/{context.bot.username}?start={user_id}"
            )
        else:
            raise Exception()

    except:
        await query.answer(
            "❌ Please join the channel first!",
            show_alert=True
        )


# ---------- ADMIN COMMAND ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    await update.message.reply_text(
        f"👑 Admin Panel\n\n"
        f"👥 Total Users: {total_users}"
    )


# ---------- POINTS ----------
async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    p = get_points(user_id)
    await update.message.reply_text(f"⭐ Your Points: {p}")


# ---------- MAIN ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("points", points))

    print("🤖 Bot is running successfully...")
    app.run_polling()


if __name__ == "__main__":
    main()
