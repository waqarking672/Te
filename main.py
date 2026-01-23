import asyncio
import sqlite3, os, re, requests, instaloader, phonenumbers
from phonenumbers import geocoder, carrier, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ================= CONFIG =================
BOT_TOKEN = "8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A"
CHANNEL_USERNAME = "@e3hacker"
CHANNEL_LINK = "https://t.me/e3hacker"
ADMIN_CONTACT = "@e3hacker2"
IG_SAVE_PATH = "/tmp/INSTALOADER"

NEW_USER_POINTS = 5
REFERRER_POINTS = 5
ADMIN_ID = 7763525520
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
        (user_id, NEW_USER_POINTS, referred_by)
    )
    conn.commit()

def add_points(user_id, points):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (points, user_id))
    conn.commit()

def get_points(user_id):
    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    r = cur.fetchone()
    return r[0] if r else 0

# ---------- MENUS ----------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 TikTok", callback_data="tiktok"),
         InlineKeyboardButton("📸 Instagram", callback_data="instagram")],
        [InlineKeyboardButton("🤖 AI IMAGE", callback_data="ai_image"),
         InlineKeyboardButton("🌐 IP & Number Info", callback_data="ip_number")],
        [InlineKeyboardButton("📧 TempMail", callback_data="tempmail")],
        [InlineKeyboardButton("👤 Admin", callback_data="admin")]
    ])

def join_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✔ I Joined", callback_data="joined")]
    ])

# ---------- UTILS ----------
async def is_member(bot, user_id):
    try:
        m = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in ("member", "administrator", "creator")
    except:
        return False

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    context.user_data.clear()

    # Referral system
    if not user_exists(user_id):
        referred_by = None
        if args:
            try:
                ref_id = int(args[0])
                if ref_id != user_id and user_exists(ref_id):
                    referred_by = ref_id
                    add_points(ref_id, REFERRER_POINTS)
            except: 
                pass
        add_user(user_id, referred_by)

    if not await is_member(context.bot, user_id):
        await update.message.reply_text("❌ Join channel first", reply_markup=join_menu())
        return

    points = get_points(user_id)
    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    await update.message.reply_text(
        f"✨ Welcome!\n⭐ Your Points: {points}\n\n"
        f"👥 Invite users using your referral link:\n{referral_link}\n\n"
        f"Choose option 👇",
        reply_markup=main_menu()
    )

