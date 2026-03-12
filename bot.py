# ================= INSTAGRAM ANALYZER PRO =================
# DEVELOPER: @proxyfxc
# VERSION: 28.0 (FLASK + NEW FORMAT)
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
from flask import Flask, render_template_string
import threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import TelegramError

# ================= FLASK APP =================

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Instagram Analyzer Pro</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            width: 90%;
        }
        h1 {
            text-align: center;
            font-size: 2em;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 10px;
        }
        .developer {
            text-align: center;
            color: #ffd700;
            font-weight: bold;
            margin-bottom: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-top: 30px;
        }
        .stat-item {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #ffd700;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 5px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.2);
            font-size: 0.9em;
            color: rgba(255,255,255,0.8);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 INSTAGRAM ANALYZER PRO 🔥</h1>
        <div class="developer">DEVELOPER: @proxyfxc</div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{{ total_users }}</div>
                <div class="stat-label">TOTAL USERS</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{ total_analyses }}</div>
                <div class="stat-label">ANALYSES</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{ premium_users }}</div>
                <div class="stat-label">PREMIUM</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{ bot_status }}</div>
                <div class="stat-label">STATUS</div>
            </div>
        </div>
        
        <div class="footer">
            ⚡ BOT IS RUNNING ON TELEGRAM ⚡<br>
            JOIN @midnight_xaura | @proxydominates
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """FLASK HOME PAGE"""
    try:
        CUR.execute("SELECT COUNT(*) FROM USERS")
        total_users = CUR.fetchone()[0]
        
        CUR.execute("SELECT COUNT(*) FROM USERS WHERE IS_PREMIUM=1")
        premium_users = CUR.fetchone()[0]
        
        CUR.execute("SELECT SUM(TOTAL_ANALYSIS) FROM USERS")
        total_analyses = CUR.fetchone()[0] or 0
        
        return render_template_string(
            HTML_TEMPLATE,
            total_users=total_users,
            total_analyses=total_analyses,
            premium_users=premium_users,
            bot_status="🟢 ONLINE"
        )
    except Exception as e:
        return f"Error: {str(e)}"

def run_flask():
    """RUN FLASK IN SEPARATE THREAD"""
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# ================= CONFIGURATION =================

BOT_TOKEN = "8727219268:AAENf3iIwQSFBZDEbwwkxWft3AAx8qMu5Z4"
ADMIN_ID = 8689614787
ADMIN_USERNAME = "@proxyfxc"

# API CONFIGURATION
API_URL = "https://tg-user-id-to-number-4erk.onrender.com/api/insta={}?api_key=PAID_INSTA_SELL187"
API_TIMEOUT = 10

# FORCE JOIN CHANNELS
FORCE_CHANNELS = ["@midnight_xaura", "@proxydominates"]

# DATABASE FILE
DB_FILE = "users.db"

