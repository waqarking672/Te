from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import requests, re, os, instaloader, asyncio

# ================= CONFIG =================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"

CHANNEL_USERNAME = "@e3hacker"
CHANNEL_LINK = "https://t.me/e3hacker"
ADMIN_CONTACT = "@e3hacker2"

SIM_API_URL = "https://fam-official.serv00.net/api/database.php?number="
CNIC_API_URL = "https://fam-official.serv00.net/api/database.php?number="

TEMPM_API_BASE = "https://temp-mail-fak.jokerkeep057.workers.dev/"
TEMPM_API_KEY = "32563"

IG_SAVE_PATH = "/tmp/INSTALOADER"
# =========================================


# ================= MENUS =================
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 SIM Info", callback_data="sim"),
            InlineKeyboardButton("🆔 CNIC Info", callback_data="cnic")
        ],
        [
            InlineKeyboardButton("🎬 TikTok", callback_data="tiktok"),
            InlineKeyboardButton("📸 Instagram", callback_data="instagram")
        ],
        [
            InlineKeyboardButton("📧 TempMail", callback_data="tempmail")
        ],
        [
            InlineKeyboardButton("👤 Admin", callback_data="admin")
        ]
    ])


def join_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✔ I Joined", callback_data="joined")]
    ])


def tempmail_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 New Email", callback_data="new_email")],
        [InlineKeyboardButton("📥 Inbox", callback_data="inbox")],
        [InlineKeyboardButton("⬅ Back", callback_data="menu")]
    ])


# ================= UTILS =================
async def is_member(bot, user_id):
    try:
        m = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ("member", "administrator", "creator")
    except:
        return False


def clean_text(t):
    return re.sub(r"(famofc|credit)", "", str(t), flags=re.I).strip()


def valid_mobile(t): return re.fullmatch(r"03\d{9}", t)
def valid_cnic(t): return re.fullmatch(r"\d{13}", t)


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    if not await is_member(context.bot, update.effective_user.id):
        await update.message.reply_text(
            "❌ Join channel first",
            reply_markup=join_menu()
        )
        return

    await update.message.reply_text(
        "✨ Welcome\nChoose option 👇",
        reply_markup=main_menu()
    )


async def joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await start(update, context)


# ================= INPUT =================
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if valid_mobile(text):
        await fetch_api(update, SIM_API_URL + text, "SIM Info")
    elif valid_cnic(text):
        await fetch_api(update, CNIC_API_URL + text, "CNIC Info")
    elif "tiktok.com" in text:
        await fetch_tiktok(update, text)
    elif "instagram.com" in text:
        await fetch_instagram(update, text)
    else:
        await update.message.reply_text("❌ Invalid input")


# ================= API =================
async def fetch_api(update, url, title):
    msg = await update.message.reply_text("⏳ Fetching...")
    try:
        r = requests.get(url, timeout=15).json()
        out = ""
        for k, v in r.items():
            k, v = clean_text(k), clean_text(v)
            if k and v:
                out += f"{k}: {v}\n"
        await msg.edit_text(f"📄 {title}\n\n{out}")
    except:
        await msg.edit_text("❌ Error")


# ================= TikTok =================
async def fetch_tiktok(update, url):
    msg = await update.message.reply_text("⏳ Downloading...")
    try:
        api = f"https://mrking-tiktok-download-api.deno.dev/?url={url}"
        video = requests.get(api).json().get("video")
        r = requests.get(video)
        open("t.mp4", "wb").write(r.content)
        await update.message.reply_video(open("t.mp4", "rb"))
        os.remove("t.mp4")
    except:
        await msg.edit_text("❌ Failed")


# ================= Instagram =================
async def fetch_instagram(update, url):
    msg = await update.message.reply_text("⏳ Downloading...")
    try:
        code = re.search(r"/(reel|p)/([^/?]+)", url).group(2)
        os.makedirs(IG_SAVE_PATH, exist_ok=True)
        loader = instaloader.Instaloader(
            download_videos=True, quiet=True,
            dirname_pattern=IG_SAVE_PATH,
            filename_pattern="{shortcode}"
        )
        post = instaloader.Post.from_shortcode(loader.context, code)
        loader.download_post(post, "")
        path = f"{IG_SAVE_PATH}/{code}.mp4"
        await update.message.reply_video(open(path, "rb"))
        os.remove(path)
    except:
        await msg.edit_text("❌ Failed")


# ================= TEMPMail =================
async def auto_refresh(context):
    chat_id = context.job.chat_id
    session = context.job.data
    r = requests.get(
        f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=inbox&session={session}"
    ).json()
    for m in r.get("inbox", []):
        await context.bot.send_message(
            chat_id,
            f"📩 {m.get('subject')}\nFrom: {m.get('from')}"
        )


async def temp_new_email(update, context):
    q = update.callback_query
    await q.answer()

    r = requests.get(
        f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=generate"
    ).json()

    context.user_data["session"] = r["sessionId"]
    context.user_data["email"] = r["emailAddress"]

    await q.message.reply_text(
        f"📧 Email Created\n{r['emailAddress']}",
        reply_markup=tempmail_menu()
    )

    context.job_queue.run_repeating(
        auto_refresh, interval=15, first=15,
        chat_id=q.message.chat_id,
        data=r["sessionId"]
    )


async def temp_inbox(update, context):
    q = update.callback_query
    await q.answer()

    r = requests.get(
        f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=inbox&session={context.user_data['session']}"
    ).json()

    for m in r.get("inbox", []):
        await q.message.reply_text(
            f"📩 {m.get('subject')}\nFrom: {m.get('from')}"
        )


# ================= BUTTONS =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "joined":
        await start(update, context)

    elif q.data == "menu":
        await q.message.reply_text("🏠 Main Menu", reply_markup=main_menu())

    elif q.data == "sim":
        await q.message.reply_text("Send mobile number")

    elif q.data == "cnic":
        await q.message.reply_text("Send CNIC number")

    elif q.data == "tiktok":
        await q.message.reply_text("Send TikTok link")

    elif q.data == "instagram":
        await q.message.reply_text("Send Instagram link")

    elif q.data == "admin":
        await q.message.reply_text(f"Contact: {ADMIN_CONTACT}")

    elif q.data == "tempmail":
        if not context.user_data.get("tm_open"):
            context.user_data["tm_open"] = True
            await q.message.reply_text("📧 TempMail Menu", reply_markup=tempmail_menu())

    elif q.data == "new_email":
        await temp_new_email(update, context)

    elif q.data == "inbox":
        await temp_inbox(update, context)


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
