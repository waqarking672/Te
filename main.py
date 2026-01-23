import asyncio
import sqlite3
import os
import re
import requests
import instaloader
import phonenumbers
import tempfile
import shutil
from datetime import datetime, timedelta
from phonenumbers import geocoder, carrier, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ================= CONFIG =================
BOT_TOKEN = os.getenv("8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A")
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN not found in environment variables!")
    print("Create a .env file with: 8484540629:AAGDNlJw0sYtkpNkRk6HKFSGRtrqcfllI5A")
    exit(1)

CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@e3hacker")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/e3hacker")
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "@e3hacker2")

NEW_USER_POINTS = 5
REFERRER_POINTS = 5
ADMIN_ID = int(os.getenv("ADMIN_ID", "7763525520"))

# Create temp directory
TEMP_DIR = tempfile.mkdtemp(prefix="bot_")
IG_SAVE_PATH = os.path.join(TEMP_DIR, "INSTALOADER")
os.makedirs(IG_SAVE_PATH, exist_ok=True)
# =========================================

# ================= DATABASE =================
def get_db_connection():
    """Create a new database connection"""
    return sqlite3.connect("users.db", check_same_thread=False, timeout=10)

# Initialize database
def init_database():
    """Initialize the database tables"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            referred_by INTEGER,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
    finally:
        conn.close()

init_database()

def user_exists(user_id):
    """Check if user exists in database"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        return cur.fetchone() is not None
    finally:
        conn.close()

def add_user(user_id, referred_by=None):
    """Add new user to database"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (user_id, points, referred_by) VALUES (?, ?, ?)",
            (user_id, NEW_USER_POINTS, referred_by)
        )
        conn.commit()
    finally:
        conn.close()

def add_points(user_id, points):
    """Add points to user"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (points, user_id))
        conn.commit()
    finally:
        conn.close()

def get_points(user_id):
    """Get user points"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        r = cur.fetchone()
        return r[0] if r else 0
    finally:
        conn.close()

def get_total_users():
    """Get total user count"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]
    finally:
        conn.close()
# =========================================

# ================= RATE LIMITER =================
class RateLimiter:
    """Simple rate limiter to prevent abuse"""
    def __init__(self):
        self.user_requests = {}
    
    def check_rate(self, user_id, limit=5, window=60):
        """Check if user is within rate limits"""
        now = datetime.now()
        
        # Initialize user entry if not exists
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Clean old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < timedelta(seconds=window)
        ]
        
        # Check if limit exceeded
        if len(self.user_requests[user_id]) >= limit:
            return False
        
        # Add current request
        self.user_requests[user_id].append(now)
        return True

rate_limiter = RateLimiter()
# =========================================

# ================= UTILITIES =================
def sanitize_input(text, max_length=500):
    """Sanitize user input to prevent injection"""
    if not text:
        return ""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\'\{\}\[\]\\]', '', text)
    # Limit length
    return text[:max_length]

def validate_url(url, platform):
    """Validate URLs"""
    patterns = {
        "tiktok": r"https?://(?:www\.|vm\.|vt\.)?tiktok\.com/(?:@[\w.-]+/video/|v/|t/|embed/|[\w.-]+/video/|video/)?(\d+)",
        "instagram": r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/([a-zA-Z0-9_-]+)"
    }
    pattern = patterns.get(platform)
    if not pattern:
        return False
    return re.match(pattern, url) is not None

def validate_phone_number(number):
    """Validate phone number"""
    try:
        parsed = phonenumbers.parse(number, None)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False