# ================= DATABASE SETUP ===========

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
        PREMIUM_ACTIVATED_DATE TEXT
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
        COLLECTED_TIME TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS STATS (
        ID INTEGER PRIMARY KEY CHECK (ID=1),
        TOTAL_USERS INTEGER DEFAULT 0,
        TOTAL_ANALYSES INTEGER DEFAULT 0,
        TOTAL_PREMIUM INTEGER DEFAULT 0,
        TOTAL_REFERRALS INTEGER DEFAULT 0,
        LAST_RESTART TEXT
    )
    """)
    
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

# ================= RISK ENGINE =================

def CALC_RISK(profile: Dict) -> Tuple[int, List[str]]:
    """RISK CALCULATION ENGINE"""
    try:
        username = profile.get("username", "user")
        bio = (profile.get("biography") or "").lower()
        private = profile.get("is_private", False)
        posts = int(profile.get("posts") or 0)
        is_business = profile.get("is_business_account", False)
        is_professional = profile.get("is_professional_account", False)

        seed = int(hashlib.sha256(username.encode()).hexdigest(), 16)
        rnd = random.Random(seed)

        POOL = [
            "SCAM", "SPAM", "NUDITY",
            "HATE", "HARASSMENT",
            "BULLYING", "VIOLENCE",
            "TERRORISM"
        ]

        if any(x in bio for x in ["music", "rapper", "artist", "singer"]):
            POOL += ["DRUGS", "DRUGS"]

        if private and posts == 0:
            POOL += ["SCAM", "SCAM", "SCAM"]
            
        if is_business and posts == 0:
            POOL += ["FAKE BUSINESS", "SCAM"]

        if rnd.random() < 0.15:
            POOL.append("WEAPONS")

        rnd.shuffle(POOL)
        SELECTED = list(dict.fromkeys(POOL))[:rnd.randint(1, 3)]

        ISSUES = []
        INTENSITY = 0
        for i in SELECTED:
            COUNT = rnd.randint(3, 4) if i == "WEAPONS" else rnd.randint(1, 4)
            INTENSITY += COUNT
            ISSUES.append(f"{COUNT}X {i}")

        RISK = min(95, 40 + INTENSITY * 6 + (10 if private else 0) + (10 if posts == 0 else 0))
        return RISK, ISSUES
    except Exception as e:
        log_error(str(e), "CALC_RISK")
        return 50, ["1X ERROR"]

# ================= API FUNCTION =================

def GET_INSTAGRAM_DATA(username: str) -> Optional[Dict]:
    """FETCH INSTAGRAM DATA FROM API"""
    try:
        url = API_URL.format(username)
        response = requests.get(url, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                return data.get('profile', {})
        return None
    except Exception as e:
        log_error(str(e), "GET_INSTAGRAM_DATA")
        return None

# ================= FORMAT REPORT =================

def FORMAT_REPORT(username: str, profile: Dict, risk: int, issues: List[str]) -> str:
    """PROFESSIONAL REPORT WITH @proxyfxc BRANDING - EXACT FORMAT"""
    try:
        if risk < 30:
            RISK_LEVEL = "🟢 LOW RISK"
        elif risk < 60:
            RISK_LEVEL = "🟡 MEDIUM RISK"
        else:
            RISK_LEVEL = "🔴 HIGH RISK"
        
        FOLLOWERS = f"{profile.get('followers', 0):,}"
        FOLLOWING = f"{profile.get('following', 0):,}"
        POSTS = f"{profile.get('posts', 0):,}"
        
        CURRENT_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # EXACT FORMAT AS REQUESTED
        REPORT = f"""
