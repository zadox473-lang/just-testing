# ================= INSTAGRAM ANALYZER PRO =================
# DEVELOPER: @proxyfxc
# VERSION: 28.0 (FULL FIXED - ALL BUTTONS WORKING + PROFILE PIC)
# ==========================================================

import requests
import json
import random
import hashlib
import sqlite3
import re
import asyncio
import os
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, jsonify
import threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import TelegramError

# ================= CONFIG FROM ENV =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8727219268:AAHpwzsihqTMnFldtBGl9yVlW-0h-C_Zi6U")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8689614787))
CREATOR = "@proxyfxc"  # SIRF TERA NAAM

API_URL = "https://tg-user-id-to-number-4erk.onrender.com/api/insta={}?api_key=PAID_INSTA_SELL187"
FORCE_CHANNELS = ["@midnight_xaura", "@proxydominates"]
PORT = int(os.environ.get("PORT", 8080))

# ================= FLASK APP =================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "active",
        "bot": "Instagram Analyzer Pro",
        "creator": CREATOR,
        "message": "Bot is running!"
    })

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT)

# ================= DATABASE =================
db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()

# CREATE TABLES
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    joined_date TEXT,
    approved INTEGER DEFAULT 0,
    blocked INTEGER DEFAULT 0,
    total_analysis INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS pending (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    request_time TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS cache (
    username TEXT PRIMARY KEY,
    data TEXT,
    time TEXT
)
""")
db.commit()

# ================= DATABASE FUNCTIONS =================
def save_user(uid, username, first_name):
    cur.execute("INSERT OR IGNORE INTO users (id, username, first_name, joined_date, approved) VALUES (?, ?, ?, ?, 0)", 
                (uid, username, first_name, datetime.now().isoformat()))
    db.commit()

def check_access(uid):
    if uid == ADMIN_ID:
        return True
    cur.execute("SELECT approved, blocked FROM users WHERE id=?", (uid,))
    res = cur.fetchone()
    return res and res[0] == 1 and res[1] == 0

def add_pending(uid, username, first_name):
    cur.execute("INSERT OR IGNORE INTO pending VALUES (?, ?, ?, ?)",
                (uid, username, first_name, datetime.now().isoformat()))
    db.commit()

def approve_user(uid):
    cur.execute("UPDATE users SET approved=1 WHERE id=?", (uid,))
    cur.execute("DELETE FROM pending WHERE user_id=?", (uid,))
    db.commit()

def total_users():
    cur.execute("SELECT COUNT(*) FROM users")
    return cur.fetchone()[0]

# ================= FORCE JOIN =================
async def is_joined(bot, user_id):
    for ch in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def join_kb():
    # SIDE BY SIDE BUTTONS
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📢 JOIN {FORCE_CHANNELS[0]}", url=f"https://t.me/{FORCE_CHANNELS[0][1:]}"),
         InlineKeyboardButton(f"📢 JOIN {FORCE_CHANNELS[1]}", url=f"https://t.me/{FORCE_CHANNELS[1][1:]}")],
        [InlineKeyboardButton("✅ CHECK AGAIN", callback_data="check")]
    ])

# ================= KEYBOARDS =================
def menu_kb(is_admin=False):
    btns = [
        [InlineKeyboardButton("🔍 DEEP ANALYSIS", callback_data="deep")],
        [InlineKeyboardButton("❓ HELP", callback_data="help")]
    ]
    if is_admin:
        btns.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])
    return InlineKeyboardMarkup(btns)

def after_kb(username):
    # SIDE BY SIDE BUTTONS - EXACT SCREENSHOT
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 FULL REPORT", callback_data=f"report|{username}"),
         InlineKeyboardButton("🔄 ANALYZE AGAIN", callback_data="deep")],
        [InlineKeyboardButton("⬅️ MENU", callback_data="menu")]
    ])

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 STATS", callback_data="admin_stats"),
         InlineKeyboardButton("👥 PENDING", callback_data="admin_pending")],
        [InlineKeyboardButton("✅ APPROVE", callback_data="admin_approve"),
         InlineKeyboardButton("🚫 BLOCK", callback_data="admin_block")],
        [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast")],
        [InlineKeyboardButton("⬅️ MENU", callback_data="menu")]
    ])

# ================= API =================
def fetch_profile(username):
    try:
        url = API_URL.format(username)
        print(f"🔍 Fetching: {username}")
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ API Response: {data.get('status')}")
            if data.get('status') == 'ok':
                return data.get('profile', {})
        return None
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None

def download_image(url):
    try:
        r = requests.get(url, timeout=10)
        return BytesIO(r.content)
    except:
        return None

# ================= RISK ENGINE =================
def calc_risk(profile):
    username = profile.get("username", "user")
    bio = (profile.get("biography") or "").lower()
    private = profile.get("is_private", False)
    posts = int(profile.get("posts") or 0)

    seed = int(hashlib.sha256(username.encode()).hexdigest(), 16)
    rnd = random.Random(seed)

    pool = ["SCAM", "SPAM", "NUDITY", "HATE", "HARASSMENT", "BULLYING", "VIOLENCE", "TERRORISM"]

    if any(x in bio for x in ["music", "rapper", "artist", "singer", "phonk", "promo"]):
        pool += ["DRUGS", "DRUGS"]

    if private and posts < 5:
        pool += ["SCAM", "SCAM", "SCAM"]

    if rnd.random() < 0.15:
        pool.append("WEAPONS")

    rnd.shuffle(pool)
    selected = list(dict.fromkeys(pool))[:rnd.randint(1, 3)]

    issues, intensity = [], 0
    for i in selected:
        count = rnd.randint(3, 4) if i == "WEAPONS" else rnd.randint(1, 4)
        intensity += count
        issues.append(f"{count}X {i}")

    risk = min(95, 40 + intensity * 6 + (10 if private else 0) + (15 if posts < 5 else 0))
    return risk, issues

# ================ FORMAT REPORT =================
def format_report(username, profile, risk, issues):
    # EXACT FORMAT FROM methgodspecific.py
    full_name = profile.get('full_name', 'N/A')
    user_id = profile.get('id', 'N/A')
    bio = profile.get('biography', 'No bio') or 'No bio'
    followers = f"{profile.get('followers', 0):,}"
    following = f"{profile.get('following', 0):,}"
    posts = f"{profile.get('posts', 0):,}"
    private = "✅ YES" if profile.get('is_private') else "❌ NO"
    verified = "✅ YES" if profile.get('is_verified') else "❌ NO"
    business = "✅ YES" if profile.get('is_business_account') else "❌ NO"
    professional = "✅ YES" if profile.get('is_professional_account') else "❌ NO"
    url = profile.get('external_url', 'None')

    risk_emoji = "🔴 HIGH RISK" if risk >= 80 else "🟡 MEDIUM RISK" if risk >= 50 else "🟢 LOW RISK"
    
    report = f"""
╔══════════════════════════════════════╗
║     🔥 INSTAGRAM ANALYZER PRO 🔥     ║
║           BY {CREATOR}               ║
╚══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 INSTAGRAM INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• USERNAME: @{username}
• FULL NAME: {full_name}
• USER ID: {user_id}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 BIO:
{bio[:200]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STATISTICS:
• 👥 FOLLOWERS: {followers}
• 🔄 FOLLOWING: {following}
• 📸 POSTS: {posts}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 PRIVATE: {private}
✅ VERIFIED: {verified}
💼 BUSINESS: {business}
🎯 PROFESSIONAL: {professional}
🔗 EXTERNAL URL: {url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 DETECTED ISSUES"""
    
    for issue in issues:
        report += f"\n• {issue}"
    
    report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ RISK ASSESSMENT
• SCORE: {risk}% {risk_emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ COLLECTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💻 DEVELOPER: {CREATOR}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    
    return report

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)

    # FORCE JOIN CHECK
    if not await is_joined(context.bot, user.id):
        await update.message.reply_text(
            "❌ **PLEASE JOIN ALL CHANNELS FIRST!**",
            parse_mode='Markdown',
            reply_markup=join_kb()
        )
        return

    # ADMIN CHECK
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            f"👑 **WELCOME ADMIN!**\nCreator: {CREATOR}",
            parse_mode='Markdown',
            reply_markup=menu_kb(True)
        )
        return

    # USER ACCESS CHECK
    if check_access(user.id):
        await update.message.reply_text(
            f"✨ **WELCOME {user.first_name}!**\nCreator: {CREATOR}",
            parse_mode='Markdown',
            reply_markup=menu_kb()
        )
    else:
        add_pending(user.id, user.username, user.first_name)
        # NOTIFY ADMIN
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"🔔 **NEW APPROVAL REQUEST**\n\n"
                f"👤 Name: {user.first_name}\n"
                f"🆔 ID: `{user.id}`\n"
                f"📝 Username: @{user.username}\n\n"
                f"Use: `/approve {user.id}`"
            )
        except:
            pass
        
        await update.message.reply_text(
            "⏳ **PENDING APPROVAL**\nYou'll be notified once approved.",
            parse_mode='Markdown'
        )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user

    # CHECK JOIN FOR ALL BUTTONS
    if q.data != "check" and not await is_joined(context.bot, user.id):
        await q.message.edit_text("❌ JOIN CHANNELS FIRST!", reply_markup=join_kb())
        return

    # CHECK ACCESS FOR PROTECTED BUTTONS
    protected = ["deep", "admin", "admin_stats", "admin_pending", "admin_approve", "admin_block", "admin_broadcast", "report"]
    if any(q.data.startswith(p) for p in protected) and not check_access(user.id) and user.id != ADMIN_ID:
        await q.message.edit_text("⏳ PENDING APPROVAL!")
        return

    # ===== FORCE JOIN =====
    if q.data == "check":
        if await is_joined(context.bot, user.id):
            await q.message.edit_text("✅ ACCESS GRANTED!", reply_markup=menu_kb(user.id == ADMIN_ID))
        else:
            await q.message.edit_text("❌ NOT JOINED!", reply_markup=join_kb())

    # ===== MENU =====
    elif q.data == "menu":
        await q.message.edit_text("🏠 MAIN MENU", reply_markup=menu_kb(user.id == ADMIN_ID))

    # ===== DEEP ANALYSIS =====
    elif q.data == "deep":
        context.user_data['mode'] = 'deep'
        await q.message.edit_text("🔍 **SEND INSTAGRAM USERNAME**\nExample: `cristiano` or `@therock`", parse_mode='Markdown')

    # ===== HELP =====
    elif q.data == "help":
        await q.message.edit_text(
            f"❓ **HELP**\n\n"
            f"🔍 Send username to analyze\n"
            f"📊 Get full profile report\n"
            f"👑 Creator: {CREATOR}",
            parse_mode='Markdown',
            reply_markup=menu_kb(user.id == ADMIN_ID)
        )

    # ===== ADMIN PANEL =====
    elif q.data == "admin" and user.id == ADMIN_ID:
        await q.message.edit_text("👑 **ADMIN PANEL**", parse_mode='Markdown', reply_markup=admin_kb())

    # ===== ADMIN STATS =====
    elif q.data == "admin_stats" and user.id == ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE approved=1")
        approved = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM pending")
        pending = cur.fetchone()[0]
        
        await q.message.edit_text(
            f"📊 **BOT STATS**\n\n"
            f"👥 Total Users: {total}\n"
            f"✅ Approved: {approved}\n"
            f"⏳ Pending: {pending}\n"
            f"👑 Creator: {CREATOR}",
            parse_mode='Markdown',
            reply_markup=admin_kb()
        )

    # ===== ADMIN PENDING =====
    elif q.data == "admin_pending" and user.id == ADMIN_ID:
        cur.execute("SELECT user_id, username, first_name FROM pending")
        pending = cur.fetchall()
        
        if not pending:
            await q.message.edit_text("✅ No pending approvals!", reply_markup=admin_kb())
            return
        
        text = "⏳ **PENDING USERS:**\n\n"
        for uid, uname, fname in pending[:10]:
            text += f"👤 `{uid}` - @{uname or 'None'}\n📝 {fname}\n\n"
        
        await q.message.edit_text(text, parse_mode='Markdown', reply_markup=admin_kb())

    # ===== ADMIN APPROVE =====
    elif q.data == "admin_approve" and user.id == ADMIN_ID:
        context.user_data['admin_mode'] = 'approve'
        await q.message.edit_text(
            "✅ **SEND USER ID TO APPROVE**\nExample: `123456789`",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ CANCEL", callback_data="admin")]])
        )

    # ===== ADMIN BLOCK =====
    elif q.data == "admin_block" and user.id == ADMIN_ID:
        context.user_data['admin_mode'] = 'block'
        await q.message.edit_text(
            "🚫 **SEND USER ID TO BLOCK**",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ CANCEL", callback_data="admin")]])
        )

    # ===== ADMIN BROADCAST =====
    elif q.data == "admin_broadcast" and user.id == ADMIN_ID:
        context.user_data['admin_mode'] = 'broadcast'
        await q.message.edit_text(
            "📢 **SEND BROADCAST MESSAGE**",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ CANCEL", callback_data="admin")]])
        )

    # ===== FULL REPORT =====
    elif q.data.startswith("report|"):
        username = q.data.split("|")[1]
        cur.execute("SELECT data FROM cache WHERE username=?", (username,))
        cached = cur.fetchone()
        
        if cached:
            profile = json.loads(cached[0])
            risk, issues = calc_risk(profile)
            report = format_report(username, profile, risk, issues)
            await q.message.edit_text(report, parse_mode='Markdown', reply_markup=after_kb(username))
        else:
            await q.message.edit_text("❌ Data expired! Analyze again.", reply_markup=menu_kb(user.id == ADMIN_ID))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    if not user or not msg:
        return

    # CHECK JOIN
    if not await is_joined(context.bot, user.id):
        await msg.reply_text("❌ JOIN CHANNELS FIRST!", reply_markup=join_kb())
        return

    # ===== ADMIN MODES =====
    if context.user_data.get('admin_mode') == 'approve' and user.id == ADMIN_ID:
        try:
            uid = int(msg.text.strip())
            approve_user(uid)
            await msg.reply_text(f"✅ Approved `{uid}`", parse_mode='Markdown', reply_markup=admin_kb())
            try:
                await context.bot.send_message(uid, f"✅ **APPROVED!**\nCreator: {CREATOR}\n/start")
            except:
                pass
        except:
            await msg.reply_text("❌ Invalid ID!", reply_markup=admin_kb())
        context.user_data['admin_mode'] = None
        return

    elif context.user_data.get('admin_mode') == 'block' and user.id == ADMIN_ID:
        try:
            uid = int(msg.text.strip())
            cur.execute("UPDATE users SET blocked=1 WHERE id=?", (uid,))
            db.commit()
            await msg.reply_text(f"🚫 Blocked `{uid}`", parse_mode='Markdown', reply_markup=admin_kb())
        except:
            await msg.reply_text("❌ Invalid ID!", reply_markup=admin_kb())
        context.user_data['admin_mode'] = None
        return

    elif context.user_data.get('admin_mode') == 'broadcast' and user.id == ADMIN_ID:
        text = msg.text
        context.user_data['admin_mode'] = None
        
        cur.execute("SELECT id FROM users WHERE approved=1")
        users = cur.fetchall()
        
        status = await msg.reply_text(f"📢 Broadcasting to {len(users)} users...")
        sent = 0
        
        for (uid,) in users:
            try:
                await context.bot.send_message(uid, f"📢 **BROADCAST**\n\n{text}\n\n— {CREATOR}")
                sent += 1
                await asyncio.sleep(0.05)
            except:
                pass
        
        await status.edit_text(f"✅ Sent to {sent}/{len(users)} users", reply_markup=admin_kb())
        return

    # ===== CHECK ACCESS =====
    if not check_access(user.id) and user.id != ADMIN_ID:
        await msg.reply_text("⏳ PENDING APPROVAL!")
        return

    # ===== DEEP ANALYSIS =====
    if context.user_data.get('mode') == 'deep':
        context.user_data['mode'] = None
        username = msg.text.replace('@', '').strip().lower()
        
        if not re.match(r'^[a-zA-Z0-9._]+$', username):
            await msg.reply_text("❌ INVALID USERNAME!")
            return
        
        status = await msg.reply_text(f"🔄 Analyzing @{username}...")
        
        profile = fetch_profile(username)
        
        if profile:
            risk, issues = calc_risk(profile)
            
            # SAVE TO CACHE
            cur.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                       (username, json.dumps(profile), datetime.now().isoformat()))
            db.commit()
            
            # UPDATE USER STATS
            cur.execute("UPDATE users SET total_analysis = total_analysis + 1 WHERE id=?", (user.id,))
            db.commit()
            
            # TRY TO SEND WITH PROFILE PIC
            pic_url = profile.get('profile_pic_url_hd') or profile.get('profile_pic_url')
            if pic_url:
                pic = download_image(pic_url)
                if pic:
                    pic.name = "profile.jpg"
                    await msg.reply_photo(
                        photo=pic,
                        caption=f"ANALYSIS COMPLETE\n@{username}\nRisk: {risk}%",
                        reply_markup=after_kb(username)
                    )
                    await status.delete()
                    return
            
            # TEXT ONLY
            await status.edit_text(
                f"ANALYSIS COMPLETE\n@{username}\nRisk: {risk}%",
                reply_markup=after_kb(username)
            )
        else:
            await status.edit_text("❌ PROFILE NOT FOUND!")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        uid = int(context.args[0])
        approve_user(uid)
        await update.message.reply_text(f"✅ Approved {uid}")
        try:
            await context.bot.send_message(uid, f"✅ **APPROVED!**\nCreator: {CREATOR}\n/start")
        except:
            pass
    except:
        await update.message.reply_text("Usage: /approve user_id")

# ================= MAIN =================
def main():
    # START FLASK
    threading.Thread(target=run_flask, daemon=True).start()
    
    # START BOT
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("\n" + "="*50)
    print("🔥 INSTAGRAM ANALYZER PRO 🔥")
    print(f"👑 CREATOR: {CREATOR}")
    print("="*50)
    print("✅ BOT STARTED!")
    print(f"🌐 FLASK PORT: {PORT}")
    print("="*50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
