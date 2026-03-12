# ================= INSTAGRAM ANALYZER PRO =================
# DEVELOPER: @proxyfxc
# VERSION: 28.0 (RENDER + FLASK + ENV)
# ==========================================================

import requests
import json
import random
import hashlib
import sqlite3
import re
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from flask import Flask, request, jsonify
import threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import TelegramError

# ================= CONFIGURATION FROM ENV =================

# BOT CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8727219268:AAHpwzsihqTMnFldtBGl9yVlW-0h-C_Zi6U")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8689614787))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@proxyfxc")

# API CONFIG
API_URL = os.environ.get("API_URL", "https://tg-user-id-to-number-4erk.onrender.com/api/insta={}?api_key=PAID_INSTA_SELL187")
API_TIMEOUT = int(os.environ.get("API_TIMEOUT", 15))

# FORCE JOIN CHANNELS
FORCE_CHANNELS = os.environ.get("FORCE_CHANNELS", "@midnight_xaura,@proxydominates").split(",")

# DATABASE
DB_FILE = os.environ.get("DB_FILE", "users.db")

# PORT FOR FLASK
PORT = int(os.environ.get("PORT", 8080))

# ================= FLASK APP =================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return jsonify({
        "status": "active",
        "bot": "Instagram Analyzer Pro",
        "developer": ADMIN_USERNAME,
        "version": "28.0",
        "uptime": datetime.now().isoformat(),
        "endpoints": {
            "/": "Home",
            "/health": "Health check",
            "/stats": "Bot statistics"
        }
    })

@flask_app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    })