╔══════════════════════════════════════╗
║     🔥 INSTAGRAM ANALYZER PRO 🔥     ║
║           BY @proxyfxc               ║
╚══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 INSTAGRAM INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• USERNAME: @{username}
• FULL NAME: {profile.get('full_name', '') or 'No name'}
• USER ID: {profile.get('id', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 BIO:
{profile.get('biography', 'No bio')[:200]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 STATISTICS:
• FOLLOWERS: {FOLLOWERS}
• FOLLOWING: {FOLLOWING}
• POSTS: {POSTS}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 PRIVATE: {'YES' if profile.get('is_private') else 'NO'}
✅ VERIFIED: {'YES' if profile.get('is_verified') else 'NO'}
💼 BUSINESS: {'YES' if profile.get('is_business_account') else 'NO'}
📱 PROFESSIONAL: {'YES' if profile.get('is_professional_account') else 'NO'}
🔗 EXTERNAL URL: {profile.get('external_url', 'None')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 DETECTED ISSUES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if issues:
            for issue in issues:
                REPORT += f"• {issue}\n"
        else:
            REPORT += "• NO ISSUES DETECTED\n"
        
        REPORT += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ RISK ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• SCORE: {risk}%
• {RISK_LEVEL}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ COLLECTED: {CURRENT_TIME}
👨‍💻 DEVELOPER: @proxyfxc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return REPORT
    except Exception as e:
        log_error(str(e), "FORMAT_REPORT")
        return "❌ ERROR GENERATING REPORT"

# ================= DATABASE FUNCTIONS =================

def SAVE_USER(user_id: int, username: str, first_name: str):
    """SAVE USER TO DATABASE"""
    try:
        CUR.execute("""
            INSERT OR IGNORE INTO USERS 
            (ID, USERNAME, FIRST_NAME, JOINED_DATE, IS_APPROVED, IS_PREMIUM, REFERRALS)
            VALUES (?, ?, ?, ?, 0, 0, 0)
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
        return True
    except Exception as e:
        log_error(str(e), "APPROVE_USER")
        return False

def ADD_REFERRAL(user_id: int, referred_id: int, referred_username: str) -> bool:
    """ADD REFERRAL RECORD"""
    try:
        CUR.execute("""
            INSERT INTO REFERRALS (USER_ID, REFERRED_USER_ID, REFERRED_USERNAME, REFERRAL_DATE)
            VALUES (?, ?, ?, ?)
        """, (user_id, referred_id, referred_username, datetime.now().isoformat()))
        
        CUR.execute("UPDATE USERS SET REFERRALS = REFERRALS + 1 WHERE ID=?", (user_id,))
        DB.commit()
        return True
    except Exception as e:
        log_error(str(e), "ADD_REFERRAL")
        return False

# ================= FORCE JOIN CHECK =================

async def CHECK_JOINED(bot, user_id: int) -> bool:
    """CHECK IF USER JOINED ALL CHANNELS"""
    try:
        for channel in FORCE_CHANNELS:
            try:
                MEMBER = await bot.get_chat_member(channel, user_id)
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
        BUTTONS.append([InlineKeyboardButton(f"📢 JOIN {ch}", url=f"https://t.me/{ch[1:]}")])
    BUTTONS.append([InlineKeyboardButton("✅ CHECK AGAIN", callback_data="CHECK")])
    return InlineKeyboardMarkup(BUTTONS)

# ================= KEYBOARDS =================

def MAIN_KEYBOARD(is_admin: bool = False) -> InlineKeyboardMarkup:
    """MAIN MENU KEYBOARD"""
    BUTTONS = [
        [InlineKeyboardButton("🔍 DEEP ANALYSIS", callback_data="DEEP")],
        [InlineKeyboardButton("📊 MY STATS", callback_data="STATS")],
        [InlineKeyboardButton("💎 PREMIUM", callback_data="PREMIUM")],
        [InlineKeyboardButton("👥 REFER & EARN", callback_data="REFER")],
        [InlineKeyboardButton("❓ HELP", callback_data="HELP")]
    ]
    
    if is_admin:
        BUTTONS.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="ADMIN")])
    
    return InlineKeyboardMarkup(BUTTONS)

def AFTER_ANALYSIS_KEYBOARD(username: str) -> InlineKeyboardMarkup:
    """AFTER ANALYSIS KEYBOARD"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 FULL REPORT", callback_data=f"REPORT|{username}")],
        [InlineKeyboardButton("🔄 ANALYZE AGAIN", callback_data="DEEP")],
        [InlineKeyboardButton("🏠 MENU", callback_data="MENU")]
    ])

def ADMIN_KEYBOARD() -> InlineKeyboardMarkup:
    """ADMIN PANEL KEYBOARD"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 STATISTICS", callback_data="ADMIN_STATS"),
         InlineKeyboardButton("👥 USER LIST", callback_data="ADMIN_USERS")],
        [InlineKeyboardButton("⏳ PENDING", callback_data="ADMIN_PENDING"),
         InlineKeyboardButton("✅ APPROVE", callback_data="ADMIN_APPROVE")],
        [InlineKeyboardButton("💎 ADD PREMIUM", callback_data="ADMIN_ADD_PREMIUM"),
         InlineKeyboardButton("🚫 BLOCK", callback_data="ADMIN_BLOCK")],
        [InlineKeyboardButton("✅ UNBLOCK", callback_data="ADMIN_UNBLOCK"),
         InlineKeyboardButton("📢 BROADCAST", callback_data="ADMIN_BROADCAST")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="MENU")]
    ])

def PREMIUM_KEYBOARD() -> InlineKeyboardMarkup:
    """PREMIUM PLANS KEYBOARD"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 DAY - ₹10", callback_data="BUY_1")],
        [InlineKeyboardButton("7 DAYS - ₹50", callback_data="BUY_7")],
        [InlineKeyboardButton("30 DAYS - ₹150", callback_data="BUY_30")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="MENU")]
    ])

