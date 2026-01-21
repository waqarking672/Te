from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import requests, re, os, instaloader, asyncio, phonenumbers, socket
from phonenumbers import geocoder, carrier, timezone
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"

CHANNEL_USERNAME = "@e3hacker"
CHANNEL_LINK = "https://t.me/e3hacker"
ADMIN_CONTACT = "@e3hacker2"

TEMPM_API_BASE = "https://temp-mail-fak.jokerkeep057.workers.dev/"
TEMPM_API_KEY = "32563"

IG_SAVE_PATH = "/tmp/INSTALOADER"
# =========================================

# ================= MENUS =================
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 TikTok", callback_data="tiktok"),
            InlineKeyboardButton("📸 Instagram", callback_data="instagram")
        ],
        [
            InlineKeyboardButton("🤖 AI IMAGE", callback_data="ai_image"),
            InlineKeyboardButton("🌐 IP & Number Info", callback_data="ip_number")
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

# ================= INPUT =================
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get("mode")

    if mode == "ai_image":
        await generate_ai_image(update, context, text)
        return
    elif mode == "ip_number_ip":
        result = await get_extended_ip_info(text)
    elif mode == "ip_number_phone":
        result = await get_extended_phone_info(text)
    elif "tiktok.com" in text:
        await fetch_tiktok(update, text)
        return
    elif "instagram.com" in text:
        await fetch_instagram(update, text)
        return
    else:
        await update.message.reply_text("❌ Invalid input")
        return

    keyboard = [
        [InlineKeyboardButton("🔙 Back to menu", callback_data="menu")],
        [InlineKeyboardButton("📢 Join the channel", url=CHANNEL_LINK)]
    ]
    await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ================= AI IMAGE =================
async def generate_ai_image(update, context, description):
    msg = await update.message.reply_text("🎨 Generating AI Image...")
    headers = {
        'accept': '*/*',
        'origin': 'https://www.writecream.com',
        'referer': 'https://www.writecream.com/',
        'user-agent': 'Mozilla/5.0'
    }
    params = {
        'prompt': description,
        'aspect_ratio': '16:9',
        'link': 'writecream.com',
        'description': description,
    }
    try:
        r = requests.get(
            'https://1yjs1yldj7.execute-api.us-east-1.amazonaws.com/default/ai_image',
            params=params,
            headers=headers,
            timeout=30
        ).json()
        image = r.get("image_link")
        if not image:
            await msg.edit_text("❌ Image generation failed")
            return
        await update.message.reply_photo(photo=image, caption=f"🤖 AI IMAGE\n📝 Prompt:\n{description}")
        context.user_data.pop("mode", None)
    except:
        await msg.edit_text("❌ Error generating image")

# ================= TikTok =================
async def fetch_tiktok(update, url):
    msg = await update.message.reply_text("⏳ Downloading...")
    try:
        api = f"https://mrking-tiktok-download-api.deno.dev/?url={url}"
        video = requests.get(api, timeout=15).json().get("video")
        r = requests.get(video)
        open("tiktok.mp4", "wb").write(r.content)
        await update.message.reply_video(open("tiktok.mp4", "rb"))
        os.remove("tiktok.mp4")
    except:
        await msg.edit_text("❌ TikTok download failed")

# ================= Instagram =================
async def fetch_instagram(update, url):
    msg = await update.message.reply_text("⏳ Downloading...")
    try:
        code = re.search(r"/(reel|p)/([^/?]+)", url).group(2)
        os.makedirs(IG_SAVE_PATH, exist_ok=True)
        loader = instaloader.Instaloader(download_videos=True, quiet=True, dirname_pattern=IG_SAVE_PATH, filename_pattern="{shortcode}")
        post = instaloader.Post.from_shortcode(loader.context, code)
        loader.download_post(post, "")
        path = f"{IG_SAVE_PATH}/{code}.mp4"
        await update.message.reply_video(open(path, "rb"))
        os.remove(path)
    except:
        await msg.edit_text("❌ Instagram download failed")

# ================= TEMPMail =================
async def auto_refresh(context):
    chat_id = context.job.chat_id
    session = context.job.data
    r = requests.get(f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=inbox&session={session}").json()
    for m in r.get("inbox", []):
        await context.bot.send_message(chat_id, f"📩 {m.get('subject')}\nFrom: {m.get('from')}")

async def temp_new_email(update, context):
    q = update.callback_query
    await q.answer()
    for job in context.job_queue.get_jobs_by_name(str(q.message.chat_id)):
        job.schedule_removal()
    r = requests.get(f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=generate").json()
    context.user_data["session"] = r["sessionId"]
    await q.message.reply_text(f"📧 Email Created\n{r['emailAddress']}", reply_markup=tempmail_menu())
    context.job_queue.run_repeating(auto_refresh, interval=15, first=15, chat_id=q.message.chat_id, name=str(q.message.chat_id), data=r["sessionId"])

async def temp_inbox(update, context):
    q = update.callback_query
    await q.answer()
    r = requests.get(f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=inbox&session={context.user_data.get('session')}").json()
    for m in r.get("inbox", []):
        await q.message.reply_text(f"📩 {m.get('subject')}\nFrom: {m.get('from')}")

# ================= IP & Number Info =================
async def get_extended_ip_info(ip):
    try:
        url = f"http://ip-api.com/json/{ip}?fields=66846719"
        r = await asyncio.to_thread(requests.get, url)
        data = r.json()
        if data.get('status') != 'success': return "❌ IP info not found"
        return f"🌐 *IP Info*: `{ip}`\nCountry: {data.get('country','N/A')}\nCity: {data.get('city','N/A')}\nISP: {data.get('isp','N/A')}"
    except: return "❌ Error fetching IP info"

async def get_extended_phone_info(number):
    try:
        parsed = phonenumbers.parse(number, None)
        if not phonenumbers.is_valid_number(parsed): return "❌ Invalid number"
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        country = geocoder.description_for_number(parsed, "en")
        operator_name = carrier.name_for_number(parsed, "en")
        tz = timezone.time_zones_for_number(parsed)
        return f"📱 *Number Info*: `{formatted}`\nCountry: {country}\nOperator: {operator_name}\nTimezones: {', '.join(tz)}"
    except: return "❌ Error fetching number info"

# ================= BUTTON HANDLER =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "joined":
        await start(update, context)
    elif q.data == "menu":
        await start(update, context)
    elif q.data == "tiktok":
        await q.message.reply_text("🎬 Send TikTok link")
    elif q.data == "instagram":
        await q.message.reply_text("📸 Send Instagram link")
    elif q.data == "ai_image":
        context.user_data["mode"] = "ai_image"
        await q.message.reply_text("🤖 Send image description")
    elif q.data == "ip_number":
        kb = [[InlineKeyboardButton("🌐 IP Info", callback_data="ip_info")],
              [InlineKeyboardButton("📱 Number Info", callback_data="phone_info")],
              [InlineKeyboardButton("🔙 Back", callback_data="menu")]]
        await q.message.reply_text("Select IP or Number tool", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data == "ip_info":
        context.user_data["mode"] = "ip_number_ip"
        await q.message.reply_text("🌐 Send IP address (e.g., 8.8.8.8)")
    elif q.data == "phone_info":
        context.user_data["mode"] = "ip_number_phone"
        await q.message.reply_text("📱 Send phone number (e.g., +919912345678)")
    elif q.data == "tempmail":
        await q.message.reply_text("📧 TempMail Menu", reply_markup=tempmail_menu())
    elif q.data == "new_email":
        await temp_new_email(update, context)
    elif q.data == "inbox":
        await temp_inbox(update, context)
    elif q.data == "admin":
        await q.message.reply_text(f"👤 Contact: {ADMIN_CONTACT}")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
    msg = await update.message.reply_text("🎨 Generating AI Image...")

    headers = {
        'accept': '*/*',
        'origin': 'https://www.writecream.com',
        'referer': 'https://www.writecream.com/',
        'user-agent': 'Mozilla/5.0'
    }

    params = {
        'prompt': description,
        'aspect_ratio': '16:9',
        'link': 'writecream.com',
        'description': description,
    }

    try:
        r = requests.get(
            'https://1yjs1yldj7.execute-api.us-east-1.amazonaws.com/default/ai_image',
            params=params,
            headers=headers,
            timeout=30
        ).json()

        image = r.get("image_link")

        if not image:
            await msg.edit_text("❌ Image generation failed")
            return

        await update.message.reply_photo(
            photo=image,
            caption=f"🤖 AI IMAGE\n\n📝 Prompt:\n{description}"
        )

        context.user_data.pop("mode", None)

    except:
        await msg.edit_text("❌ Error generating image")


# ================= TikTok =================
async def fetch_tiktok(update, url):
    msg = await update.message.reply_text("⏳ Downloading...")
    try:
        api = f"https://mrking-tiktok-download-api.deno.dev/?url={url}"
        video = requests.get(api, timeout=15).json().get("video")
        r = requests.get(video)
        open("tiktok.mp4", "wb").write(r.content)
        await update.message.reply_video(open("tiktok.mp4", "rb"))
        os.remove("tiktok.mp4")
    except:
        await msg.edit_text("❌ TikTok download failed")


# ================= Instagram =================
async def fetch_instagram(update, url):
    msg = await update.message.reply_text("⏳ Downloading...")
    try:
        code = re.search(r"/(reel|p)/([^/?]+)", url).group(2)
        os.makedirs(IG_SAVE_PATH, exist_ok=True)

        loader = instaloader.Instaloader(
            download_videos=True,
            quiet=True,
            dirname_pattern=IG_SAVE_PATH,
            filename_pattern="{shortcode}"
        )

        post = instaloader.Post.from_shortcode(loader.context, code)
        loader.download_post(post, "")

        path = f"{IG_SAVE_PATH}/{code}.mp4"
        await update.message.reply_video(open(path, "rb"))
        os.remove(path)
    except:
        await msg.edit_text("❌ Instagram download failed")


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

    for job in context.job_queue.get_jobs_by_name(str(q.message.chat_id)):
        job.schedule_removal()

    r = requests.get(
        f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=generate"
    ).json()

    context.user_data["session"] = r["sessionId"]

    await q.message.reply_text(
        f"📧 Email Created\n{r['emailAddress']}",
        reply_markup=tempmail_menu()
    )

    context.job_queue.run_repeating(
        auto_refresh,
        interval=15,
        first=15,
        chat_id=q.message.chat_id,
        name=str(q.message.chat_id),
        data=r["sessionId"]
    )


async def temp_inbox(update, context):
    q = update.callback_query
    await q.answer()

    r = requests.get(
        f"{TEMPM_API_BASE}?key={TEMPM_API_KEY}&action=inbox&session={context.user_data.get('session')}"
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

    elif q.data == "tiktok":
        await q.message.reply_text("🎬 Send TikTok link")

    elif q.data == "instagram":
        await q.message.reply_text("📸 Send Instagram link")

    elif q.data == "ai_image":
        context.user_data["mode"] = "ai_image"
        await q.message.reply_text("🤖 Send image description")

    elif q.data == "admin":
        await q.message.reply_text(f"👤 Contact: {ADMIN_CONTACT}")

    elif q.data == "tempmail":
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