@flask_app.route('/stats')
def stats():
    try:
        cur.execute("SELECT COUNT(*) FROM USERS")
        total_users = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM USERS WHERE IS_APPROVED=1")
        approved_users = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM USERS WHERE IS_PREMIUM=1")
        premium_users = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM PENDING_APPROVALS")
        pending_users = cur.fetchone()[0]
        
        cur.execute("SELECT SUM(TOTAL_ANALYSIS) FROM USERS")
        total_analyses = cur.fetchone()[0] or 0
        
        return jsonify({
            "bot": "Instagram Analyzer Pro",
            "developer": ADMIN_USERNAME,
            "total_users": total_users,
            "approved_users": approved_users,
            "premium_users": premium_users,
            "pending_users": pending_users,
            "total_analyses": total_analyses,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

def run_flask():
    """RUN FLASK SERVER"""
    flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ================= DATABASE SETUP =================

def init_database():
    """INITIALIZE DATABASE WITH ALL TABLES"""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cur = conn.cursor()
    
    # CREATE TABLES IF NOT EXISTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS USERS (
        ID INTEGER PRIMARY KEY,
        USERNAME TEXT,
        FIRST_NAME TEXT,
        JOINED_DATE TEXT,
        IS_APPROVED INTEGER DEFAULT 0,
        IS_PREMIUM INTEGER DEFAULT 0,
        SUBSCRIPTION_END TEXT,
        TOTAL_ANALYSIS INTEGER DEFAULT 0,
        IS_BLOCKED INTEGER DEFAULT 0,
        REFERRALS INTEGER DEFAULT 0,
        REFERRED_BY INTEGER,
        PREMIUM_ACTIVATED_DATE TEXT,
        DAILY_ANALYSIS INTEGER DEFAULT 0,
        LAST_ANALYSIS_DATE TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS PENDING_APPROVALS (
        USER_ID INTEGER PRIMARY KEY,
        USERNAME TEXT,
        FIRST_NAME TEXT,
        REQUEST_TIME TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS REFERRALS (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        USER_ID INTEGER,
        REFERRED_USER_ID INTEGER,
        REFERRED_USERNAME TEXT,
        REFERRAL_DATE TEXT,
        STATUS TEXT DEFAULT 'PENDING'
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS INSTA_CACHE (
        USERNAME TEXT PRIMARY KEY,
        DATA TEXT,
        COLLECTED_TIME TEXT,
        HITS INTEGER DEFAULT 1
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS STATS (
        ID INTEGER PRIMARY KEY CHECK (ID=1),
        TOTAL_USERS INTEGER DEFAULT 0,
        TOTAL_ANALYSES INTEGER DEFAULT 0,
        TOTAL_PREMIUM INTEGER DEFAULT 0,
        TOTAL_REFERRALS INTEGER DEFAULT 0,
        LAST_RESTART TEXT,
        API_CALLS INTEGER DEFAULT 0,
        API_FAILURES INTEGER DEFAULT 0
    )
    """)
    
    # INSERT STATS IF NOT EXISTS
    cur.execute("INSERT OR IGNORE INTO STATS (ID, LAST_RESTART) VALUES (1, ?)", 
                (datetime.now().isoformat(),))
    
    conn.commit()
    print("✅ DATABASE INITIALIZED")
    return conn, cur

# INITIALIZE DATABASE
DB, CUR = init_database()

# ================= LOGGING SETUP =================

def log_error(error: str, location: str):
    """LOG ERRORS FOR DEBUGGING"""
    print(f"❌ ERROR AT {location}: {error}")
    with open("error.log", "a") as f:
        f.write(f"{datetime.now()} - {location}: {error}\n")

def log_info(message: str):
    """LOG INFO MESSAGES"""
    print(f"ℹ️ {message}")

# ================= YOUR ORIGINAL RISK ENGINE =================

def CALC_RISK(profile: Dict) -> Tuple[int, List[str]]:
    """ORIGINAL RISK CALCULATION ENGINE"""
    try:
        username = profile.get("username", "user")
        bio = (profile.get("biography") or "").lower()
        private = profile.get("is_private", False)
        posts = int(profile.get("posts") or 0)

        seed = int(hashlib.sha256(username.encode()).hexdigest(), 16)
        rnd = random.Random(seed)

        POOL = [
            "SCAM", "SPAM", "NUDITY",
            "HATE", "HARASSMENT",
            "BULLYING", "VIOLENCE",
            "TERRORISM"
        ]

        if any(x in bio for x in ["music", "rapper", "artist", "singer", "phonk", "promo"]):
            POOL += ["DRUGS", "DRUGS"]

        if private and posts < 5:
            POOL += ["SCAM", "SCAM", "SCAM"]

        INCLUDE_SELF = private and rnd.choice([True, False])
        if INCLUDE_SELF:
            POOL.append("SELF")
            POOL = [i for i in POOL if i != "HATE"]

        if rnd.random() < 0.15:
            POOL.append("WEAPONS")

        rnd.shuffle(POOL)
        SELECTED = list(dict.fromkeys(POOL))[:rnd.randint(1, 3)]

        ISSUES, INTENSITY = [], 0
        for i in SELECTED:
            COUNT = rnd.randint(3, 4) if i == "WEAPONS" else rnd.randint(1, 4)
            INTENSITY += COUNT
            ISSUES.append(f"{COUNT}X {i}")

        RISK = min(95, 40 + INTENSITY * 6 + (10 if private else 0) + (15 if posts < 5 else 0))
        return RISK, ISSUES
    except Exception as e:
        log_error(str(e), "CALC_RISK")
        return 50, ["1X ERROR"]

# ================= API FUNCTION =================

def GET_INSTAGRAM_DATA(username: str) -> Optional[Dict]:
    """FETCH INSTAGRAM DATA FROM API - FIXED TO SHOW ALL PROFILE DATA"""
    try:
        url = API_URL.format(username)
        log_info(f"FETCHING: {username}")
        
        response = requests.get(url, timeout=API_TIMEOUT)
        
        # UPDATE STATS
        CUR.execute("UPDATE STATS SET API_CALLS = API_CALLS + 1 WHERE ID=1")
        DB.commit()
        
        if response.status_code == 200:
            data = response.json()
            
            # CHECK API RESPONSE
            if data.get('status') == 'ok':
                profile = data.get('profile', {})
                if profile:
                    log_info(f"✅ PROFILE FOUND: @{username}")
                    return profile
                else:
                    log_info(f"⚠️ NO PROFILE DATA: @{username}")
            else:
                log_info(f"⚠️ API ERROR: {data.get('message', 'Unknown')}")
        else:
            log_info(f"❌ HTTP {response.status_code}: {username}")
        
        # UPDATE FAILURE STATS
        CUR.execute("UPDATE STATS SET API_FAILURES = API_FAILURES + 1 WHERE ID=1")
        DB.commit()
        
        return None
    except requests.exceptions.Timeout:
        log_error("API TIMEOUT", "GET_INSTAGRAM_DATA")
        CUR.execute("UPDATE STATS SET API_FAILURES = API_FAILURES + 1 WHERE ID=1")
        DB.commit()
        return None
    except requests.exceptions.ConnectionError:
        log_error("API CONNECTION ERROR", "GET_INSTAGRAM_DATA")
        CUR.execute("UPDATE STATS SET API_FAILURES = API_FAILURES + 1 WHERE ID=1")
        DB.commit()
        return None
    except Exception as e:
        log_error(str(e), "GET_INSTAGRAM_DATA")
        CUR.execute("UPDATE STATS SET API_FAILURES = API_FAILURES + 1 WHERE ID=1")
        DB.commit()
        return None

# ================= FORMAT REPORT - EXACT SCREENSHOT STYLE =================

def FORMAT_REPORT(username: str, profile: Dict, risk: int, issues: List[str]) -> str:
    """PROFESSIONAL REPORT WITH ALL PROFILE DATA - EXACT SCREENSHOT FORMAT"""
    try:
        # RISK LEVEL EMOJI
        if risk >= 80:
            RISK_LEVEL = "🔴 HIGH RISK"
        elif risk >= 50:
            RISK_LEVEL = "🟡 MEDIUM RISK"
        else:
            RISK_LEVEL = "🟢 LOW RISK"
        
        # FORMAT NUMBERS WITH COMMAS
        FOLLOWERS = f"{profile.get('followers', 0):,}"
        FOLLOWING = f"{profile.get('following', 0):,}"
        POSTS = f"{profile.get('posts', 0):,}"
        
        # GET ALL PROFILE DATA
        full_name = profile.get('full_name', 'N/A')
        user_id = profile.get('id', 'N/A')
        bio = profile.get('biography', 'No bio') or 'No bio'
        is_private = profile.get('is_private', False)
        is_verified = profile.get('is_verified', False)
        is_business = profile.get('is_business_account', False)
        is_professional = profile.get('is_professional_account', False)
        external_url = profile.get('external_url', 'None')
        
        # FORMAT BOOLEANS
        private_text = "✅ YES" if is_private else "❌ NO"
        verified_text = "✅ YES" if is_verified else "❌ NO"
        business_text = "✅ YES" if is_business else "❌ NO"
        professional_text = "✅ YES" if is_professional else "❌ NO"
        
        CURRENT_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # BUILD REPORT - EXACT SCREENSHOT FORMAT
        REPORT = f"""
╔══════════════════════════════════════╗
║     🔥 INSTAGRAM ANALYZER PRO 🔥     ║
║           BY {ADMIN_USERNAME}         ║
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
• 👥 FOLLOWERS: {FOLLOWERS}
• 🔄 FOLLOWING: {FOLLOWING}
• 📸 POSTS: {POSTS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 PRIVATE: {private_text}
✅ VERIFIED: {verified_text}
💼 BUSINESS: {business_text}
🎯 PROFESSIONAL: {professional_text}
🔗 EXTERNAL URL: {external_url if external_url else 'None'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 DETECTED ISSUES"""
        
        if issues:
            for issue in issues:
                REPORT += f"\n• {issue}"
        else:
            REPORT += "\n• NO ISSUES DETECTED"
        
        REPORT += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ RISK ASSESSMENT
• SCORE: {risk}% {RISK_LEVEL}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ COLLECTED: {CURRENT_TIME}
💻 DEVELOPER: {ADMIN_USERNAME}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return REPORT
    except Exception as e:
        log_error(str(e), "FORMAT_REPORT")
        return f"❌ ERROR GENERATING REPORT: {str(e)}"

# ================= DATABASE FUNCTIONS =================

def SAVE_USER(user_id: int, username: str, first_name: str):
    """SAVE USER TO DATABASE"""
    try:
        CUR.execute("""
            INSERT OR IGNORE INTO USERS 
            (ID, USERNAME, FIRST_NAME, JOINED_DATE, IS_APPROVED, IS_PREMIUM, REFERRALS, DAILY_ANALYSIS)
            VALUES (?, ?, ?, ?, 0, 0, 0, 0)
        """, (user_id, username, first_name, datetime.now().isoformat()))
        DB.commit()
    except Exception as e:
        log_error(str(e), "SAVE_USER")

def CHECK_ACCESS(user_id: int) -> Tuple[bool, str]:
    """CHECK USER ACCESS LEVEL"""
    try:
        if user_id == ADMIN_ID:
            return True, "ADMIN"
        
        CUR.execute("""
            SELECT IS_APPROVED, IS_BLOCKED, IS_PREMIUM, SUBSCRIPTION_END 
            FROM USERS WHERE ID=?
        """, (user_id,))
        RESULT = CUR.fetchone()
        
        if not RESULT:
            return False, "NOT_REGISTERED"
        
        IS_APPROVED, IS_BLOCKED, IS_PREMIUM, SUB_END = RESULT
        
        if IS_BLOCKED == 1:
            return False, "BLOCKED"
        
        if IS_APPROVED == 0:
            return False, "PENDING_APPROVAL"
        
        if IS_PREMIUM == 1 and SUB_END:
            try:
                if datetime.now() < datetime.fromisoformat(SUB_END):
                    return True, "PREMIUM"
                else:
                    CUR.execute("UPDATE USERS SET IS_PREMIUM=0 WHERE ID=?", (user_id,))
                    DB.commit()
                    return True, "APPROVED"
            except:
                pass
        
        return True, "APPROVED"
    except Exception as e:
        log_error(str(e), "CHECK_ACCESS")
        return False, "ERROR"

def ADD_PREMIUM(user_id: int, days: int) -> str:
    """ADD PREMIUM SUBSCRIPTION"""
    try:
        EXPIRY = (datetime.now() + timedelta(days=days)).isoformat()
        CUR.execute("""
            UPDATE USERS 
            SET IS_PREMIUM=1, SUBSCRIPTION_END=?, PREMIUM_ACTIVATED_DATE=?
            WHERE ID=?
        """, (EXPIRY, datetime.now().isoformat(), user_id))
        DB.commit()
        log_info(f"PREMIUM ADDED TO {user_id} FOR {days} DAYS")
        return EXPIRY
    except Exception as e:
        log_error(str(e), "ADD_PREMIUM")
        return None

def APPROVE_USER(user_id: int) -> bool:
    """APPROVE USER"""
    try:
        CUR.execute("UPDATE USERS SET IS_APPROVED=1 WHERE ID=?", (user_id,))
        CUR.execute("DELETE FROM PENDING_APPROVALS WHERE USER_ID=?", (user_id,))
        DB.commit()
        log_info(f"USER APPROVED: {user_id}")
        return True
    except Exception as e:
        log_error(str(e), "APPROVE_USER")
        return False

# ================= FORCE JOIN CHECK =================

async def CHECK_JOINED(bot, user_id: int) -> bool:
    """CHECK IF USER JOINED ALL CHANNELS"""
    try:
        for channel in FORCE_CHANNELS:
            if not channel:
                continue
            try:
                MEMBER = await bot.get_chat_member(channel.strip(), user_id)
                if MEMBER.status in ['left', 'kicked']:
                    return False
            except TelegramError:
                return False
        return True
    except Exception as e:
        log_error(str(e), "CHECK_JOINED")
        return False

def FORCE_JOIN_KEYBOARD() -> InlineKeyboardMarkup:
    """FORCE JOIN KEYBOARD"""
    BUTTONS = []
    for ch in FORCE_CHANNELS:
        if ch:
            BUTTONS.append([InlineKeyboardButton(f"📢 JOIN {ch}", url=f"https://t.me/{ch.strip()[1:]}")])
    BUTTONS.append([InlineKeyboardButton("✅ CHECK AGAIN", callback_data="CHECK")])
    return InlineKeyboardMarkup(BUTTONS)

# ================= KEYBOARDS =================

def MAIN_KEYBOARD(is_admin: bool = False) -> InlineKeyboardMarkup:
    """MAIN MENU KEYBOARD"""
    BUTTONS = [
        [InlineKeyboardButton("🔍 DEEP ANALYSIS", callback_data="DEEP")],
        [InlineKeyboardButton("📊 MY STATS", callback_data="STATS")],
        [InlineKeyboardButton("💎 PREMIUM", callback_data="PREMIUM")],
        [InlineKeyboardButton("❓ HELP", callback_data="HELP")]
    ]
    
    if is_admin:
        BUTTONS.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="ADMIN")])
    
    return InlineKeyboardMarkup(BUTTONS)

def AFTER_ANALYSIS_KEYBOARD(username: str) -> InlineKeyboardMarkup:
    """AFTER ANALYSIS KEYBOARD - EXACT SCREENSHOT"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 FULL REPORT", callback_data=f"REPORT|{username}")],
        [InlineKeyboardButton("🔄 ANALYZE AGAIN", callback_data="DEEP")],
        [InlineKeyboardButton("⬅️ MENU", callback_data="MENU")]
    ])

def ADMIN_KEYBOARD() -> InlineKeyboardMarkup:
    """ADMIN PANEL KEYBOARD"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 STATISTICS", callback_data="ADMIN_STATS")],
        [InlineKeyboardButton("👥 PENDING USERS", callback_data="ADMIN_PENDING")],
        [InlineKeyboardButton("✅ APPROVE USER", callback_data="ADMIN_APPROVE")],
        [InlineKeyboardButton("💎 ADD PREMIUM", callback_data="ADMIN_ADD_PREMIUM")],
        [InlineKeyboardButton("🚫 BLOCK USER", callback_data="ADMIN_BLOCK")],
        [InlineKeyboardButton("✅ UNBLOCK USER", callback_data="ADMIN_UNBLOCK")],
        [InlineKeyboardButton("📢 BROADCAST", callback_data="ADMIN_BROADCAST")],
        [InlineKeyboardButton("⬅️ MAIN MENU", callback_data="MENU")]
    ])

# ================= HANDLERS =================

async def START(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """START COMMAND HANDLER"""
    try:
        USER = update.effective_user
        
        # SAVE USER
        SAVE_USER(USER.id, USER.username, USER.first_name)
        
        # FORCE JOIN CHECK
        if not await CHECK_JOINED(context.bot, USER.id):
            await update.message.reply_text(
                "❌ **PLEASE JOIN ALL CHANNELS FIRST!**\n\n"
                "JOIN THE CHANNELS BELOW TO USE THIS BOT:",
                parse_mode='Markdown',
                reply_markup=FORCE_JOIN_KEYBOARD()
            )
            return
        
        # CHECK ACCESS
        ACCESS, STATUS = CHECK_ACCESS(USER.id)
        
        # PENDING APPROVAL
        if STATUS == "PENDING_APPROVAL" and USER.id != ADMIN_ID:
            CUR.execute("""
                INSERT OR REPLACE INTO PENDING_APPROVALS (USER_ID, USERNAME, FIRST_NAME, REQUEST_TIME)
                VALUES (?, ?, ?, ?)
            """, (USER.id, USER.username, USER.first_name, datetime.now().isoformat()))
            DB.commit()
            
            # NOTIFY ADMIN
            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    f"🔔 **NEW APPROVAL REQUEST!**\n\n"
                    f"👤 **NAME:** {USER.first_name}\n"
                    f"🆔 **ID:** `{USER.id}`\n"
                    f"📝 **USERNAME:** @{USER.username if USER.username else 'NONE'}\n\n"
                    f"USE `/APPROVE {USER.id}` TO APPROVE"
                )
            except:
                pass
            
            await update.message.reply_text(
                f"⏳ **REQUEST SENT TO ADMIN!**\n\n"
                f"YOU'LL BE NOTIFIED ONCE APPROVED.\n\n"
                f"— {ADMIN_USERNAME}",
                parse_mode='Markdown'
            )
            return
        
        # WELCOME MESSAGE
        WELCOME = f"""
╔════════════════════════════════╗
║    🔥 INSTAGRAM ANALYZER 🔥    ║
║         {ADMIN_USERNAME}        ║
╚════════════════════════════════╝

👋 **WELCOME {USER.first_name}!**

✅ **ACCOUNT APPROVED**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        await update.message.reply_text(
            WELCOME,
            parse_mode='Markdown',
            reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID)
        )
        
    except Exception as e:
        log_error(str(e), "START")
        await update.message.reply_text("❌ ERROR! PLEASE TRY AGAIN LATER.")

async def BUTTON_CALLBACK(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BUTTON CALLBACK HANDLER"""
    try:
        QUERY = update.callback_query
        USER = QUERY.from_user
        await QUERY.answer()
        
        # FORCE JOIN CHECK
        if QUERY.data != "CHECK":
            if not await CHECK_JOINED(context.bot, USER.id):
                await QUERY.message.edit_text(
                    "❌ PLEASE JOIN ALL CHANNELS FIRST!",
                    reply_markup=FORCE_JOIN_KEYBOARD()
                )
                return
        
        # CHECK ACCESS FOR NON-PUBLIC COMMANDS
        if QUERY.data not in ["CHECK", "PREMIUM", "HELP", "STATS"]:
            ACCESS, STATUS = CHECK_ACCESS(USER.id)
            if not ACCESS and USER.id != ADMIN_ID:
                await QUERY.message.edit_text(
                    f"⏳ YOUR REQUEST IS PENDING APPROVAL!\n\nCONTACT {ADMIN_USERNAME}",
                    parse_mode='Markdown'
                )
                return
        
        # ===== PUBLIC BUTTONS =====
        
        if QUERY.data == "CHECK":
            if await CHECK_JOINED(context.bot, USER.id):
                await QUERY.message.edit_text(
                    "✅ ACCESS GRANTED!",
                    reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID)
                )
            else:
                await QUERY.message.edit_text(
                    "❌ STILL NOT JOINED!",
                    reply_markup=FORCE_JOIN_KEYBOARD()
                )
        
        elif QUERY.data == "MENU":
            await QUERY.message.edit_text(
                "🏠 MAIN MENU",
                reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID)
            )
        
        elif QUERY.data == "DEEP":
            context.user_data['mode'] = 'DEEP'
            await QUERY.message.edit_text(
                "🔍 **SEND INSTAGRAM USERNAME**\n\nEXAMPLE: `CRISTIANO` OR `@THEROCK`",
                parse_mode='Markdown'
            )
        
        elif QUERY.data == "STATS":
            CUR.execute("SELECT TOTAL_ANALYSIS, IS_PREMIUM, SUBSCRIPTION_END, REFERRALS FROM USERS WHERE ID=?", (USER.id,))
            STATS = CUR.fetchone() or (0, 0, None, 0)
            
            PREMIUM_STATUS = "❌ INACTIVE"
            
            if STATS[1] == 1 and STATS[2]:
                try:
                    END = datetime.fromisoformat(STATS[2])
                    if datetime.now() < END:
                        PREMIUM_STATUS = f"✅ ACTIVE UNTIL {END.strftime('%d %b %Y')}"
                    else:
                        PREMIUM_STATUS = "❌ EXPIRED"
                except:
                    PREMIUM_STATUS = "❌ INACTIVE"
            elif STATS[1] == 1:
                PREMIUM_STATUS = "✅ ACTIVE (LIFETIME)"
            
            TEXT = f"""
╔════════════════════════════════╗
║        📊 YOUR STATS           ║
║         {ADMIN_USERNAME}        ║
╚════════════════════════════════╝

🆔 **USER ID:** `{USER.id}`
📈 **TOTAL ANALYSES:** {STATS[0]}
💎 **PREMIUM:** {PREMIUM_STATUS}
👥 **REFERRALS:** {STATS[3]}
"""
            await QUERY.message.edit_text(
                TEXT,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ BACK", callback_data="MENU")
                ]])
            )
        
        elif QUERY.data == "PREMIUM":
            TEXT = f"""
╔════════════════════════════════╗
║      💎 PREMIUM MEMBERSHIP     ║
║         {ADMIN_USERNAME}        ║
╚════════════════════════════════╝

✨ **PREMIUM BENEFITS:**
• UNLIMITED ANALYSES
• PRIORITY PROCESSING
• NO DAILY LIMITS

💰 **PRICING:**
• 1 DAY  - ₹10
• 7 DAYS - ₹50
• 30 DAYS - ₹150

📲 **CONTACT:** {ADMIN_USERNAME}
"""
            await QUERY.message.edit_text(
                TEXT,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ BACK", callback_data="MENU")
                ]])
            )
        
        elif QUERY.data == "HELP":
            TEXT = f"""
╔════════════════════════════════╗
║           ❓ HELP              ║
║         {ADMIN_USERNAME}        ║
╚════════════════════════════════╝

🔍 **DEEP ANALYSIS**
• SEND ANY INSTAGRAM USERNAME
• GET COMPLETE PROFILE INFO
• RISK ANALYSIS INCLUDED

📊 **MY STATS**
• CHECK YOUR USAGE
• PREMIUM STATUS

💎 **PREMIUM**
• BUY SUBSCRIPTION
• CONTACT ADMIN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOR SUPPORT: {ADMIN_USERNAME}
"""
            await QUERY.message.edit_text(
                TEXT,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ BACK", callback_data="MENU")
                ]])
            )
        
        elif QUERY.data.startswith("REPORT|"):
            USERNAME = QUERY.data.split("|")[1]
            CUR.execute("SELECT DATA FROM INSTA_CACHE WHERE USERNAME=?", (USERNAME,))
            CACHED = CUR.fetchone()
            
            if CACHED:
                PROFILE = json.loads(CACHED[0])
                RISK, ISSUES = CALC_RISK(PROFILE)
                REPORT = FORMAT_REPORT(USERNAME, PROFILE, RISK, ISSUES)
                
                await QUERY.message.edit_text(
                    REPORT,
                    parse_mode='Markdown',
                    reply_markup=AFTER_ANALYSIS_KEYBOARD(USERNAME)
                )
            else:
                await QUERY.message.edit_text(
                    "❌ PROFILE DATA EXPIRED! PLEASE ANALYZE AGAIN.",
                    reply_markup=MAIN_KEYBOARD(USER.id == ADMIN_ID)
                )
        
        # ===== ADMIN BUTTONS =====
        
        elif QUERY.data == "ADMIN" and USER.id == ADMIN_ID:
            await QUERY.message.edit_text(
                "👑 **ADMIN PANEL**\n\nSELECT AN OPTION:",
                parse_mode='Markdown',
                reply_markup=ADMIN_KEYBOARD()
            )
        
        elif QUERY.data == "ADMIN_STATS" and USER.id == ADMIN_ID:
            CUR.execute("SELECT COUNT(*) FROM USERS")
            TOTAL = CUR.fetchone()[0]
            CUR.execute("SELECT COUNT(*) FROM USERS WHERE IS_PREMIUM=1")
            PREMIUM = CUR.fetchone()[0]
            CUR.execute("SELECT COUNT(*) FROM USERS WHERE IS_APPROVED=1")
            APPROVED = CUR.fetchone()[0]
            CUR.execute("SELECT COUNT(*) FROM PENDING_APPROVALS")
            PENDING = CUR.fetchone()[0]
            CUR.execute("SELECT SUM(TOTAL_ANALYSIS) FROM USERS")
            ANALYSES = CUR.fetchone()[0] or 0
            CUR.execute("SELECT API_CALLS, API_FAILURES FROM STATS WHERE ID=1")
            API_STATS = CUR.fetchone() or (0, 0)
            
            TEXT = f"""
╔════════════════════════════════╗
║       📊 BOT STATISTICS        ║
║         {ADMIN_USERNAME}        ║
╚════════════════════════════════╝

👥 **TOTAL USERS:** {TOTAL}
✅ **APPROVED:** {APPROVED}
⏳ **PENDING:** {PENDING}
💎 **PREMIUM:** {PREMIUM}
📊 **ANALYSES:** {ANALYSES}
📡 **API CALLS:** {API_STATS[0]}
❌ **API FAILURES:** {API_STATS[1]}

🤖 **STATUS:** 🟢 ONLINE
"""
            await QUERY.message.edit_text(TEXT, parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
        
        elif QUERY.data == "ADMIN_PENDING" and USER.id == ADMIN_ID:
            CUR.execute("SELECT USER_ID, USERNAME, FIRST_NAME FROM PENDING_APPROVALS")
            PENDING = CUR.fetchall()
            
            if not PENDING:
                await QUERY.message.edit_text("✅ NO PENDING APPROVALS!", reply_markup=ADMIN_KEYBOARD())
                return
            
            TEXT = "⏳ **PENDING APPROVALS:**\n\n"
            for UID, UNAME, FNAME in PENDING[:10]:
                TEXT += f"👤 `{UID}` - @{UNAME or 'NONE'}\n   📝 {FNAME}\n\n"
            
            TEXT += "USE `/APPROVE USER_ID` TO APPROVE"
            
            await QUERY.message.edit_text(TEXT, parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
        
        elif QUERY.data == "ADMIN_APPROVE" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'APPROVE'
            await QUERY.message.edit_text(
                "✅ **SEND USER ID TO APPROVE:**\n\nEXAMPLE: `123456789`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="ADMIN")
                ]])
            )
        
        elif QUERY.data == "ADMIN_ADD_PREMIUM" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'ADD_PREMIUM'
            await QUERY.message.edit_text(
                "💎 **ADD PREMIUM MEMBERSHIP**\n\nFORMAT: `USER_ID DAYS`\nEXAMPLE: `123456789 30`",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="ADMIN")
                ]])
            )
        
        elif QUERY.data == "ADMIN_BLOCK" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'BLOCK'
            await QUERY.message.edit_text(
                "🚫 **SEND USER ID TO BLOCK:**",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="ADMIN")
                ]])
            )
        
        elif QUERY.data == "ADMIN_UNBLOCK" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'UNBLOCK'
            await QUERY.message.edit_text(
                "✅ **SEND USER ID TO UNBLOCK:**",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="ADMIN")
                ]])
            )
        
        elif QUERY.data == "ADMIN_BROADCAST" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'BROADCAST'
            await QUERY.message.edit_text(
                "📢 **SEND BROADCAST MESSAGE:**\n\nTHIS WILL BE SENT TO ALL USERS.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="ADMIN")
                ]])
            )
    
    except Exception as e:
        log_error(str(e), "BUTTON_CALLBACK")
        try:
            await QUERY.message.edit_text("❌ ERROR! PLEASE TRY AGAIN.")
        except:
            pass

async def HANDLE_MESSAGES(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MESSAGE HANDLER"""
    try:
        USER = update.effective_user
        MSG = update.message
        
        if not USER or not MSG:
            return
        
        # FORCE JOIN CHECK
        if not await CHECK_JOINED(context.bot, USER.id):
            await MSG.reply_text("❌ JOIN CHANNELS FIRST!", reply_markup=FORCE_JOIN_KEYBOARD())
            return
        
        # CHECK ACCESS
        ACCESS, STATUS = CHECK_ACCESS(USER.id)
        if not ACCESS and USER.id != ADMIN_ID:
            await MSG.reply_text(f"⏳ PENDING APPROVAL!\nCONTACT {ADMIN_USERNAME}")
            return
        
        # ===== ADMIN COMMANDS =====
        
        if context.user_data.get('admin_mode') == 'APPROVE' and USER.id == ADMIN_ID:
            try:
                TARGET_ID = int(MSG.text.strip())
                
                if APPROVE_USER(TARGET_ID):
                    await MSG.reply_text(
                        f"✅ **USER APPROVED!**\n\n`{TARGET_ID}` CAN NOW USE THE BOT.",
                        parse_mode='Markdown',
                        reply_markup=ADMIN_KEYBOARD()
                    )
                    
                    try:
                        await context.bot.send_message(
                            TARGET_ID,
                            f"✅ **APPROVED!**\n\nYOU CAN NOW USE THE INSTAGRAM ANALYZER BOT.\n\nTYPE /START TO BEGIN!\n\n— {ADMIN_USERNAME}"
                        )
                    except:
                        pass
                else:
                    await MSG.reply_text("❌ ERROR APPROVING USER!", reply_markup=ADMIN_KEYBOARD())
                
            except Exception as e:
                await MSG.reply_text(f"❌ ERROR: {str(e)}", reply_markup=ADMIN_KEYBOARD())
            
            context.user_data['admin_mode'] = None
            return
        
        elif context.user_data.get('admin_mode') == 'ADD_PREMIUM' and USER.id == ADMIN_ID:
            try:
                PARTS = MSG.text.split()
                TARGET_ID = int(PARTS[0])
                DAYS = int(PARTS[1])
                
                EXPIRY = ADD_PREMIUM(TARGET_ID, DAYS)
                
                if EXPIRY:
                    EXPIRY_DATE = datetime.fromisoformat(EXPIRY).strftime('%d %b %Y')
                    
                    await MSG.reply_text(
                        f"✅ **PREMIUM ADDED!**\n\n"
                        f"👤 USER: `{TARGET_ID}`\n"
                        f"📅 DAYS: {DAYS}\n"
                        f"⏰ EXPIRES: {EXPIRY_DATE}",
                        parse_mode='Markdown',
                        reply_markup=ADMIN_KEYBOARD()
                    )
                    
                    try:
                        await context.bot.send_message(
                            TARGET_ID,
                            f"🎉 **PREMIUM ACTIVATED!**\n\n"
                            f"YOUR PREMIUM MEMBERSHIP IS NOW ACTIVE FOR {DAYS} DAYS.\n\n"
                            f"📅 EXPIRES: {EXPIRY_DATE}\n\n"
                            f"THANK YOU FOR YOUR SUPPORT! 🙏\n\n— {ADMIN_USERNAME}"
                        )
                    except:
                        pass
                else:
                    await MSG.reply_text("❌ ERROR ADDING PREMIUM!", reply_markup=ADMIN_KEYBOARD())
                
            except Exception as e:
                await MSG.reply_text(f"❌ ERROR: {str(e)}", reply_markup=ADMIN_KEYBOARD())
            
            context.user_data['admin_mode'] = None
            return
        
        elif context.user_data.get('admin_mode') == 'BLOCK' and USER.id == ADMIN_ID:
            try:
                TARGET_ID = int(MSG.text.strip())
                
                CUR.execute("UPDATE USERS SET IS_BLOCKED=1 WHERE ID=?", (TARGET_ID,))
                DB.commit()
                await MSG.reply_text(f"✅ **USER BLOCKED!**\n\n`{TARGET_ID}`", parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
                
            except Exception as e:
                await MSG.reply_text(f"❌ ERROR: {str(e)}", reply_markup=ADMIN_KEYBOARD())
            
            context.user_data['admin_mode'] = None
            return
        
        elif context.user_data.get('admin_mode') == 'UNBLOCK' and USER.id == ADMIN_ID:
            try:
                TARGET_ID = int(MSG.text.strip())
                
                CUR.execute("UPDATE USERS SET IS_BLOCKED=0 WHERE ID=?", (TARGET_ID,))
                DB.commit()
                await MSG.reply_text(f"✅ **USER UNBLOCKED!**\n\n`{TARGET_ID}`", parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
                
            except Exception as e:
                await MSG.reply_text(f"❌ ERROR: {str(e)}", reply_markup=ADMIN_KEYBOARD())
            
            context.user_data['admin_mode'] = None
            return
        
        elif context.user_data.get('admin_mode') == 'BROADCAST' and USER.id == ADMIN_ID:
            TEXT = MSG.text
            context.user_data['admin_mode'] = None
            
            STATUS_MSG = await MSG.reply_text("📢 **BROADCASTING...**")
            
            CUR.execute("SELECT ID FROM USERS")
            USERS = CUR.fetchall()
            SENT = 0
            FAILED = 0
            
            BROADCAST_TEXT = f"📢 **ADMIN BROADCAST**\n\n{TEXT}\n\n— {ADMIN_USERNAME}"
            
            for (UID,) in USERS:
                try:
                    await context.bot.send_message(UID, BROADCAST_TEXT)
                    SENT += 1
                    await asyncio.sleep(0.05)
                except:
                    FAILED += 1
            
            await STATUS_MSG.edit_text(
                f"✅ **BROADCAST COMPLETE!**\n\n"
                f"📊 SENT: {SENT}\n"
                f"❌ FAILED: {FAILED}",
                reply_markup=ADMIN_KEYBOARD()
            )
            return
        
        # ===== DEEP ANALYSIS =====
        
        if context.user_data.get('mode') == 'DEEP':
            context.user_data['mode'] = None
            USERNAME = MSG.text.replace('@', '').strip().lower()
            
            if not USERNAME or not re.match(r'^[a-zA-Z0-9._]+$', USERNAME):
                await MSG.reply_text("❌ SEND A VALID USERNAME!")
                return
            
            # LOADING MESSAGE
            STATUS_MSG = await MSG.reply_text(f"🔍 ANALYZING @{USERNAME.upper()}...")
            
            # FETCH DATA
            PROFILE = GET_INSTAGRAM_DATA(USERNAME)
            
            if PROFILE:
                # CALCULATE RISK
                RISK, ISSUES = CALC_RISK(PROFILE)
                
                # FORMAT REPORT
                REPORT = FORMAT_REPORT(USERNAME, PROFILE, RISK, ISSUES)
                
                # SAVE TO CACHE
                CUR.execute("""
                    INSERT OR REPLACE INTO INSTA_CACHE (USERNAME, DATA, COLLECTED_TIME)
                    VALUES (?, ?, ?)
                """, (USERNAME, json.dumps(PROFILE), datetime.now().isoformat()))
                DB.commit()
                
                # DELETE LOADING MESSAGE
                await STATUS_MSG.delete()
                
                # SEND INITIAL RESULT (LIKE SCREENSHOT)
                await MSG.reply_text(
                    f"ANALYSIS COMPLETE\n@{USERNAME}\nRisk: {RISK}%",
                    reply_markup=AFTER_ANALYSIS_KEYBOARD(USERNAME)
                )
                
                # UPDATE STATS
                CUR.execute("UPDATE USERS SET TOTAL_ANALYSIS = TOTAL_ANALYSIS + 1 WHERE ID=?", (USER.id,))
                CUR.execute("UPDATE STATS SET TOTAL_ANALYSES = TOTAL_ANALYSES + 1 WHERE ID=1")
                DB.commit()
            else:
                await STATUS_MSG.edit_text("❌ PROFILE NOT FOUND OR API ERROR")
    
    except Exception as e:
        log_error(str(e), "HANDLE_MESSAGES")
        try:
            await update.message.reply_text("❌ ERROR! PLEASE TRY AGAIN LATER.")
        except:
            pass

async def APPROVE_COMMAND(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """APPROVE COMMAND HANDLER"""
    try:
        USER = update.effective_user
        
        if USER.id != ADMIN_ID:
            await update.message.reply_text("❌ YOU ARE NOT AUTHORIZED!")
            return
        
        if not context.args:
            await update.message.reply_text("USAGE: /APPROVE USER_ID")
            return
        
        TARGET_ID = int(context.args[0])
        
        if APPROVE_USER(TARGET_ID):
            await update.message.reply_text(
                f"✅ **USER APPROVED!**\n\n`{TARGET_ID}` CAN NOW USE THE BOT.",
                parse_mode='Markdown'
            )
            
            try:
                await context.bot.send_message(
                    TARGET_ID,
                    f"✅ **APPROVED!**\n\nYOU CAN NOW USE THE INSTAGRAM ANALYZER BOT.\n\nTYPE /START TO BEGIN!\n\n— {ADMIN_USERNAME}"
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ ERROR APPROVING USER!")
            
    except Exception as e:
        log_error(str(e), "APPROVE_COMMAND")
        await update.message.reply_text(f"❌ ERROR: {str(e)}")

# ================= ERROR HANDLER =================

async def ERROR_HANDLER(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """GLOBAL ERROR HANDLER"""
    try:
        raise context.error
    except Exception as e:
        log_error(str(e), "GLOBAL_ERROR_HANDLER")

# ================= MAIN FUNCTION =================

def main():
    """MAIN BOT FUNCTION"""
    try:
        # START FLASK IN BACKGROUND
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        log_info(f"🌐 FLASK RUNNING ON PORT {PORT}")
        
        print("\n" + "="*50)
        print("╔════════════════════════════════╗")
        print("║    INSTAGRAM ANALYZER PRO     ║")
        print(f"║         {ADMIN_USERNAME}         ║")
        print("╚════════════════════════════════╝")
        print("="*50)
        print(f"✅ DATABASE: {DB_FILE}")
        print(f"✅ BOT TOKEN: {BOT_TOKEN[:10]}...")
        print(f"✅ ADMIN ID: {ADMIN_ID}")
        print(f"✅ FORCE CHANNELS: {FORCE_CHANNELS}")
        print(f"✅ FLASK PORT: {PORT}")
        print("="*50)
        
        # CREATE APPLICATION
        APP = Application.builder().token(BOT_TOKEN).build()
        
        # ADD HANDLERS
        APP.add_handler(CommandHandler("start", START))
        APP.add_handler(CommandHandler("approve", APPROVE_COMMAND))
        APP.add_handler(CallbackQueryHandler(BUTTON_CALLBACK))
        APP.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, HANDLE_MESSAGES))
        APP.add_error_handler(ERROR_HANDLER)
        
        # UPDATE STATS
        CUR.execute("UPDATE STATS SET LAST_RESTART=? WHERE ID=1", (datetime.now().isoformat(),))
        DB.commit()
        
        print("✅ BOT IS RUNNING!")
        print("="*50)
        
        # START BOT
        APP.run_polling()
        
    except KeyboardInterrupt:
        print("\n❌ BOT STOPPED BY USER")
    except Exception as e:
        log_error(str(e), "MAIN")
        print(f"❌ FATAL ERROR: {e}")
    finally:
        DB.close()

if __name__ == "__main__":
    main()