def validate_ip(ip):
    """Validate IP address"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    for part in parts:
        if not 0 <= int(part) <= 255:
            return False
    return True
# =========================================

# ================= MENUS =================
def main_menu():
    """Main menu keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 TikTok", callback_data="tiktok"),
         InlineKeyboardButton("📸 Instagram", callback_data="instagram")],
        [InlineKeyboardButton("🤖 AI IMAGE", callback_data="ai_image"),
         InlineKeyboardButton("🌐 IP & Number Info", callback_data="ip_number")],
        [InlineKeyboardButton("📊 My Points", callback_data="my_points"),
         InlineKeyboardButton("👤 Admin", callback_data="admin")],
        [InlineKeyboardButton("🔄 Refresh Menu", callback_data="refresh")]
    ])

def join_menu():
    """Join channel menu"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✔ I Joined", callback_data="joined")]
    ])

def back_menu():
    """Back button menu"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ])
# =========================================

# ================= CHANNEL CHECK =================
async def is_member(bot, user_id):
    """Check if user is channel member"""
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"Channel check error: {e}")
        return False
# =========================================

# ================= START COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    args = context.args
    context.user_data.clear()
    
    # Check rate limit
    if not rate_limiter.check_rate(user_id):
        await update.message.reply_text("⏳ Please wait before sending another request!")
        return
    
    # Check if user is channel member
    if not await is_member(context.bot, user_id):
        welcome_text = (
            f"👋 Welcome {user.first_name}!\n\n"
            f"📢 Please join our channel to use this bot:\n"
            f"{CHANNEL_USERNAME}\n\n"
            f"After joining, click 'I Joined' below 👇"
        )
        await update.message.reply_text(welcome_text, reply_markup=join_menu())
        return
    
    # Handle referral system
    if not user_exists(user_id):
        referred_by = None
        if args:
            try:
                ref_id = int(args[0])
                if ref_id != user_id and user_exists(ref_id):
                    referred_by = ref_id
                    add_points(ref_id, REFERRER_POINTS)
                    print(f"✅ User {user_id} referred by {ref_id}")
            except ValueError:
                pass
        add_user(user_id, referred_by)
        print(f"✅ New user added: {user_id}")
    
    # Get user points
    points = get_points(user_id)
    
    # Generate referral link
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    # Welcome message
    welcome_text = (
        f"✨ Welcome {user.first_name}!\n\n"
        f"⭐ Your Points: {points}\n\n"
        f"📢 **Referral System:**\n"
        f"Invite friends using your link:\n"
        f"`{referral_link}`\n\n"
        f"🎁 You get {REFERRER_POINTS} points for each referral!\n\n"
        f"👇 **Choose an option:**"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode='Markdown')
# =========================================