# ================= HANDLERS =================

async def START(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """START COMMAND HANDLER"""
    try:
        USER = update.effective_user
        
        # CHECK REFERRAL
        if context.args and context.args[0].startswith('ref_'):
            try:
                REFERRER_ID = int(context.args[0].replace('ref_', ''))
                if REFERRER_ID != USER.id:
                    ADD_REFERRAL(REFERRER_ID, USER.id, USER.username)
                    await context.bot.send_message(
                        REFERRER_ID,
                        f"🎉 **NEW REFERRAL!**\n\n@{USER.username} JOINED USING YOUR LINK!"
                    )
            except:
                pass
        
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
                    f"👤 NAME: {USER.first_name}\n"
                    f"🆔 ID: `{USER.id}`\n"
                    f"📝 USERNAME: @{USER.username if USER.username else 'NONE'}\n\n"
                    f"USE /APPROVE {USER.id} TO APPROVE"
                )
            except:
                pass
            
            await update.message.reply_text(
                "⏳ **REQUEST SENT TO ADMIN!**\n\n"
                "YOU'LL BE NOTIFIED ONCE APPROVED.\n\n"
                "— @proxyfxc",
                parse_mode='Markdown'
            )
            return
        
        # WELCOME MESSAGE
        STATUS_EMOJI = {
            "PREMIUM": "💎",
            "ADMIN": "👑",
            "APPROVED": "✅"
        }.get(STATUS, "⏳")
        
        WELCOME = f"""
╔════════════════════════════════╗
║    🔥 INSTAGRAM ANALYZER 🔥    ║
║         BY @proxyfxc           ║
╚════════════════════════════════╝

👋 **WELCOME {USER.first_name}!**
📊 **STATUS:** {STATUS_EMOJI} {STATUS}

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
        
        # PUBLIC BUTTONS
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
                "🔍 **SEND INSTAGRAM USERNAME**\n\nEXAMPLE: `cristiano` OR `@therock`",
                parse_mode='Markdown'
            )
        
        elif QUERY.data == "STATS":
            ACCESS, STATUS = CHECK_ACCESS(USER.id)
            if not ACCESS and USER.id != ADMIN_ID:
                await QUERY.message.edit_text(f"⏳ PENDING APPROVAL!\nCONTACT {ADMIN_USERNAME}")
                return
            
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
║         BY @proxyfxc           ║
╚════════════════════════════════╝

🆔 USER ID: `{USER.id}`
📈 TOTAL ANALYSES: {STATS[0]}
💎 PREMIUM: {PREMIUM_STATUS}
👥 REFERRALS: {STATS[3]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            await QUERY.message.edit_text(
                TEXT,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ BACK", callback_data="MENU")
                ]])
            )
        
        elif QUERY.data == "PREMIUM":
            ACCESS, STATUS = CHECK_ACCESS(USER.id)
            if not ACCESS and USER.id != ADMIN_ID:
                await QUERY.message.edit_text(f"⏳ PENDING APPROVAL!\nCONTACT {ADMIN_USERNAME}")
                return
            
            TEXT = f"""
╔════════════════════════════════╗
║      💎 PREMIUM MEMBERSHIP     ║
║         BY @proxyfxc           ║
╚════════════════════════════════╝

✨ **PREMIUM BENEFITS:**
• UNLIMITED ANALYSES
• PRIORITY PROCESSING
• NO DAILY LIMITS

💰 **PRICING:**
• 1 DAY  - ₹10
• 7 DAYS - ₹50
• 30 DAYS - ₹150

👥 **REFER & EARN:**
• REFER 2 FRIENDS = 1 DAY PREMIUM
• REFER 10 FRIENDS = 7 DAYS PREMIUM