# ---------- BUTTON HANDLER ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    data = q.data

    if data in ["joined", "menu"]:
        await start(update, context)

    elif data == "tiktok":
        await q.message.reply_text("🎬 Send TikTok link")
        context.user_data["mode"] = "tiktok"

    elif data == "instagram":
        await q.message.reply_text("📸 Send Instagram link")
        context.user_data["mode"] = "instagram"

    elif data == "ai_image":
        await q.message.reply_text("🤖 Send AI Image description")
        context.user_data["mode"] = "ai_image"

    elif data == "ip_number":
        kb = [
            [InlineKeyboardButton("🌐 IP Info", callback_data="ip_info")],
            [InlineKeyboardButton("📱 Number Info", callback_data="phone_info")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu")]
        ]
        await q.message.reply_text("Select IP or Number tool", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "ip_info":
        await q.message.reply_text("🌐 Send IP address (example: 8.8.8.8)")
        context.user_data["mode"] = "ip_number_ip"

    elif data == "phone_info":
        await q.message.reply_text("📱 Send phone number (example: +919912345678)")
        context.user_data["mode"] = "ip_number_phone"

    elif data == "admin":
        await q.message.reply_text(f"👤 Contact: {ADMIN_CONTACT}")

# ---------- HANDLE INPUT ----------
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    text = update.message.text.strip()
    if not mode:
        await update.message.reply_text("❌ Please select an option from menu first")
        return

    if mode == "tiktok":
        await fetch_tiktok(update, text)
    elif mode == "instagram":
        await fetch_instagram(update, text)
    elif mode == "ai_image":
        await generate_ai_image(update, text)
    elif mode == "ip_number_ip":
        result = await get_extended_ip_info(text)
        await update.message.reply_text(result)
    elif mode == "ip_number_phone":
        result = await get_extended_phone_info(text)
        await update.message.reply_text(result)

    context.user_data.pop("mode", None)

# ---------- AI IMAGE ----------
async def generate_ai_image(update, description):
    msg = await update.message.reply_text("🎨 Generating AI Image...")
    try:
        headers = {'accept':'*/*','user-agent':'Mozilla/5.0'}
        params = {'prompt': description, 'aspect_ratio':'16:9', 'description': description}
        r = await asyncio.to_thread(requests.get, 'https://1yjs1yldj7.execute-api.us-east-1.amazonaws.com/default/ai_image', params=params, headers=headers, timeout=30)
        r_json = r.json()
        image = r_json.get("image_link")
        if not image:
            await msg.edit_text("❌ Image generation failed")
            return
        await update.message.reply_photo(photo=image, caption=f"🤖 AI IMAGE\n📝 Prompt:\n{description}")
    except:
        await msg.edit_text("❌ Error generating image")

# ---------- IP & PHONE ----------
async def get_extended_ip_info(ip):
    try:
        r = await asyncio.to_thread(requests.get, f"http://ip-api.com/json/{ip}")
        data = r.json()
        if data.get("status")!="success": return "❌ IP info not found"
        return f"🌐 *IP Info*: `{ip}`\nCountry: {data.get('country','N/A')}\nCity: {data.get('city','N/A')}\nISP: {data.get('isp','N/A')}"
    except:
        return "❌ Error fetching IP info"

async def get_extended_phone_info(number):
    try:
        parsed = phonenumbers.parse(number, None)
        if not phonenumbers.is_valid_number(parsed): return "❌ Invalid number"
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        country = geocoder.description_for_number(parsed, "en")
        operator_name = carrier.name_for_number(parsed, "en")
        tz = timezone.time_zones_for_number(parsed)
        return f"📱 *Number Info*: `{formatted}`\nCountry: {country}\nOperator: {operator_name}\nTimezones: {', '.join(tz)}"
    except:
        return "❌ Error fetching number info"

# ---------- TikTok ----------
async def fetch_tiktok(update, url):
    msg = await update.message.reply_text("⏳ Downloading TikTok...")
    try:
        api = f"https://mrking-tiktok-download-api.deno.dev/?url={url}"
        video = requests.get(api, timeout=15).json().get("video")
        r = requests.get(video)
        open("tiktok.mp4","wb").write(r.content)
        await update.message.reply_video(open("tiktok.mp4","rb"))
        os.remove("tiktok.mp4")
    except:
        await msg.edit_text("❌ TikTok download failed")

# ---------- Instagram ----------
async def fetch_instagram(update, url):
    msg = await update.message.reply_text("⏳ Downloading Instagram...")
    try:
        code = re.search(r"/(reel|p)/([^/?]+)", url).group(2)
        os.makedirs(IG_SAVE_PATH, exist_ok=True)
        loader = instaloader.Instaloader(download_videos=True, quiet=True, dirname_pattern=IG_SAVE_PATH, filename_pattern="{shortcode}")
        post = instaloader.Post.from_shortcode(loader.context, code)
        loader.download_post(post, "")
        path = f"{IG_SAVE_PATH}/{code}.mp4"
        await update.message.reply_video(open(path,"rb"))
        os.remove(path)
    except:
        await msg.edit_text("❌ Instagram download failed")

# ---------- ADMIN ----------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    await update.message.reply_text(f"👑 Admin Panel\n\n👥 Total Users: {total_users}\n📞 Contact: {ADMIN_CONTACT}")

# ---------- MAIN ----------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("admin", admin_panel))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