# ================= BUTTON HANDLER =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    # Check rate limit
    if not rate_limiter.check_rate(user_id):
        await query.message.reply_text("⏳ Please wait before another request!")
        return
    
    # Check channel membership
    if not await is_member(context.bot, user_id):
        await query.message.reply_text("❌ Please join the channel first!", reply_markup=join_menu())
        return
    
    if data == "joined":
        # User claims to have joined, verify
        if await is_member(context.bot, user_id):
            await start(update, context)
        else:
            await query.message.reply_text("❌ I can't see you in the channel yet! Please join first.", reply_markup=join_menu())
    
    elif data == "menu" or data == "refresh":
        # Return to main menu
        points = get_points(user_id)
        bot_username = context.bot.username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        
        menu_text = (
            f"🔄 Menu Refreshed!\n"
            f"⭐ Your Points: {points}\n\n"
            f"Your referral link:\n`{referral_link}`\n\n"
            f"👇 Choose an option:"
        )
        await query.message.edit_text(menu_text, reply_markup=main_menu(), parse_mode='Markdown')
    
    elif data == "my_points":
        points = get_points(user_id)
        bot_username = context.bot.username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        
        points_text = (
            f"📊 **Your Stats**\n\n"
            f"⭐ Points: {points}\n\n"
            f"🔗 **Referral Link:**\n"
            f"`{referral_link}`\n\n"
            f"👥 Earn {REFERRER_POINTS} points for each friend who joins!"
        )
        await query.message.edit_text(points_text, reply_markup=back_menu(), parse_mode='Markdown')
    
    elif data == "tiktok":
        await query.message.edit_text(
            "🎬 **TikTok Downloader**\n\n"
            "Send me a TikTok video link (URL)\n\n"
            "Example: https://tiktok.com/@username/video/123456789",
            reply_markup=back_menu(),
            parse_mode='Markdown'
        )
        context.user_data["mode"] = "tiktok"
    
    elif data == "instagram":
        await query.message.edit_text(
            "📸 **Instagram Downloader**\n\n"
            "Send me an Instagram post/reel link (URL)\n\n"
            "Example: https://instagram.com/p/ABC123 or https://instagram.com/reel/XYZ456",
            reply_markup=back_menu(),
            parse_mode='Markdown'
        )
        context.user_data["mode"] = "instagram"
    
    elif data == "ai_image":
        await query.message.edit_text(
            "🤖 **AI Image Generator**\n\n"
            "Send me a description of the image you want to generate\n\n"
            "Example: 'A futuristic city with flying cars at sunset'",
            reply_markup=back_menu(),
            parse_mode='Markdown'
        )
        context.user_data["mode"] = "ai_image"
    
    elif data == "ip_number":
        kb = [
            [InlineKeyboardButton("🌐 IP Info Lookup", callback_data="ip_info")],
            [InlineKeyboardButton("📱 Phone Number Info", callback_data="phone_info")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu")]
        ]
        await query.message.edit_text(
            "🔍 **Information Tools**\n\n"
            "Select what you want to lookup:",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode='Markdown'
        )
    
    elif data == "ip_info":
        await query.message.edit_text(
            "🌐 **IP Information Lookup**\n\n"
            "Send me an IP address to get information\n\n"
            "Example: 8.8.8.8 or 1.1.1.1",
            reply_markup=back_menu(),
            parse_mode='Markdown'
        )
        context.user_data["mode"] = "ip_info"
    
    elif data == "phone_info":
        await query.message.edit_text(
            "📱 **Phone Number Information**\n\n"
            "Send me a phone number with country code\n\n"
            "Example: +919876543210 or +1234567890",
            reply_markup=back_menu(),
            parse_mode='Markdown'
        )
        context.user_data["mode"] = "phone_info"
    
    elif data == "admin":
        admin_text = (
            f"👑 **Admin Contact**\n\n"
            f"📞 Contact: {ADMIN_CONTACT}\n\n"
            f"⚠️ Only contact for serious issues or business inquiries."
        )
        await query.message.edit_text(admin_text, reply_markup=back_menu(), parse_mode='Markdown')
# =========================================

# ================= MESSAGE HANDLER =================
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user text input"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Check rate limit
    if not rate_limiter.check_rate(user_id):
        await update.message.reply_text("⏳ Please wait before sending another request!")
        return
    
    # Check channel membership
    if not await is_member(context.bot, user_id):
        await update.message.reply_text("❌ Please join the channel first!", reply_markup=join_menu())
        return
    
    mode = context.user_data.get("mode")
    
    if not mode:
        await update.message.reply_text("❌ Please select an option from the menu first!", reply_markup=main_menu())
        return
    
    # Sanitize input
    text = sanitize_input(text)
    
    if mode == "tiktok":
        await fetch_tiktok(update, text)
    
    elif mode == "instagram":
        await fetch_instagram(update, text)
    
    elif mode == "ai_image":
        await generate_ai_image(update, text)
    
    elif mode == "ip_info":
        await get_ip_info(update, text)
    
    elif mode == "phone_info":
        await get_phone_info(update, text)
    
    # Clear mode after processing
    context.user_data.pop("mode", None)
# =========================================

# ================= AI IMAGE GENERATOR =================
async def generate_ai_image(update, description):
    """Generate AI image from description"""
    if len(description) < 5:
        await update.message.reply_text("❌ Description too short! Please provide more details.")
        return
    
    msg = await update.message.reply_text("🎨 Generating your AI image... This may take a moment...")
    
    try:
        headers = {
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        params = {
            'prompt': description,
            'aspect_ratio': '16:9',
            'description': description
        }
        
        # Use async thread to avoid blocking
        response = await asyncio.to_thread(
            requests.get,
            'https://1yjs1yldj7.execute-api.us-east-1.amazonaws.com/default/ai_image',
            params=params,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            image_url = data.get("image_link")
            
            if image_url:
                await msg.edit_text("✅ Image generated! Sending now...")
                await update.message.reply_photo(
                    photo=image_url,
                    caption=f"🤖 **AI Generated Image**\n\n📝 **Prompt:**\n{description}\n\n✨ Generated by @{update.effective_user.username if update.effective_user.username else 'User'}",
                    parse_mode='Markdown'
                )
                await msg.delete()
            else:
                await msg.edit_text("❌ Failed to generate image. Please try a different description.")
        else:
            await msg.edit_text("❌ Image generation service is currently unavailable. Please try again later.")
    
    except requests.exceptions.Timeout:
        await msg.edit_text("⏰ Request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        await msg.edit_text(f"❌ Network error: {str(e)[:100]}")
    except Exception as e:
        await msg.edit_text(f"❌ Error generating image: {str(e)[:100]}")
# =========================================

# ================= IP INFORMATION =================
async def get_ip_info(update, ip_address):
    """Get information about an IP address"""
    if not validate_ip(ip_address):
        await update.message.reply_text("❌ Invalid IP address format! Use format like: 8.8.8.8")
        return
    
    msg = await update.message.reply_text(f"🔍 Looking up information for IP: {ip_address}...")
    
    try:
        response = await asyncio.to_thread(
            requests.get,
            f"http://ip-api.com/json/{ip_address}",
            timeout=10
        )
        
        data = response.json()
        
        if data.get("status") == "success":
            info_text = (
                f"🌐 **IP Information**\n\n"
                f"📍 **IP Address:** `{data.get('query', 'N/A')}`\n"
                f"🏛️ **Country:** {data.get('country', 'N/A')}\n"
                f"🏙️ **Region:** {data.get('regionName', 'N/A')}\n"
                f"🏘️ **City:** {data.get('city', 'N/A')}\n"
                f"📮 **ZIP Code:** {data.get('zip', 'N/A')}\n"
                f"📍 **Timezone:** {data.get('timezone', 'N/A')}\n"
                f"📡 **ISP:** {data.get('isp', 'N/A')}\n"
                f"🏢 **Organization:** {data.get('org', 'N/A')}\n"
                f"📍 **Location:** Lat: {data.get('lat', 'N/A')}, Lon: {data.get('lon', 'N/A')}"
            )
            await msg.edit_text(info_text, parse_mode='Markdown')
        else:
            await msg.edit_text(f"❌ Could not find information for IP: {ip_address}")
    
    except requests.exceptions.Timeout:
        await msg.edit_text("⏰ Request timed out. Please try again.")
    except Exception as e:
        await msg.edit_text(f"❌ Error fetching IP information: {str(e)[:100]}")
# =========================================

# ================= PHONE INFORMATION =================
async def get_phone_info(update, phone_number):
    """Get information about a phone number"""
    if not validate_phone_number(phone_number):
        await update.message.reply_text("❌ Invalid phone number! Use format with country code like: +919876543210")
        return
    
    msg = await update.message.reply_text(f"🔍 Looking up information for: {phone_number}...")
    
    try:
        parsed_number = phonenumbers.parse(phone_number, None)
        
        if not phonenumbers.is_valid_number(parsed_number):
            await msg.edit_text("❌ Invalid phone number!")
            return
        
        # Format the number
        formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        
        # Get information
        country = geocoder.description_for_number(parsed_number, "en") or "Unknown"
        carrier_name = carrier.name_for_number(parsed_number, "en") or "Unknown"
        time_zones = timezone.time_zones_for_number(parsed_number)
        timezone_str = ", ".join(time_zones) if time_zones else "Unknown"
        number_type = phonenumbers.number_type(parsed_number)
        
        # Convert number type to readable string
        type_map = {
            0: "Fixed line",
            1: "Mobile",
            2: "Fixed line or mobile",
            3: "Toll free",
            4: "Premium rate",
            5: "Shared cost",
            6: "VOIP",
            7: "Personal number",
            8: "Pager",
            9: "UAN",
            10: "Voicemail",
            27: "Unknown"
        }
        number_type_str = type_map.get(number_type, "Unknown")
        
        info_text = (
            f"📱 **Phone Number Information**\n\n"
            f"📞 **Number:** `{formatted}`\n"
            f"🌍 **Country:** {country}\n"
            f"📡 **Carrier:** {carrier_name}\n"
            f"🕐 **Timezone(s):** {timezone_str}\n"
            f"📊 **Type:** {number_type_str}\n"
            f"✅ **Valid:** Yes\n"
            f"🌐 **Country Code:** +{parsed_number.country_code}"
        )
        
        await msg.edit_text(info_text, parse_mode='Markdown')
    
    except Exception as e:
        await msg.edit_text(f"❌ Error fetching phone information: {str(e)[:100]}")
# =========================================

# ================= TIKTOK DOWNLOADER =================
async def fetch_tiktok(update, url):
    """Download TikTok video"""
    if not validate_url(url, "tiktok"):
        await update.message.reply_text("❌ Invalid TikTok URL! Please send a valid TikTok video link.")
        return
    
    msg = await update.message.reply_text("⏳ Downloading TikTok video... This may take a moment...")
    
    try:
        # Try multiple TikTok API endpoints
        apis = [
            f"https://api.tiklydown.com/api/download?url={url}",
            f"https://www.tikwm.com/api/?url={url}",
            f"https://tikdown.io/download?url={url}"
        ]
        
        video_url = None
        for api in apis:
            try:
                response = await asyncio.to_thread(requests.get, api, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    # Try different response formats
                    video_url = (
                        data.get("video") or 
                        data.get("data", {}).get("play") or 
                        data.get("data", {}).get("wmplay") or
                        data.get("play")
                    )
                    if video_url:
                        break
            except:
                continue
        
        if not video_url:
            await msg.edit_text("❌ Could not fetch TikTok video. The link might be invalid or private.")
            return
        
        # Download video
        video_response = await asyncio.to_thread(requests.get, video_url, timeout=30, stream=True)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            for chunk in video_response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_path = tmp_file.name
        
        # Check file size
        file_size = os.path.getsize(tmp_path)
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            os.remove(tmp_path)
            await msg.edit_text("❌ Video is too large to send via Telegram (max 50MB)")
            return
        
        await msg.edit_text("✅ Download complete! Sending video...")
        
        # Send video
        with open(tmp_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="🎬 **TikTok Video**\n\nDownloaded via @{}".format(
                    update.effective_user.username if update.effective_user.username else "Bot"
                ),
                parse_mode='Markdown'
            )
        
        await msg.delete()
        
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    except requests.exceptions.Timeout:
        await msg.edit_text("⏰ Download timed out. Please try again.")
    except Exception as e:
        await msg.edit_text(f"❌ Failed to download TikTok: {str(e)[:100]}")
# =========================================

# ================= INSTAGRAM DOWNLOADER =================
async def fetch_instagram(update, url):
    """Download Instagram post/reel"""
    if not validate_url(url, "instagram"):
        await update.message.reply_text("❌ Invalid Instagram URL! Please send a valid Instagram post/reel link.")
        return
    
    msg = await update.message.reply_text("⏳ Downloading Instagram content... This may take a moment...")
    
    try:
        # Extract shortcode from URL
        match = re.search(r"(?:p|reel|tv)/([a-zA-Z0-9_-]+)", url)
        if not match:
            await msg.edit_text("❌ Could not extract post ID from URL")
            return
        
        shortcode = match.group(1)
        
        # Create Instagram loader
        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern="",
            dirname_pattern=IG_SAVE_PATH,
            filename_pattern="{shortcode}",
            quiet=True
        )
        
        # Try to login anonymously (for public posts)
        try:
            loader.load_session_from_file("instagram_session")
        except:
            pass
        
        # Download post
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        
        # Check if post exists
        if not post:
            await msg.edit_text("❌ Post not found or might be private")
            return
        
        # Download the post
        loader.download_post(post, target=IG_SAVE_PATH)
        
        # Find downloaded file
        downloaded_files = []
        for ext in ['.mp4', '.jpg', '.png']:
            file_path = os.path.join(IG_SAVE_PATH, f"{shortcode}{ext}")
            if os.path.exists(file_path):
                downloaded_files.append(file_path)
        
        if not downloaded_files:
            await msg.edit_text("❌ No media found in the post")
            return
        
        await msg.edit_text("✅ Download complete! Sending media...")
        
        # Send the file(s)
        for file_path in downloaded_files:
            file_size = os.path.getsize(file_path)
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                await update.message.reply_text(f"❌ File too large to send: {os.path.basename(file_path)}")
                continue
            
            if file_path.endswith('.mp4'):
                with open(file_path, 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption="📸 **Instagram Video**\n\nDownloaded via @{}".format(
                            update.effective_user.username if update.effective_user.username else "Bot"
                        ),
                        parse_mode='Markdown'
                    )
            else:
                with open(file_path, 'rb') as image_file:
                    await update.message.reply_photo(
                        photo=image_file,
                        caption="📸 **Instagram Photo**\n\nDownloaded via @{}".format(
                            update.effective_user.username if update.effective_user.username else "Bot"
                        ),
                        parse_mode='Markdown'
                    )
        
        await msg.delete()
        
        # Cleanup downloaded files
        for file_path in downloaded_files:
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except instaloader.exceptions.InstaloaderException as e:
        await msg.edit_text(f"❌ Instagram error: {str(e)[:100]}")
    except Exception as e:
        await msg.edit_text(f"❌ Failed to download Instagram content: {str(e)[:100]}")
# =========================================

# ================= ADMIN COMMAND =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel command"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to access this command!")
        return
    
    total_users = get_total_users()
    
    admin_text = (
        f"👑 **Admin Panel**\n\n"
        f"📊 **Statistics:**\n"
        f"• Total Users: {total_users}\n"
        f"• Your ID: {user_id}\n\n"
        f"📞 **Contact:** {ADMIN_CONTACT}\n\n"
        f"⚙️ **Bot Status:** Running ✅"
    )
    
    await update.message.reply_text(admin_text, parse_mode='Markdown')
# =========================================

# ================= CLEANUP =================
def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
            print(f"✅ Cleaned up temp directory: {TEMP_DIR}")
    except Exception as e:
        print(f"⚠️ Could not clean temp directory: {e}")
# =========================================

# ================= MAIN FUNCTION =================
def main():
    """Main function to start the bot"""
    print("=" * 50)
    print("🤖 Starting Multi-Tool Bot...")
    print(f"📁 Temp directory: {TEMP_DIR}")
    print(f"📊 Database: users.db")
    print("=" * 50)
    
    # Register cleanup on exit
    import atexit
    atexit.register(cleanup_temp_files)
    
    try:
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("admin", admin_panel))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
        
        # Start the bot
        print("✅ Bot is now running...")
        print("📱 Press Ctrl+C to stop")
        print("=" * 50)
        
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        cleanup_temp_files()
        exit(1)

if __name__ == "__main__":
    main()