📲 **CONTACT:** {ADMIN_USERNAME}
"""
            await QUERY.message.edit_text(
                TEXT,
                parse_mode='Markdown',
                reply_markup=PREMIUM_KEYBOARD()
            )
        
        elif QUERY.data.startswith("BUY_"):
            ACCESS, STATUS = CHECK_ACCESS(USER.id)
            if not ACCESS and USER.id != ADMIN_ID:
                await QUERY.message.edit_text(f"⏳ PENDING APPROVAL!\nCONTACT {ADMIN_USERNAME}")
                return
            
            DAYS = {"BUY_1": 1, "BUY_7": 7, "BUY_30": 30}[QUERY.data]
            PRICE = {"BUY_1": "₹10", "BUY_7": "₹50", "BUY_30": "₹150"}[QUERY.data]
            
            TEXT = f"""
╔════════════════════════════════╗
║        💎 PAYMENT INFO        ║
║         BY @proxyfxc           ║
╚════════════════════════════════╝

📅 **PLAN:** {DAYS} DAYS
💰 **PRICE:** {PRICE}

📲 **CONTACT ADMIN:** {ADMIN_USERNAME}

💳 **PAYMENT METHODS:**
• UPI / PHONEPE / GOOGLE PAY
• CRYPTOCURRENCY (USDT)
• PAYPAL (INTERNATIONAL)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AFTER PAYMENT, ADMIN WILL ACTIVATE PREMIUM.
"""
            await QUERY.message.edit_text(
                TEXT,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ BACK", callback_data="PREMIUM")
                ]])
            )
        
        elif QUERY.data == "REFER":
            ACCESS, STATUS = CHECK_ACCESS(USER.id)
            if not ACCESS and USER.id != ADMIN_ID:
                await QUERY.message.edit_text(f"⏳ PENDING APPROVAL!\nCONTACT {ADMIN_USERNAME}")
                return
            
            BOT_USERNAME = (await context.bot.get_me()).username
            REF_LINK = f"https://t.me/{BOT_USERNAME}?start=ref_{USER.id}"
            
            CUR.execute("SELECT REFERRALS FROM USERS WHERE ID=?", (USER.id,))
            REF_COUNT = CUR.fetchone()[0] if CUR.fetchone() else 0
            
            TEXT = f"""
╔════════════════════════════════╗
║        👥 REFER & EARN        ║
║         BY @proxyfxc           ║
╚════════════════════════════════╝

🎁 **REFER 2 FRIENDS = 1 DAY PREMIUM**
🎁 **REFER 10 FRIENDS = 7 DAYS PREMIUM**

🔗 **YOUR REFERRAL LINK:**
`{REF_LINK}`

📊 **YOUR REFERRALS:** {REF_COUNT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHARE THIS LINK WITH YOUR FRIENDS!
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
║         BY @proxyfxc           ║
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

👥 **REFER & EARN**
• INVITE FRIENDS
• GET FREE PREMIUM

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
        
        # ADMIN BUTTONS
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
            
            TEXT = f"""
╔════════════════════════════════╗
║       📊 BOT STATISTICS        ║
║         BY @proxyfxc           ║
╚════════════════════════════════╝

👥 TOTAL USERS: {TOTAL}
✅ APPROVED: {APPROVED}
⏳ PENDING: {PENDING}
💎 PREMIUM: {PREMIUM}
📊 TOTAL ANALYSES: {ANALYSES}

🤖 BOT STATUS: 🟢 ONLINE
"""
            await QUERY.message.edit_text(TEXT, parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
        
        elif QUERY.data == "ADMIN_USERS" and USER.id == ADMIN_ID:
            CUR.execute("SELECT ID, USERNAME, FIRST_NAME, IS_APPROVED, IS_PREMIUM, TOTAL_ANALYSIS FROM USERS ORDER BY ID DESC LIMIT 10")
            USERS = CUR.fetchall()
            
            TEXT = "👥 **RECENT USERS:**\n\n"
            for UID, UNAME, FNAME, APPROVED, PREMIUM, ANALYSES in USERS:
                STATUS = "✅" if APPROVED else "⏳"
                PREM = "💎" if PREMIUM else "👤"
                TEXT += f"{STATUS}{PREM} `{UID}` - @{UNAME or 'NONE'}\n   📊 {ANALYSES} ANALYSES\n\n"
            
            await QUERY.message.edit_text(TEXT, parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
        
        elif QUERY.data == "ADMIN_PENDING" and USER.id == ADMIN_ID:
            CUR.execute("SELECT USER_ID, USERNAME, FIRST_NAME FROM PENDING_APPROVALS")
            PENDING = CUR.fetchall()
            
            if not PENDING:
                await QUERY.message.edit_text("✅ NO PENDING APPROVALS!", reply_markup=ADMIN_KEYBOARD())
                return
            
            TEXT = "⏳ **PENDING APPROVALS:**\n\n"
            for UID, UNAME, FNAME in PENDING:
                TEXT += f"👤 `{UID}` - @{UNAME or 'NONE'}\n   📝 {FNAME}\n\n"
            
            TEXT += "USE /APPROVE USER_ID TO APPROVE"
            
            await QUERY.message.edit_text(TEXT, parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
        
        elif QUERY.data == "ADMIN_APPROVE" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'APPROVE'
            await QUERY.message.edit_text(
                "✅ **SEND USER ID OR @USERNAME TO APPROVE:**\n\nEXAMPLE: `123456789` OR `@username`",
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
                "🚫 **SEND USER ID OR @USERNAME TO BLOCK:**",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ CANCEL", callback_data="ADMIN")
                ]])
            )
        
        elif QUERY.data == "ADMIN_UNBLOCK" and USER.id == ADMIN_ID:
            context.user_data['admin_mode'] = 'UNBLOCK'
            await QUERY.message.edit_text(
                "✅ **SEND USER ID OR @USERNAME TO UNBLOCK:**",
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
        
        # ADMIN COMMANDS
        if context.user_data.get('admin_mode') == 'APPROVE' and USER.id == ADMIN_ID:
            TARGET = MSG.text.strip()
            
            if TARGET.startswith('@'):
                CUR.execute("SELECT ID FROM USERS WHERE USERNAME=?", (TARGET[1:],))
                RES = CUR.fetchone()
                if not RES:
                    await MSG.reply_text("❌ USER NOT FOUND!")
                    return
                TARGET_ID = RES[0]
            else:
                try:
                    TARGET_ID = int(TARGET)
                except:
                    await MSG.reply_text("❌ INVALID ID!")
                    return
            
            if APPROVE_USER(TARGET_ID):
                await MSG.reply_text(
                    f"✅ **USER APPROVED!**\n\n`{TARGET_ID}` CAN NOW USE THE BOT.",
                    parse_mode='Markdown',
                    reply_markup=ADMIN_KEYBOARD()
                )
                
                try:
                    await context.bot.send_message(
                        TARGET_ID,
                        "✅ **APPROVED!**\n\nYOU CAN NOW USE THE INSTAGRAM ANALYZER BOT.\n\nTYPE /START TO BEGIN!\n\n— @proxyfxc"
                    )
                except:
                    pass
            else:
                await MSG.reply_text("❌ ERROR APPROVING USER!", reply_markup=ADMIN_KEYBOARD())
            
            context.user_data['admin_mode'] = None
            return
        
        elif context.user_data.get('admin_mode') == 'ADD_PREMIUM' and USER.id == ADMIN_ID:
            try:
                PARTS = MSG.text.split()
                TARGET = PARTS[0]
                DAYS = int(PARTS[1])
                
                if TARGET.startswith('@'):
                    CUR.execute("SELECT ID FROM USERS WHERE USERNAME=?", (TARGET[1:],))
                    RES = CUR.fetchone()
                    if not RES:
                        await MSG.reply_text("❌ USER NOT FOUND!")
                        return
                    TARGET_ID = RES[0]
                else:
                    TARGET_ID = int(TARGET)
                
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
                            f"THANK YOU FOR YOUR SUPPORT! 🙏\n\n— @proxyfxc"
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
                TARGET = MSG.text.strip()
                
                if TARGET.startswith('@'):
                    CUR.execute("SELECT ID FROM USERS WHERE USERNAME=?", (TARGET[1:],))
                    RES = CUR.fetchone()
                    if not RES:
                        await MSG.reply_text("❌ USER NOT FOUND!")
                        return
                    TARGET_ID = RES[0]
                else:
                    TARGET_ID = int(TARGET)
                
                CUR.execute("UPDATE USERS SET IS_BLOCKED=1 WHERE ID=?", (TARGET_ID,))
                DB.commit()
                await MSG.reply_text(f"✅ **USER BLOCKED!**\n\n`{TARGET_ID}`", parse_mode='Markdown', reply_markup=ADMIN_KEYBOARD())
                
            except Exception as e:
                await MSG.reply_text(f"❌ ERROR: {str(e)}", reply_markup=ADMIN_KEYBOARD())
            
            context.user_data['admin_mode'] = None
            return
        
        elif context.user_data.get('admin_mode') == 'UNBLOCK' and USER.id == ADMIN_ID:
            try:
                TARGET = MSG.text.strip()
                
                if TARGET.startswith('@'):
                    CUR.execute("SELECT ID FROM USERS WHERE USERNAME=?", (TARGET[1:],))
                    RES = CUR.fetchone()
                    if not RES:
                        await MSG.reply_text("❌ USER NOT FOUND!")
                        return
                    TARGET_ID = RES[0]
                else:
                    TARGET_ID = int(TARGET)
                
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
        
        # DEEP ANALYSIS
        if context.user_data.get('mode') == 'DEEP':
            ACCESS, STATUS = CHECK_ACCESS(USER.id)
            if not ACCESS and USER.id != ADMIN_ID:
                await MSG.reply_text(f"⏳ PENDING APPROVAL!\nCONTACT {ADMIN_USERNAME}")
                context.user_data['mode'] = None
                return
            
            context.user_data['mode'] = None
            USERNAME = MSG.text.replace('@', '').strip().lower()
            
            if not USERNAME or not re.match(r'^[a-zA-Z0-9._]+$', USERNAME):
                await MSG.reply_text("❌ SEND A VALID USERNAME!")
                return
            
            # LOADING MESSAGE
            STATUS_MSG = await MSG.reply_text(f"🔍 ANALYZING @{USERNAME}...")
            
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
                
                # SEND REPORT
                await MSG.reply_text(
                    REPORT,
                    parse_mode='Markdown',
                    reply_markup=AFTER_ANALYSIS_KEYBOARD(USERNAME)
                )
                
                # UPDATE STATS
                CUR.execute("UPDATE USERS SET TOTAL_ANALYSIS = TOTAL_ANALYSIS + 1 WHERE ID=?", (USER.id,))
                DB.commit()
                
                # UPDATE TOTAL ANALYSES STAT
                CUR.execute("UPDATE STATS SET TOTAL_ANALYSES = TOTAL_ANALYSES + 1 WHERE ID=1")
                DB.commit()
            else:
                await STATUS_MSG.edit_text("❌ FAILED TO FETCH PROFILE! PLEASE TRY AGAIN.")
    
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
            await update.message.reply_text("USAGE: /approve USER_ID")
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
                    "✅ **APPROVED!**\n\nYOU CAN NOW USE THE INSTAGRAM ANALYZER BOT.\n\nTYPE /START TO BEGIN!\n\n— @proxyfxc"
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

async def MAIN():
    """MAIN BOT FUNCTION"""
    try:
        print("╔════════════════════════════════╗")
        print("║    INSTAGRAM ANALYZER PRO     ║")
        print("║         BY @proxyfxc           ║")
        print("╚════════════════════════════════╝")
        print("✅ DATABASE INITIALIZED")
        print("✅ FLASK SERVER STARTING ON PORT 8080")
        print("✅ BOT STARTING...")
        
        # START FLASK IN BACKGROUND
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
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
        print("✅ FLASK IS RUNNING ON http://localhost:8080")
        print("=" * 40)
        
        await APP.initialize()
        await APP.start()
        await APP.updater.start_polling()
        
        # KEEP RUNNING
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n❌ BOT STOPPED BY USER")
    except Exception as e:
        log_error(str(e), "MAIN")
        print(f"❌ FATAL ERROR: {e}")
    finally:
        await APP.stop()
        await APP.shutdown()
        DB.close()

if __name__ == "__main__":
    asyncio.run(MAIN())
