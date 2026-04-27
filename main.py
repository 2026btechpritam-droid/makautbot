"""
MAKAUT Mechanical Engineering Study Bot
2018-19 Syllabus | Semesters 1–8 | All Theory + All Electives
python-telegram-bot v21 | @GURU_HOSTING_TGBOT compatible

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADMIN GUIDE — HOW TO ADD CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 ALL FILES (notes, books, videos) now use the CHANNEL STORAGE method.
   This means every file goes through your private Storage Channel.
   The bot uses copy_message() — instant delivery, zero re-upload, up to 2 GB.

📋 HOW TO GET msg_id FOR ANY FILE:
   1. Upload the file (PDF, video, etc.) to your PRIVATE Storage Channel
      as a human (not the bot).
   2. Right-click the posted message → "Copy Post Link"
      → https://t.me/c/CHANNEL_ID/MSG_ID
   3. The LAST number is the msg_id.
   4. Set STORAGE_CHANNEL_ID at the top of this file.
   5. Paste {"msg_id": <number>, "caption": "..."} into the correct dict below.

📄 ADD NOTES PDFs  →  NOTES_PDF dict  (use msg_id)
   • Upload PDF to Storage Channel → get msg_id → paste below.
   • Use 0 as placeholder until uploaded (bot will skip 0 entries).

📚 ADD BOOKS PDFs  →  BOOKS_PDF dict  (use msg_id)
   • Same method as notes above.

🎬 ADD LECTURE VIDEOS  →  LECTURE_VIDEOS dict  (use msg_id)
   • Same method — works up to 2 GB per video.

📺 ADD YOUTUBE LINKS  →  YOUTUBE_LINKS dict  (below)
   • Each entry: {"title": "▶️ Playlist Name", "url": "https://..."}

🔑 SUBJECT KEYS (use these as dict keys):
   Sem1: ph1, m1b, bee1
   Sem2: ch2, m2b, pps, eng
   Sem3: m3, bio, ece3, em3, thm3, mfg3
   Sem4: mat4, at4, fm4, som4, met4
   Sem5: ht5, sm5, ktm5, etc5
   Sem6: mfgt6, dme6, or6, e6a–e6j
   Sem7: amt7, eco7, e7a–e7j, oe7a–oe7i
   Sem8: e8a–e8i, oe8a–oe8m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, asyncio, logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           ContextTypes, MessageHandler, filters)

# ── Flask keep-alive server (required for Replit to stay online) ──────────────
_flask_app = Flask(__name__)

@_flask_app.route("/")
def _home():
    return "🤖 MAKAUT ME Bot is running!", 200

@_flask_app.route("/health")
def _health():
    return "OK", 200

def _start_http():
    port = int(os.environ.get("PORT", 8080))
    _flask_app.run(host="0.0.0.0", port=port)
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN          = os.environ.get("BOT_TOKEN", "8718988931:AAGjaYFoAeWseNf7LxUSHxqkOJb7lI6KcDs")
ADMIN_CHAT_ID      = -1003756311234

# ── Channel Storage — large lecture video hosting (bypasses 50 MB bot limit) ──
STORAGE_CHANNEL_ID = int(os.environ.get("STORAGE_CHANNEL_ID", "-1003810204452"))

# ── Shared Links ───────────────────────────────────────────────────────────────
PYQ_2ND  = "https://drive.google.com/drive/folders/1pqOU462w0HneTlVK7b0Kq3W-0SnPT6wh"
ORG_2ND  = "https://drive.google.com/drive/folders/10UYEM1xmZBBWWGjbvoyyiL10ooURfi8N"
DR38     = "https://drive.google.com/drive/folders/1W46fCm1ysdJENxCazCI_ZWqsAqUxnXRy"
CS       = "coming_soon"

# ── Force Join Channels ───────────────────────────────────────────────────────
FORCE_JOIN_CHANNELS = [
    {
        "username": "mechanical_Gate_ese_je_notes2027",
        "url": "https://t.me/mechanical_Gate_ese_je_notes2027",
        "title": "🔧 Mechanical GATE/ESE/JE Notes 2027",
        "verify": True,
    },
    {
        "username": "mechanical_quiz_ese_gate_je",
        "url": "https://t.me/mechanical_quiz_ese_gate_je",
        "title": "📝 Mechanical Quiz ESE/GATE/JE",
        "verify": True,
    },
    {
        "username": "mechanicalmakaut26",
        "url": "https://youtube.com/@mechanicalmakaut26",
        "title": "▶️ YouTube — Mechanical MAKAUT",
        "verify": False,
    },
]

async def check_membership(user_id: int, context) -> list:
    not_joined = []
    for ch in FORCE_JOIN_CHANNELS:
        if not ch.get("verify", True):
            continue
        try:
            member = await context.bot.get_chat_member(
                chat_id="@" + ch["username"], user_id=user_id
            )
            logging.info("FORCE-JOIN check: user=%s ch=@%s status=%s",
                         user_id, ch["username"], member.status)
            if member.status in ("left", "kicked", "banned"):
                not_joined.append(ch)
        except Exception as e:
            msg = str(e).lower()
            if any(s in msg for s in ("member list is inaccessible",
                                      "chat not found",
                                      "bot is not a member",
                                      "bot was kicked",
                                      "chat_admin_required")):
                logging.warning("Skipping force-join check for @%s: %s", ch["username"], e)
                continue
            not_joined.append(ch)
    return not_joined

def join_keyboard(not_joined: list):
    rows = [[InlineKeyboardButton("➕ Join " + ch["title"], url=ch["url"])]
            for ch in not_joined]
    rows.append([InlineKeyboardButton("✅ I Have Joined — Check Again", callback_data="check_join")])
    return InlineKeyboardMarkup(rows)
# ─────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# 📂  NOTES PDF  ——  Channel Storage msg_ids, grouped unit-wise per subject
# ══════════════════════════════════════════════════════════════════════════════
NOTES_PDF = {

    # ── Semester 1 ──
    "ph1":  [],
    "m1b":  [],
    "bee1": [],

    # ── Semester 2 ──
    "ch2": [
        {"msg_id": 32, "caption": "Chemistry I – Unit 1 Hand Written Notes"},
        {"msg_id": 33, "caption": "Chemistry I – Unit 2 Combined Notes"},
        {"msg_id": 34, "caption": "Chemistry I – Unit 2 Hand Written Notes (One Shot)"},
        {"msg_id": 30, "caption": "Chemistry I – Unit 3 Combined Notes"},
        {"msg_id": 29, "caption": "Chemistry I – Unit 4 Hand Written Notes"},
        {"msg_id": 28, "caption": "Chemistry I – Unit 5 Hand Written Notes"},
        {"msg_id": 31, "caption": "Chemistry I – Unit 5 Hand Written Notes (Part 2)"},
    ],
    "m2b":  [],
    "pps": [
        {"msg_id": 40, "caption": "PPS – Unit 1 Hand Written Notes"},
        {"msg_id": 41, "caption": "PPS – Unit 1 Combined Notes"},
        {"msg_id": 42, "caption": "PPS – Unit 2 Combined Notes"},
        {"msg_id": 43, "caption": "PPS – Unit 2 Hand Written Notes"},
        {"msg_id": 44, "caption": "PPS – Unit 3 Hand Written Notes"},
        {"msg_id": 45, "caption": "PPS – Unit 3 Combined Notes"},
        {"msg_id": 46, "caption": "PPS – Unit 4 Hand Written Notes"},
        {"msg_id": 49, "caption": "PPS – Unit 4 Combined Notes"},
        {"msg_id": 54, "caption": "PPS – Unit 5 Combined Notes"},
        {"msg_id": 286, "caption": "PPS – Most Important Questions"},
        {"msg_id": 39, "caption": "PPS – Additional Notes"},
    ],
    "eng":  [],

    # ── Semester 3 ──
    "m3":   [],
    "bio":  [],
    "ece3": [],
    "em3":  [],
    "thm3": [],
    "mfg3": [],

    # ── Semester 4 ──
    "mat4": [],
    "at4": [
        {"msg_id": 104, "caption": "Applied Thermodynamics – Unit 1 IMP Questions"},
        {"msg_id": 106, "caption": "Applied Thermodynamics – Unit 1 Lec 1"},
        {"msg_id": 107, "caption": "Applied Thermodynamics – Unit 1 Lec 2"},
        {"msg_id": 108, "caption": "Applied Thermodynamics – Unit 1 Lec 3"},
        {"msg_id": 109, "caption": "Applied Thermodynamics – Unit 1 Lec 4"},
        {"msg_id": 110, "caption": "Applied Thermodynamics – Unit 1 Lec 5"},
        {"msg_id": 111, "caption": "Applied Thermodynamics – Unit 1 Lec 6"},
        {"msg_id": 112, "caption": "Applied Thermodynamics – Unit 1 Turbocharger & Supercharger (One Shot)"},
        {"msg_id": 105, "caption": "Applied Thermodynamics – Unit 2 Combined Notes"},
        {"msg_id": 113, "caption": "Applied Thermodynamics – Unit 3 Complete Notes"},
        {"msg_id": 114, "caption": "Applied Thermodynamics – Unit 3 Boiler Notes"},
        {"msg_id": 115, "caption": "Applied Thermodynamics – Unit 3 Boiler Notes Part 1"},
        {"msg_id": 116, "caption": "Applied Thermodynamics – Unit 3 Boiler Part 2 Draught Notes"},
        {"msg_id": 117, "caption": "Applied Thermodynamics – Unit 4 Notes"},
        {"msg_id": 118, "caption": "Applied Thermodynamics – Unit 4 Steam Nozzle Numericals"},
        {"msg_id": 119, "caption": "Applied Thermodynamics – Unit 5 Lec 1"},
        {"msg_id": 120, "caption": "Applied Thermodynamics – Unit 5 Lec 3"},
        {"msg_id": 121, "caption": "Applied Thermodynamics – Unit 5 Lec 5"},
        {"msg_id": 122, "caption": "Applied Thermodynamics – Unit 5 Lec 6"},
        {"msg_id": 123, "caption": "Applied Thermodynamics – Unit 5 Lec 7"},
        {"msg_id": 124, "caption": "Applied Thermodynamics – Unit 5 Jet Propulsion"},
    ],
    "fm4":  [],
    "som4": [
        {"msg_id": 135, "caption": "Strength of Materials – Notes Part 1"},
        {"msg_id": 149, "caption": "Strength of Materials – Notes Part 2"},
        {"msg_id": 162, "caption": "Strength of Materials – Notes Part 3"},
        {"msg_id": 163, "caption": "Strength of Materials – Notes Part 4"},
        {"msg_id": 164, "caption": "Strength of Materials – Notes Part 5"},
        {"msg_id": 165, "caption": "Strength of Materials – Notes Part 6"},
        {"msg_id": 168, "caption": "Strength of Materials – Notes Part 7"},
        {"msg_id": 169, "caption": "Strength of Materials – Notes Part 8"},
        {"msg_id": 170, "caption": "Strength of Materials – Notes Part 9"},
    ],
    "met4": [],

    # ── Semester 5 ──
    "ht5":  [],
    "sm5":  [],
    "ktm5": [],
    "etc5": [],

    # ── Semester 6 ──
    "mfgt6": [],
    "dme6":  [],
    "or6":   [],
    "e6a":   [],
    "e6b": [
        {"msg_id": 184, "caption": "Refrigeration & Air Conditioning – Notes Part 1"},
        {"msg_id": 185, "caption": "Refrigeration & Air Conditioning – Notes Part 2"},
        {"msg_id": 186, "caption": "Refrigeration & Air Conditioning – Notes Part 3"},
        {"msg_id": 187, "caption": "Refrigeration & Air Conditioning – Notes Part 4"},
    ],
    "e6c":   [],
    "e6d":   [],
    "e6e":   [],
    "e6f":   [],
    "e6g":   [],
    "e6h":   [],
    "e6i":   [],
    "e6j":   [],

    # ── Semester 7 ──
    "amt7":  [],
    "eco7":  [],
    "e7a":   [],
    "e7b":   [],
    "e7c":   [],
    "e7d":   [],
    "e7e":   [],
    "e7f":   [],
    "e7g":   [],
    "e7h":   [],
    "e7i":   [],
    "e7j":   [],

    # ── Semester 8 ──
    "e8a":   [],
    "e8b":   [],
    "e8c":   [],
    "e8d":   [],
    "e8e":   [],
    "e8f":   [],
    "e8g":   [],
    "e8h":   [],
    "e8i":   [],
}

# ══════════════════════════════════════════════════════════════════════════════
# 📁  NOTES DRIVE  ——  Google Drive folder links (when no individual PDFs yet)
# ══════════════════════════════════════════════════════════════════════════════
NOTES_DRIVE = {
    "met4": "https://drive.google.com/drive/folders/1EnmL93MnVJplEmg4CbVG2gds5ZR1MqV9",
}

# ══════════════════════════════════════════════════════════════════════════════
# 📄  NOTES PDF — CHANNEL STORAGE  (large notes; bypasses 50 MB bot limit)
# ══════════════════════════════════════════════════════════════════════════════
NOTES_PDF_CHANNEL = {

    # ── Semester 1 ──
    "ph1":  [],
    "m1b":  [],
    "bee1": [],

    # ── Semester 2 ──
    "ch2":  [],
    "m2b": [
        {"msg_id": 10, "caption": "Mathematics IIB – Notes Part 1"},
        {"msg_id": 11, "caption": "Mathematics IIB – Notes Part 2"},
        {"msg_id": 12, "caption": "Mathematics IIB – Notes Part 3"},
        {"msg_id": 13, "caption": "Mathematics IIB – Notes Part 4"},
        {"msg_id": 14, "caption": "Mathematics IIB – Notes Part 5"},
        {"msg_id": 15, "caption": "Mathematics IIB – Notes Part 6"},
        {"msg_id": 16, "caption": "Mathematics IIB – Notes Part 7"},
        {"msg_id": 17, "caption": "Mathematics IIB – Notes Part 8"},
        {"msg_id": 18, "caption": "Mathematics IIB – Notes Part 9"},
        {"msg_id": 19, "caption": "Mathematics IIB – Notes Part 10"},
        {"msg_id": 20, "caption": "Mathematics IIB – Notes Part 11"},
        {"msg_id": 21, "caption": "Mathematics IIB – Notes Part 12"},
        {"msg_id": 22, "caption": "Mathematics IIB – Notes Part 13"},
        {"msg_id": 23, "caption": "Mathematics IIB – Notes Part 14"},
        {"msg_id": 24, "caption": "Mathematics IIB – Notes Part 15"},
        {"msg_id": 25, "caption": "Mathematics IIB – Notes Part 16"},
        {"msg_id": 26, "caption": "Mathematics IIB – Notes Part 17"},
        {"msg_id": 27, "caption": "Mathematics IIB – Notes Part 18"},
        {"msg_id": 56, "caption": "Mathematics IIB – Notes Part 19"},
        {"msg_id": 57, "caption": "Mathematics IIB – Notes Part 20"},
        {"msg_id": 58, "caption": "Mathematics IIB – Notes Part 21"},
    ],
    "pps":  [],
    "eng":  [],

    # ── Semester 3 ──
    "m3":   [],
    "bio":  [],
    "ece3": [],
    "em3":  [],
    "thm3": [],
    "mfg3": [],

    # ── Semester 4 ──
    "mat4": [
        {"msg_id": 231, "caption": "Materials Engineering – Notes"},
    ],
    "at4": [
        {"msg_id": 203, "caption": "Applied Thermodynamics – Notes Part 1"},
        {"msg_id": 229, "caption": "Applied Thermodynamics – Notes Part 2"},
        {"msg_id": 230, "caption": "Applied Thermodynamics – Notes Part 3"},
        {"msg_id": 231, "caption": "Applied Thermodynamics – Notes Part 4"},
        {"msg_id": 232, "caption": "Applied Thermodynamics – Notes Part 5"},
    ],
    "fm4": [
        {"msg_id": 230, "caption": "Fluid Mechanics & Fluid Machines – Notes"},
    ],
    "som4": [],
    "met4": [],

    # ── Semester 5 ──
    "ht5":  [],
    "sm5":  [],
    "ktm5": [],
    "etc5": [],

    # ── Semester 6 ──
    "mfgt6": [
        {"msg_id": 298, "caption": "Manufacturing Technology – Notes Part 1"},
        {"msg_id": 297, "caption": "Manufacturing Technology – Notes Part 2"},
        {"msg_id": 296, "caption": "Manufacturing Technology – Notes Part 3"},
        {"msg_id": 295, "caption": "Manufacturing Technology – Notes Part 4"},
        {"msg_id": 299, "caption": "Manufacturing Technology – Notes Part 5"},
        {"msg_id": 300, "caption": "Manufacturing Technology – Notes Part 6"},
    ],
    "dme6": [
        {"msg_id": 232, "caption": "Design of Machine Elements – Notes Part 1"},
        {"msg_id": 239, "caption": "Design of Machine Elements – Notes Part 2"},
    ],
    "or6":   [],
    "e6a":   [],
    "e6b":   [],
    "e6c":   [],
    "e6d":   [],
    "e6e":   [],
    "e6f":   [],
    "e6g":   [],
    "e6h":   [],
    "e6i":   [],
    "e6j":   [],

    # ── Semester 7 ──
    "amt7":  [],
    "eco7":  [],
    "e7a":   [],
    "e7b":   [],
    "e7c":   [],
    "e7d":   [],
    "e7e":   [],
    "e7f":   [],
    "e7g":   [],
    "e7h":   [],
    "e7i":   [],
    "e7j":   [],

    # ── Semester 8 ──
    "e8a":   [],
    "e8b":   [],
    "e8c":   [],
    "e8d":   [],
    "e8e":   [],
    "e8f":   [],
    "e8g":   [],
    "e8h": [
        {"msg_id": 236, "caption": "Process Planning & Cost Estimation – Notes"},
    ],
    "e8i":   [],
}

# ══════════════════════════════════════════════════════════════════════════════
# 📹  LECTURE VIDEOS  ——  Channel Storage method (bypasses 50 MB bot limit)
# ══════════════════════════════════════════════════════════════════════════════
LECTURE_VIDEOS = {

    # ── Semester 4 ──
    "at4": [
        # Unit 2 (7 videos)
        {"msg_id": 195, "caption": "Applied Thermodynamics – Unit 2 Lecture 1"},
        {"msg_id": 196, "caption": "Applied Thermodynamics – Unit 2 Lecture 2"},
        {"msg_id": 197, "caption": "Applied Thermodynamics – Unit 2 Lecture 3"},
        {"msg_id": 198, "caption": "Applied Thermodynamics – Unit 2 Lecture 4"},
        {"msg_id": 200, "caption": "Applied Thermodynamics – Unit 2 Lecture 5"},
        {"msg_id": 201, "caption": "Applied Thermodynamics – Unit 2 Lecture 6"},
        {"msg_id": 202, "caption": "Applied Thermodynamics – Unit 2 Lecture 7"},
        # Unit 3 (10 videos)
        {"msg_id": 74,  "caption": "Applied Thermodynamics – Unit 3 Lecture 1"},
        {"msg_id": 75,  "caption": "Applied Thermodynamics – Unit 3 Lecture 2"},
        {"msg_id": 76,  "caption": "Applied Thermodynamics – Unit 3 Lecture 3"},
        {"msg_id": 77,  "caption": "Applied Thermodynamics – Unit 3 Lecture 4"},
        {"msg_id": 78,  "caption": "Applied Thermodynamics – Unit 3 Lecture 5"},
        {"msg_id": 79,  "caption": "Applied Thermodynamics – Unit 3 Lecture 6"},
        {"msg_id": 80,  "caption": "Applied Thermodynamics – Unit 3 Lecture 7"},
        {"msg_id": 81,  "caption": "Applied Thermodynamics – Unit 3 Lecture 8"},
        {"msg_id": 82,  "caption": "Applied Thermodynamics – Unit 3 Lecture 9"},
        {"msg_id": 83,  "caption": "Applied Thermodynamics – Unit 3 Lecture 10"},
        # Unit 4 & 5 (17 videos)
        {"msg_id": 85,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 1"},
        {"msg_id": 86,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 2"},
        {"msg_id": 87,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 3"},
        {"msg_id": 88,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 4"},
        {"msg_id": 89,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 5"},
        {"msg_id": 90,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 6"},
        {"msg_id": 91,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 7"},
        {"msg_id": 92,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 8"},
        {"msg_id": 93,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 9"},
        {"msg_id": 94,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 10"},
        {"msg_id": 95,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 11"},
        {"msg_id": 96,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 12"},
        {"msg_id": 97,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 13"},
        {"msg_id": 99,  "caption": "Applied Thermodynamics – Unit 4&5 Lecture 14"},
        {"msg_id": 100, "caption": "Applied Thermodynamics – Unit 4&5 Lecture 15"},
        {"msg_id": 101, "caption": "Applied Thermodynamics – Unit 4&5 Lecture 16"},
        {"msg_id": 102, "caption": "Applied Thermodynamics – Unit 4&5 Lecture 17"},
    ],

    "som4": [
        # Unit 1 (6 videos)
        {"msg_id": 127, "caption": "Strength of Materials – Unit 1 Lecture 1"},
        {"msg_id": 128, "caption": "Strength of Materials – Unit 1 Lecture 2"},
        {"msg_id": 129, "caption": "Strength of Materials – Unit 1 Lecture 3"},
        {"msg_id": 130, "caption": "Strength of Materials – Unit 1 Lecture 4"},
        {"msg_id": 131, "caption": "Strength of Materials – Unit 1 Lecture 5"},
        {"msg_id": 132, "caption": "Strength of Materials – Unit 1 Lecture 6"},
        # Unit 2 (10 videos)
        {"msg_id": 139, "caption": "Strength of Materials – Unit 2 Lecture 1"},
        {"msg_id": 140, "caption": "Strength of Materials – Unit 2 Lecture 2"},
        {"msg_id": 141, "caption": "Strength of Materials – Unit 2 Lecture 3"},
        {"msg_id": 142, "caption": "Strength of Materials – Unit 2 Lecture 4"},
        {"msg_id": 143, "caption": "Strength of Materials – Unit 2 Lecture 5"},
        {"msg_id": 144, "caption": "Strength of Materials – Unit 2 Lecture 6"},
        {"msg_id": 145, "caption": "Strength of Materials – Unit 2 Lecture 7"},
        {"msg_id": 146, "caption": "Strength of Materials – Unit 2 Lecture 8"},
        {"msg_id": 147, "caption": "Strength of Materials – Unit 2 Lecture 9"},
        {"msg_id": 148, "caption": "Strength of Materials – Unit 2 Lecture 10"},
        # Unit 3 (11 videos)
        {"msg_id": 151, "caption": "Strength of Materials – Unit 3 Lecture 1"},
        {"msg_id": 152, "caption": "Strength of Materials – Unit 3 Lecture 2"},
        {"msg_id": 153, "caption": "Strength of Materials – Unit 3 Lecture 3"},
        {"msg_id": 154, "caption": "Strength of Materials – Unit 3 Lecture 4"},
        {"msg_id": 155, "caption": "Strength of Materials – Unit 3 Lecture 5"},
        {"msg_id": 156, "caption": "Strength of Materials – Unit 3 Lecture 6"},
        {"msg_id": 157, "caption": "Strength of Materials – Unit 3 Lecture 7"},
        {"msg_id": 158, "caption": "Strength of Materials – Unit 3 Lecture 8"},
        {"msg_id": 159, "caption": "Strength of Materials – Unit 3 Lecture 9"},
        {"msg_id": 160, "caption": "Strength of Materials – Unit 3 Lecture 10"},
        {"msg_id": 161, "caption": "Strength of Materials – Unit 3 Lecture 11"},
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# 📚  BOOKS PDF  ——  Channel Storage msg_ids for reference book PDFs per subject
# ══════════════════════════════════════════════════════════════════════════════
BOOKS_PDF = {
    # legacy, kept for compatibility (no entries)
}

# ══════════════════════════════════════════════════════════════════════════════
# 📚  BOOKS PDF — CHANNEL STORAGE  (large books; bypasses 50 MB bot limit)
# ══════════════════════════════════════════════════════════════════════════════
BOOKS_PDF_CHANNEL = {

    # ── Semester 2 ──
    "ch2": [
        {"msg_id": 166, "caption": "Engineering Chemistry – Reference Book"},
    ],

    # ── Semester 3 ──
    "em3": [
        {"msg_id": 175, "caption": "Engineering Mechanics – RS Khurmi"},
        {"msg_id": 176, "caption": "Engineering Mechanics – KL Kumar"},
        {"msg_id": 178, "caption": "Engineering Mechanics – RK Bansal"},
    ],
    "thm3": [
        {"msg_id": 179, "caption": "Engineering Thermodynamics – PK Nag (5th Ed.)"},
        {"msg_id": 180, "caption": "Engineering Thermodynamics – PK Nag Solutions"},
        {"msg_id": 181, "caption": "Engineering Thermodynamics – RK Rajput"},
    ],
    "mfg3": [
        {"msg_id": 182, "caption": "Manufacturing Technology – PN Rao (Vol. 1)"},
        {"msg_id": 204, "caption": "Manufacturing Technology – PN Rao (Vol. 2)"},
        {"msg_id": 205, "caption": "Manufacturing Science – Ghosh & Malik"},
        {"msg_id": 206, "caption": "Fundamentals of Modern Manufacturing – Groover"},
    ],
    "bio":  [],
    "ece3": [],
    "m3":   [],

    # ── Semester 4 ──
    "mat4": [
        {"msg_id": 207, "caption": "Materials Science – RS Khurmi"},
        {"msg_id": 244, "caption": "Materials Engineering – Additional Book"},
    ],
    "at4": [
        {"msg_id": 208, "caption": "Engineering Thermodynamics – PK Nag (5th Ed.)"},
        {"msg_id": 209, "caption": "Engineering Thermodynamics – PK Nag Solutions"},
        {"msg_id": 240, "caption": "Applied Thermodynamics – Reference Book 1"},
        {"msg_id": 255, "caption": "Applied Thermodynamics – Reference Book 2"},
    ],
    "fm4": [
        {"msg_id": 210, "caption": "Fluid Mechanics – RS Khurmi (19th Ed.)"},
        {"msg_id": 211, "caption": "Fluid Mechanics – RK Bansal"},
        {"msg_id": 212, "caption": "Fluid Mechanics & Hydraulic Machines – RK Rajput (5th Ed.)"},
        {"msg_id": 214, "caption": "Fluid Mechanics (Advanced) – Rajput & Tabatabaian"},
        {"msg_id": 243, "caption": "Fluid Mechanics – Additional Book 1"},
        {"msg_id": 250, "caption": "Fluid Mechanics – Additional Book 2"},
        {"msg_id": 267, "caption": "Fluid Mechanics – Additional Book 3"},
    ],
    "som4": [
        {"msg_id": 215, "caption": "Strength of Materials – RS Khurmi"},
        {"msg_id": 216, "caption": "Mechanics of Materials – BC Punmia"},
        {"msg_id": 217, "caption": "Strength of Materials – RK Rajput"},
        {"msg_id": 229, "caption": "Strength of Materials – Book 4"},
        {"msg_id": 234, "caption": "Strength of Materials – Book 5"},
        {"msg_id": 245, "caption": "Strength of Materials – Book 6"},
        {"msg_id": 261, "caption": "Strength of Materials – Book 7"},
        {"msg_id": 268, "caption": "Strength of Materials – Book 8"},
    ],
    "met4": [
        {"msg_id": 218, "caption": "Mechanical Measurements & Instrumentation – RK Rajput"},
        {"msg_id": 259, "caption": "Metrology & Instrumentation – Reference Book"},
    ],

    # ── Semester 5 ──
    "ht5": [
        {"msg_id": 219, "caption": "Heat Transfer – SK Som"},
        {"msg_id": 220, "caption": "Heat & Mass Transfer – RK Rajput (5th Ed.)"},
    ],
    "ktm5": [
        {"msg_id": 221, "caption": "Theory of Machines – RS Khurmi"},
        {"msg_id": 222, "caption": "Theory of Machines – SS Ratan"},
    ],
    "sm5":  [],
    "etc5": [],

    # ── Semester 6 ──
    "mfgt6": [
        {"msg_id": 223, "caption": "Manufacturing Technology – PN Rao (Vol. 1)"},
        {"msg_id": 224, "caption": "Manufacturing Technology – PN Rao (Vol. 2)"},
        {"msg_id": 225, "caption": "Manufacturing Technology – RK Rajput"},
        {"msg_id": 226, "caption": "Manufacturing Science – Ghosh & Malik"},
        {"msg_id": 257, "caption": "Manufacturing Technology – Additional Book 1"},
        {"msg_id": 216, "caption": "Manufacturing Technology – Additional Book 2"},
        {"msg_id": 203, "caption": "Manufacturing Technology – Additional Book 3"},
    ],
    "dme6": [
        {"msg_id": 227, "caption": "Design of Machine Elements – VB Bhandari"},
        {"msg_id": 228, "caption": "Machine Design – RS Khurmi & JK Gupta"},
        {"msg_id": 249, "caption": "Design of Machine Elements – Additional Reference"},
    ],
    "or6":  [],
    "e6a": [
        {"msg_id": 179, "caption": "IC Engines & Gas Turbines – Book 1"},
        {"msg_id": 180, "caption": "IC Engines & Gas Turbines – Book 2"},
        {"msg_id": 253, "caption": "IC Engines & Gas Turbines – Book 3"},
        {"msg_id": 238, "caption": "IC Engines & Gas Turbines – Book 4"},
    ],
    "e6b": [
        {"msg_id": 248, "caption": "Refrigeration & Air Conditioning – Book 1"},
        {"msg_id": 260, "caption": "Refrigeration & Air Conditioning – Book 2"},
    ],
    "e6c":  [],
    "e6d":  [],
    "e6e":  [],
    "e6f":  [],
    "e6g":  [],
    "e6h":  [],
    "e6i":  [],
    "e6j":  [],

    # ── Semester 7 ──
    "amt7":  [],
    "eco7":  [],
    "e7a":   [],
    "e7f":   [],
    "e7g":   [],
    "oe7a":  [],
    "oe7d":  [],

    # ── Semester 8 ──
    "e8b": [
        {"msg_id": 252, "caption": "Power Plant Engineering – RK Rajput"},
        {"msg_id": 240, "caption": "Power Plant Engineering – PK Nag"},
    ],
    "e8h":   [],
    "oe8d":  [],
    "oe8f":  [],
}

# ══════════════════════════════════════════════════════════════════════════════
# 🎬  YOUTUBE LINKS  ——  Playlists & videos per subject
# ══════════════════════════════════════════════════════════════════════════════
YOUTUBE_LINKS = {

    # ── Semester 2 ──
    "ch2": [
        {"title": "▶️ Engineering Chemistry – Playlist 1", "url": "https://youtube.com/playlist?list=PLiYAH68F-CTBTtumVFNH8exEvjWtUYdw_&si=pRJJmQCCY9jE78r0"},
        {"title": "▶️ Engineering Chemistry – Playlist 2", "url": "https://youtube.com/playlist?list=PLW1Y7Rfg4m8Jhs-s_VfYWgWzwTqYUvxJb&si=oBGuCdECHbD8v_h5"},
        {"title": "▶️ Engineering Chemistry – Playlist 3", "url": "https://youtube.com/playlist?list=PLHWPZcIu1IxDyJAGxeeTSneBFwhhbdStX&si=FjkiGaRSGI_gy13k"},
        {"title": "▶️ Engineering Chemistry – Playlist 4", "url": "https://youtube.com/playlist?list=PLqbFiuYjdw8i0oJwSng6-udW4izlDJkBj&si=Kf1xWu2588UCUaHp"},
        {"title": "▶️ Engineering Chemistry – Playlist 5", "url": "https://youtube.com/playlist?list=PLDjIJRH6sIC7cmnj9U4fIbxrULzm53ZwT&si=l7aiID3id5c--aQi"},
        {"title": "▶️ Engineering Chemistry – Video",      "url": "https://youtu.be/E1MikgBHcZU?si=WymAVXRe77HqIZK7"},
    ],

    "m2b": [
        {"title": "▶️ Mathematics IIB – Playlist 1",       "url": "https://youtube.com/playlist?list=PL5Dqs90qDljUoxJRL1Mxm7Twa4ysdsQzf&si=HzbB_Ew8MNK6upXN"},
        {"title": "▶️ Mathematics IIB – Playlist 2",       "url": "https://youtube.com/playlist?list=PLT3bOBUU3L9iJduBlC3tcC6RN2TvUwAno&si=UWtGqWMmbo_pl5vd"},
        {"title": "▶️ Mathematics IIB – Playlist 3",       "url": "https://youtube.com/playlist?list=PLhSp9OSVmeyKxN4DXIA5f2noV2cZ_1DZJ&si=9nsuzfyBqrmny5cn"},
        {"title": "▶️ Mathematics IIB – Playlist 4",       "url": "https://youtube.com/playlist?list=PLKS7ZMKnbPrTe_ayBsypP_36cH34NOylM&si=fSZK8Nd31nyrU9zx"},
        {"title": "▶️ Mathematics IIB – Playlist 5",       "url": "https://youtube.com/playlist?list=PL5Dqs90qDljXrOVMo1nnKRe7e7AyCUzuC&si=zFhiJkSTkbS-ntlR"},
        {"title": "▶️ Mathematics IIB – Playlist 6",       "url": "https://youtube.com/playlist?list=PL5Dqs90qDljUOgDy9scaX5vRPa5Koio5h&si=RzU8AN0xHAd7cJDC"},
        {"title": "▶️ Mathematics IIB – Live Lecture",     "url": "https://www.youtube.com/live/leeYyymYcdA?si=I6QNWlaHwtbKBafe"},
        {"title": "▶️ Mathematics IIB – Video",            "url": "https://youtu.be/M2y9lwcy9tc?si=yqPFk2NaIWXZRTio"},
        {"title": "▶️ Dr SP Gupta M-Classes (Channel)",    "url": "https://youtube.com/@dr.spgupta-mclasses?si=W-UScX3fEUlJ3QK2"},
    ],

    "pps": [
        {"title": "▶️ PPS – Playlist 1", "url": "https://youtube.com/playlist?list=PL-vEH_IPWrhCXIzSaO9t9LlxMwtSCtwxR&si=iWAApF4bk4BusBtk"},
        {"title": "▶️ PPS – Playlist 2", "url": "https://youtube.com/playlist?list=PL49mRA0Y_C8vQV1h4YVtGUQGu4BQY6hrv&si=5jM3K_hsvUK1NxYL"},
        {"title": "▶️ PPS – Playlist 3", "url": "https://youtube.com/playlist?list=PLkojphh8hBnYb6K3B79ZEhb4AyuvgksFA&si=ukhP0m_Wxn0SI441"},
    ],

    # ── Semester 4 ──
    "mat4": [
        {"title": "▶️ Materials Engineering – Playlist 1", "url": "https://youtube.com/playlist?list=PLjMQ11sM-5iwWYbnSsBxUus1HawGg0HGa"},
        {"title": "▶️ Materials Engineering – Video",      "url": "https://youtu.be/nCBUwiib0Xo"},
        {"title": "▶️ Materials Engineering – Playlist 2", "url": "https://youtube.com/playlist?list=PLWo-ERPOfIbbOV1slvh62wHgcxaB2-mDT"},
    ],

    "fm4": [
        {"title": "▶️ Fluid Mechanics – Playlist 1", "url": "https://youtube.com/playlist?list=PLY8pCdWSlXrTmdn-QOYb71f1LazGmyVT9"},
        {"title": "▶️ Fluid Mechanics – Playlist 2", "url": "https://youtube.com/playlist?list=PL03n4PEXL4sZZQ_4_Z9zGUEfpRbAyYxbc"},
        {"title": "▶️ Fluid Mechanics – Playlist 3", "url": "https://youtube.com/playlist?list=PL03n4PEXL4sZkNWcZRfiStoVUxIMCyl13"},
        {"title": "▶️ Fluid Mechanics – Playlist 4", "url": "https://youtube.com/playlist?list=PLm_MSClsnwm-0hJKaJrnYbIVNOUudxj7O"},
        {"title": "▶️ Fluid Mechanics – Playlist 5", "url": "https://youtube.com/playlist?list=PLzpAOaJe3cEibAI-LLEUja3q34NaQdMgb"},
        {"title": "▶️ Fluid Mechanics – Playlist 6", "url": "https://youtube.com/playlist?list=PLxELPHxWUOQvwlY1Dxc6iwKfjoJjC2zO0"},
        {"title": "▶️ Fluid Mechanics – Playlist 7", "url": "https://youtube.com/playlist?list=PLxELPHxWUOQtykLc0S5F74gNSVYRVQcvI"},
    ],

    "som4": [
        {"title": "▶️ SOM – Playlist 1 ✅ (Recommended)", "url": "https://youtube.com/playlist?list=PLm_MSClsnwm9j0syYD13UsLAUQEqiBX3v&si=dJL_QA8tNbWnDO8T"},
        {"title": "▶️ SOM – Playlist 2 ✅",               "url": "https://youtube.com/playlist?list=PLIhUrsYr8yHzft7ygw5THZo4aDcsxEadP&si=mU_aczalCC8SX-kL"},
    ],

    "met4": [
        {"title": "▶️ Metrology – Playlist 1 ✅", "url": "https://youtube.com/playlist?list=PLPXROVdwXkYDecNQ90_6ndO0aTfeugVaV&si=-BWj3sQ47srcdYVH"},
        {"title": "▶️ Metrology – Playlist 2",    "url": "https://youtube.com/playlist?list=PLGTEoD30O0gaXcQ6c46xXTmSRAMXtQFKp"},
        {"title": "▶️ Metrology – Playlist 3",    "url": "https://youtube.com/playlist?list=PLg9TnucUbzBX9R9T6imFDCjTZp8nJFtQm"},
        {"title": "▶️ Metrology – Playlist 4 ✅", "url": "https://youtube.com/playlist?list=PL0s3O6GgLL5cY5F3ZZjSVpgJp1FkqMXJW"},
        {"title": "▶️ Metrology – Playlist 5",    "url": "https://youtube.com/playlist?list=PLTWGsRaojtPaSXtSsNxNiATHrxlhaBwfa"},
    ],

    # ── Semester 6 ──
    "e6a": [
        {"title": "▶️ IC Engines & Gas Turbines – Playlist 1", "url": "https://youtube.com/playlist?list=PLwdnzlV3ogoXHbVNKWL1BYOo_8PpyNtnC"},
        {"title": "▶️ IC Engines & Gas Turbines – Playlist 2", "url": "https://youtube.com/playlist?list=PLc8T_CSyq_2CeqWmOQmDN-0eHQHY55k84"},
        {"title": "▶️ IC Engines & Gas Turbines – Playlist 3", "url": "https://youtube.com/playlist?list=PLEt20WwAo4BjQHKRJPyuy8Wd9uZATpNCg"},
    ],

    "dme6": [
        {"title": "▶️ Design of Machine Elements – Playlist 1", "url": "https://youtube.com/playlist?list=PLfq4fiRrJSn4lPuuGfL1bj6FvueRlslOt"},
        {"title": "▶️ Design of Machine Elements – Playlist 2", "url": "https://youtube.com/playlist?list=PLfcoXoGOQYe6ifMj-ntsYXlwnVwugMWPz"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────

WELCOME = (
    "🔧 *Mechanical Engineering — MAKAUT University* 🎓\n\n"
    "Welcome to your ultimate study companion for Mechanical Engineering "
    "under *Maulana Abul Kalam Azad University of Technology (MAKAUT)*!\n\n"
    "✅ *What We Offer:*\n"
    "• 📚 Complete syllabus-wise study materials (Semester 1–8)\n"
    "• 📝 Previous year question papers & solutions\n"
    "• 🎯 Important questions & exam tips\n"
    "• 📘 Lecture notes, PDFs & handwritten resources\n"
    "• 🔄 Unit-wise & subject-wise organized content\n"
    "• 💡 Concepts explained simply for better understanding\n\n"
    "👇 Select your *Semester* below:"
)

# ── Resource builder ───────────────────────────────────────────────────────────
def r(pyq, org):
    return {
        "pyq": [
            {"title": "📂 PYQ — Google Drive", "url": pyq, "description": "Previous year question papers on Drive"},
        ],
        "books": [
            {"title": "🚧 Direct Book PDF Links", "url": CS},
        ],
        "organizers": [
            {"title": "📋 Organizer / Handouts — Google Drive", "url": org, "description": "Organized study materials & handouts"},
        ],
    }

def s(name, code, desc, pyq=DR38, org=DR38):
    return {"name": name, "code": code, "description": desc, "resources": r(pyq, org)}

# ─────────────────────────────────────────────────────────────────────────────
# STUDY MATERIALS — MAKAUT 2018-19 Syllabus
# ─────────────────────────────────────────────────────────────────────────────
MATERIALS = {
    "1": {
        "name": "1st Semester",
        "info": "3 theory subjects | Physics, Mathematics & Electrical Engineering.",
        "subjects": {
            "ph1":  s("Physics I",                   "BS-PH101", "Mechanics, oscillations, waves, optics, electricity, modern physics.",                       CS, CS),
            "m1b":  s("Mathematics IB",              "BS-M102",  "Differential calculus, integral calculus, series, ODE, vector algebra.",                     CS, CS),
            "bee1": s("Basic Electrical Engineering","ES-EE101", "DC/AC circuits, network theorems, transformers, electrical machines, measuring instruments.", CS, CS),
        },
    },
    "2": {
        "name": "2nd Semester",
        "info": "4 theory subjects | PYQ & organizers available on Google Drive.",
        "subjects": {
            "ch2":  s("Chemistry I",                    "BS-CH201", "Atomic structure, bonding, electrochemistry, polymers, corrosion, water treatment.", PYQ_2ND, ORG_2ND),
            "m2b":  s("Mathematics IIB",                "BS-M202",  "Partial differentiation, multiple integrals, ODE, linear algebra, Z-transform.",    PYQ_2ND, ORG_2ND),
            "pps":  s("Programming for Problem Solving","ES-CS201", "C programming, algorithms, arrays, functions, pointers, file handling.",             PYQ_2ND, ORG_2ND),
            "eng":  s("English",                        "HM-HU201", "Technical English, grammar, comprehension, business communication, writing skills.",  PYQ_2ND, ORG_2ND),
        },
    },
    "3": {
        "name": "3rd Semester",
        "info": "6 theory subjects | PYQ & organizers on Google Drive.",
        "subjects": {
            "m3":   s("Mathematics III",              "BS-M301",   "Fourier series, Laplace transform, PDE, complex variables, probability & statistics."),
            "bio":  s("Biology",                      "BS-BIO301", "Cell biology, genetics, enzyme kinetics, microbiology, ecology, biomolecules."),
            "ece3": s("Basic Electronics Engineering","ES-ECE301", "Diodes, BJT, Op-Amp, digital electronics, communication systems fundamentals."),
            "em3":  s("Engineering Mechanics",        "ES-ME301",  "Force systems, equilibrium, friction, kinematics of particles & rigid bodies, dynamics."),
            "thm3": s("Thermodynamics",               "PC-ME301",  "Zeroth–Third laws, entropy, availability, steam tables, thermodynamic cycles."),
            "mfg3": s("Manufacturing Processes",      "PC-ME302",  "Casting, welding, forging, sheet metal, powder metallurgy, joining processes."),
        },
    },
    "4": {
        "name": "4th Semester",
        "info": "5 theory subjects | PYQ & organizers on Google Drive.",
        "subjects": {
            "mat4": s("Materials Engineering",           "ES-ME401", "Crystal structure, phase diagrams, heat treatment, mechanical properties, testing."),
            "at4":  s("Applied Thermodynamics",          "PC-ME401", "Combustion, Rankine & Brayton cycles, IC engines, refrigeration, compressors."),
            "fm4":  s("Fluid Mechanics & Fluid Machines","PC-ME402", "Fluid statics, Bernoulli, pipe flow, boundary layer, pumps, turbines, similarity."),
            "som4": s("Strength of Materials",           "PC-ME403", "Stress-strain, SFD/BMD, torsion, columns, deflection, springs, failure theories."),
            "met4": s("Metrology & Instrumentation",     "PC-ME404", "Linear/angular measurements, gauges, surface finish, CMM, transducers, data acquisition."),
        },
    },
    "5": {
        "name": "5th Semester",
        "info": "4 theory subjects | PYQ & organizers on Google Drive.",
        "subjects": {
            "ht5":  s("Heat Transfer",                     "PC-ME501", "Conduction, convection, radiation, heat exchangers, fins, boiling, condensation."),
            "sm5":  s("Solid Mechanics",                   "PC-ME502", "Stress-strain, energy methods, thick cylinders, rotating discs, contact stresses."),
            "ktm5": s("Kinematics & Theory of Machines",   "PC-ME503", "Mechanisms, velocity & acceleration analysis, cams, gears, gear trains, governors."),
            "etc5": s("Effective Technical Communication", "HM-HU501", "Technical writing, report writing, presentations, professional communication."),
        },
    },
    "6": {
        "name": "6th Semester",
        "info": "3 core + 10 elective options (choose 2 electives) | 2018-19 syllabus.",
        "subjects": {
            "mfgt6": s("Manufacturing Technology",   "PC-ME601", "Machining, tool geometry, CNC, NC programming, CAPP, non-conventional machining."),
            "dme6":  s("Design of Machine Elements", "PC-ME602", "Design of shafts, keys, gears, bearings, springs, clutches, brakes, welded joints."),
            "or6":   s("Operations Research",        "HM-HU601", "LPP, simplex, transportation, assignment, network analysis, CPM/PERT, queueing."),
            "e6a":   s("IC Engines & Gas Turbines  [Elec-I/II-A]",          "PE-ME601A/602A", "SI/CI engine cycles, fuel systems, supercharging, emissions, gas turbine cycles."),
            "e6b":   {
                "name": "Refrigeration & Air Conditioning  [Elec-I/II-B]",
                "code": "PE-ME601B/602B",
                "description": "Vapour compression/absorption cycles, psychrometry, cooling load, AC systems.",
                "resources": {
                    "pyq": [
                        {"title": "📂 PYQ — Google Drive", "url": DR38, "description": "Previous year question papers on Drive"},
                    ],
                    "books": [
                        {"title": "📗 Refrigeration & Air Conditioning – CP Arora (3rd Ed.)", "url": "https://drive.google.com/file/d/1iK0E6Meo1QUQxjWToSP0XBRh_JQ-wNhd/view?usp=sharing", "description": "Google Drive Book Link"},
                        {"title": "🚧 Direct Book PDF Links", "url": CS},
                    ],
                    "organizers": [
                        {"title": "📋 Organizer / Handouts — Google Drive", "url": DR38, "description": "Organized study materials & handouts"},
                    ],
                },
            },
            "e6c":   s("Turbo Machinery  [Elec-I/II-C]",                    "PE-ME601C/602C", "Centrifugal & axial flow compressors, turbines, velocity triangles, cavitation."),
            "e6d":   s("Fluid Power Control  [Elec-I/II-D]",                "PE-ME601D/602D", "Hydraulic & pneumatic systems, control valves, actuators, servo systems."),
            "e6e":   s("Advanced Fluid Mechanics  [Elec-I/II-E]",           "PE-ME601E/602E", "Navier-Stokes equations, turbulence, compressible flow, boundary layer theory."),
            "e6f":   s("Composite Materials  [Elec-I/II-F]",                "PE-ME601F/602F", "Fibre-reinforced composites, laminates, failure criteria, manufacturing methods."),
            "e6g":   s("Mechatronics  [Elec-I/II-G]",                       "PE-ME601G/602G", "Sensors, actuators, PLCs, microcontrollers, motion control, embedded systems."),
            "e6h":   s("Robotics  [Elec-I/II-H]",                           "PE-ME601H/602H", "Robot kinematics, dynamics, trajectory planning, programming, applications."),
            "e6i":   s("Material Handling  [Elec-I/II-I]",                  "PE-ME601I/602I", "Conveyors, cranes, AGVs, storage systems, material flow analysis."),
            "e6j":   s("Principles & Practices of Management  [Elec-I/II-J]","PE-ME601J/602J","Management functions, planning, organizing, HRM, industrial relations."),
        },
    },
    "7": {
        "name": "7th Semester",
        "info": "2 core + 10 PE options (choose 2) + 9 OE options (choose 1) | 2018-19.",
        "subjects": {
            "amt7":  s("Advanced Manufacturing Technology","PC-ME701", "Lean mfg, JIT, automation, robotics, rapid prototyping, Industry 4.0, MEMS."),
            "eco7":  s("Economics for Engineers",          "HM-HU701", "Engineering economics, depreciation, BEP, NPV, IRR, project evaluation."),
            "e7a":   s("Automobile Engineering  [PE-III/IV-A]",            "PE-ME701A/702A", "Vehicle dynamics, transmission, braking, steering, suspension, EV fundamentals."),
            "e7b":   s("Gas Dynamics & Jet Propulsion  [PE-III/IV-B]",     "PE-ME701B/702B", "Compressible flow, normal & oblique shocks, nozzles, ramjet, turbojet engines."),
            "e7c":   s("Computational Fluid Dynamics  [PE-III/IV-C]",      "PE-ME701C/702C", "FDM/FVM/FEM for fluid flow, turbulence modelling, CFD software applications."),
            "e7d":   s("Atmospheric Fluid Dynamics  [PE-III/IV-D]",        "PE-ME701D/702D", "Atmospheric boundary layer, wind loads, environmental fluid mechanics."),
            "e7e":   s("Selection & Testing of Materials  [PE-III/IV-E]",  "PE-ME701E/702E", "Material selection methodology, destructive & non-destructive testing methods."),
            "e7f":   s("Mechanical Vibration  [PE-III/IV-F]",              "PE-ME701F/702F", "Free & forced vibrations, damping, MDOF systems, vibration measurement & control."),
            "e7g":   s("Finite Element Analysis  [PE-III/IV-G]",           "PE-ME701G/702G", "FEM theory, 1D/2D/3D elements, meshing, boundary conditions, FEA software."),
            "e7h":   s("Advanced Welding Technology  [PE-III/IV-H]",       "PE-ME701H/702H", "Advanced welding processes, metallurgy of welds, NDT, robotic welding, codes."),
            "e7i":   s("Quantity Production Methods  [PE-III/IV-I]",       "PE-ME701I/702I", "Mass production, jigs & fixtures, transfer lines, group technology, cellular mfg."),
            "e7j":   s("CAD / CAM  [PE-III/IV-J]",                         "PE-ME701J/702J", "CAD modelling, CAM, CNC programming, CAPP, FEM in design, reverse engineering."),
            "oe7a":  s("Industrial Engineering  [OE-I-A]",                 "OE-ME701A", "Work study, method study, work measurement, production planning & control."),
            "oe7b":  s("Project Management  [OE-I-B]",                     "OE-ME701B", "Project lifecycle, CPM, PERT, resource allocation, risk management, MS Project."),
            "oe7c":  s("Product Design & Development  [OE-I-C]",           "OE-ME701C", "Product development process, QFD, DFMA, prototyping, product lifecycle."),
            "oe7d":  s("Non-conventional Energy Sources  [OE-I-D]",        "OE-ME701D", "Solar, wind, geothermal, tidal, biomass energy — principles & applications."),
            "oe7e":  s("Biomechanics & Biomaterials  [OE-I-E]",            "OE-ME701E", "Mechanics of biological systems, implant design, biocompatibility, prosthetics."),
            "oe7f":  s("Computational Methods in Engineering  [OE-I-F]",   "OE-ME701F", "Numerical methods, finite differences, optimization, MATLAB/Python applications."),
            "oe7g":  s("Artificial Intelligence (AI)  [OE-I-G]",           "OE-ME701G", "Search algorithms, knowledge representation, expert systems, AI in engineering."),
            "oe7h":  s("Machine Learning  [OE-I-H]",                       "OE-ME701H", "Supervised/unsupervised learning, neural networks, ML for engineering problems."),
            "oe7i":  s("Water Resource Engineering  [OE-I-I]",             "OE-ME701I", "Hydrology, irrigation, dams, water supply & treatment, flood management."),
        },
    },
    "8": {
        "name": "8th Semester",
        "info": "9 PE options (choose 2) + 13 OE options (choose 2) | 2018-19 syllabus.",
        "subjects": {
            "e8a":  s("Analysis & Performance of Fluid Machines  [PE-V/VI-A]","PE-ME801A/802A", "Performance testing of pumps, turbines, compressors; characteristic curves, CFD."),
            "e8b":  s("Power Plant Engineering  [PE-V/VI-B]",               "PE-ME801B/802B", "Thermal, hydro, nuclear, solar, wind power plants; economics & environmental impact."),
            "e8c":  s("Cryogenics  [PE-V/VI-C]",                            "PE-ME801C/802C", "Low temperature engineering, cryogenic fluids, insulation, applications in space."),
            "e8d":  s("Introduction to Wind Engineering  [PE-V/VI-D]",      "PE-ME801D/802D", "Wind loads on structures, wind energy, VAWT/HAWT design, site assessment."),
            "e8e":  s("Tribology  [PE-V/VI-E]",                             "PE-ME801E/802E", "Friction, wear, lubrication theory, bearing design, surface engineering."),
            "e8f":  s("3D Printing & Design  [PE-V/VI-F]",                  "PE-ME801F/802F", "FDM, SLA, SLS, bio-printing, design for additive manufacturing, post-processing."),
            "e8g":  s("Micro & Nano Manufacturing  [PE-V/VI-G]",            "PE-ME801G/802G", "MEMS, photolithography, micro-EDM, nano-fabrication, surface nano-engineering."),
            "e8h":  s("Process Planning & Cost Estimation  [PE-V/VI-H]",    "PE-ME801H/802H", "Process planning, CAPP, cost estimation methods, value engineering, costing."),
            "e8i":  s("Maintenance Engineering  [PE-V/VI-I]",               "PE-ME801I/802I", "Preventive, predictive & condition-based maintenance, FMEA, reliability engineering."),
            "oe8a": s("Total Quality Management  [OE-II/III-A]",            "OE-ME801A/802A", "TQM principles, Six Sigma, SPC, ISO standards, quality tools & techniques."),
            "oe8b": s("Entrepreneurship Development  [OE-II/III-B]",        "OE-ME801B/802B", "Entrepreneurship, business plan, startup ecosystem, funding, IPR basics."),
            "oe8c": s("Safety & Occupational Health  [OE-II/III-C]",        "OE-ME801C/802C", "Industrial safety, hazard identification, OSHA standards, ergonomics, fire safety."),
            "oe8d": s("Industrial Pollution & Control  [OE-II/III-D]",      "OE-ME801D/802D", "Air/water/noise pollution, ETP, EIA, environmental management systems."),
            "oe8e": s("Energy Conservation & Management  [OE-II/III-E]",    "OE-ME801E/802E", "Energy auditing, demand-side management, energy-efficient systems & policy."),
            "oe8f": s("Waste to Energy  [OE-II/III-F]",                     "OE-ME801F/802F", "Biomass, biogas, incineration, landfill gas, WTE technologies & economics."),
            "oe8g": s("Automation & Control  [OE-II/III-G]",                "OE-ME801G/802G", "Control systems, PLC, SCADA, DCS, industrial automation & process control."),
            "oe8h": s("Internet of Things (IoT)  [OE-II/III-H]",            "OE-ME801H/802H", "IoT architecture, sensors, protocols, cloud computing, industrial IoT applications."),
            "oe8i": s("Block Chain  [OE-II/III-I]",                         "OE-ME801I/802I", "Blockchain fundamentals, smart contracts, DeFi, supply chain & industrial use."),
            "oe8j": s("Cyber Security  [OE-II/III-J]",                      "OE-ME801J/802J", "Network security, cryptography, cyber threats, industrial control system security."),
            "oe8k": s("Quantum Computing  [OE-II/III-K]",                   "OE-ME801K/802K", "Quantum mechanics basics, qubits, quantum gates, algorithms, engineering applications."),
            "oe8l": s("Data Sciences  [OE-II/III-L]",                       "OE-ME801L/802L", "Data analysis, visualization, regression, classification, engineering analytics."),
            "oe8m": s("Virtual Reality (VR)  [OE-II/III-M]",                "OE-ME801M/802M", "VR/AR/MR technologies, simulation, design review, training & manufacturing apps."),
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# KEYBOARDS
# ─────────────────────────────────────────────────────────────────────────────

def main_menu_kb():
    sems = list(MATERIALS.items())
    rows = []
    for i in range(0, len(sems), 2):
        rows.append([InlineKeyboardButton(f"📚 {d['name']}", callback_data=f"sem|{n}")
                     for n, d in sems[i:i+2]])
    rows.append([InlineKeyboardButton("🎯 GATE / ESE / JE Prep", callback_data="gate")])
    rows.append([InlineKeyboardButton("ℹ️ About Bot",             callback_data="about")])
    return InlineKeyboardMarkup(rows)

def sem_kb(sem_num):
    subjects = MATERIALS.get(sem_num, {}).get("subjects", {})
    rows = [[InlineKeyboardButton(f"📖 {s['name']}", callback_data=f"sub|{sem_num}|{sid}")]
            for sid, s in subjects.items()]
    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main")])
    return InlineKeyboardMarkup(rows)

def sub_kb(sem_num, sub_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Lectures",             callback_data=f"res|{sem_num}|{sub_id}|lectures")],
        [InlineKeyboardButton("📝 Notes / PDFs",        callback_data=f"res|{sem_num}|{sub_id}|notes")],
        [InlineKeyboardButton("📚 Reference Books",     callback_data=f"res|{sem_num}|{sub_id}|books")],
        [InlineKeyboardButton("❓ PYQs / Practice Qs", callback_data=f"res|{sem_num}|{sub_id}|pyq")],
        [InlineKeyboardButton("📋 Organizers",          callback_data=f"res|{sem_num}|{sub_id}|organizers")],
        [InlineKeyboardButton("🔙 Semester", callback_data=f"sem|{sem_num}"),
         InlineKeyboardButton("🏠 Menu",     callback_data="main")],
    ])

def back_kb(sem_num, sub_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Subject", callback_data=f"sub|{sem_num}|{sub_id}")],
        [InlineKeyboardButton("📚 Semester",         callback_data=f"sem|{sem_num}"),
         InlineKeyboardButton("🏠 Menu",             callback_data="main")],
    ])

# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    not_joined = await check_membership(user_id, context)
    if not_joined:
        names = "\n".join("• " + ch["title"] for ch in not_joined)
        await update.message.reply_text(
            "👋 *Welcome!*\n\n"
            "⚠️ To use this bot, please join our channels first:\n\n"
            + names +
            "\n\nAfter joining, tap the button below 👇",
            parse_mode="Markdown",
            reply_markup=join_keyboard(not_joined)
        )
        return
    await update.message.reply_text(WELCOME, parse_mode="Markdown", reply_markup=main_menu_kb())

async def _enforce_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    not_joined = await check_membership(user_id, context)
    if not_joined:
        names = "\n".join("• " + ch["title"] for ch in not_joined)
        await update.message.reply_text(
            "⚠️ *Please join our channels to continue:*\n\n" + names +
            "\n\nTap the button below after joining 👇",
            parse_mode="Markdown",
            reply_markup=join_keyboard(not_joined)
        )
        return True
    return False

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _enforce_join(update, context):
        return
    total = sum(len(s["subjects"]) for s in MATERIALS.values())
    await update.message.reply_text(
        "📖 *How to use this bot:*\n\n"
        "1️⃣ Tap your *Semester*\n"
        "2️⃣ Choose a *Subject*\n"
        "3️⃣ Pick a *Resource Type*\n\n"
        "📄 *Notes* → PDF files sent directly to chat\n"
        "🎬 *Lectures* → YouTube playlist links\n"
        "📂 *PYQs & Organizers* → Google Drive\n"
        "🚧 *Coming Soon* = material being added\n\n"
        f"📊 Total theory subjects covered: *{total}*\n\n"
        "Use /start for the main menu.",
        parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pts = q.data.split("|")
    act = pts[0]

    # ── Force join check ──────────────────────────────────────────────────────
    user_id = update.effective_user.id
    not_joined = await check_membership(user_id, context)

    if act == "check_join":
        if not_joined:
            names = "\n".join("• " + ch["title"] for ch in not_joined)
            await q.edit_message_text(
                "❌ *You haven\'t joined all channels yet!*\n\n"
                "Please join:\n" + names +
                "\n\nTap *I Have Joined* after joining 👇",
                parse_mode="Markdown",
                reply_markup=join_keyboard(not_joined)
            )
        else:
            await q.edit_message_text(WELCOME, parse_mode="Markdown", reply_markup=main_menu_kb())
        return

    if not_joined:
        names = "\n".join("• " + ch["title"] for ch in not_joined)
        await q.edit_message_text(
            "⚠️ *Please join our channels to continue:*\n\n" + names +
            "\n\nTap the button below after joining 👇",
            parse_mode="Markdown",
            reply_markup=join_keyboard(not_joined)
        )
        return
    # ─────────────────────────────────────────────────────────────────────────

    if act == "main":
        await q.edit_message_text(WELCOME, parse_mode="Markdown", reply_markup=main_menu_kb())

    elif act == "gate":
        await q.edit_message_text(
            "🎯 *For GATE, ESE & JE Aspirants*\n\n"
            "Want premium study materials, handwritten notes, video lectures "
            "& daily practice questions for competitive exams?\n\n"
            "👉 Join our dedicated channel:\n"
            f"[🔗 Mechanical GATE / ESE / JE Notes 2027](https://t.me/mechanical_Gate_ese_je_notes2027)\n\n"
            "✅ Handwritten notes\n✅ Video lectures\n"
            "✅ Daily Practice Problems\n✅ Mock tests & solutions",
            parse_mode="Markdown", disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📲 Join GATE / ESE / JE Channel", url="https://t.me/mechanical_Gate_ese_je_notes2027")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main")],
            ]))

    elif act == "about":
        total = sum(len(s["subjects"]) for s in MATERIALS.values())
        await q.edit_message_text(
            "ℹ️ *About This Bot*\n\n"
            "🏫 *University:* MAKAUT, West Bengal\n"
            "🔧 *Department:* Mechanical Engineering\n"
            "📅 *Syllabus:* 2018-19\n"
            "📚 *Semesters:* 1st to 8th\n"
            f"📖 *Total Subjects (incl. all electives):* {total}\n\n"
            f"📂 [PYQ & Organizers — Drive]({DR38})\n"
            f"🎯 [GATE / ESE / JE Channel](https://t.me/mechanical_Gate_ese_je_notes2027)",
            parse_mode="Markdown", disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main")]]))

    elif act == "sem" and len(pts) == 2:
        sem_num = pts[1]
        sem = MATERIALS.get(sem_num)
        if not sem:
            await q.edit_message_text("❌ Semester not found."); return
        await q.edit_message_text(
            f"📚 *{sem['name']}*\n\n"
            f"📋 Subjects listed: *{len(sem['subjects'])}*\n"
            f"_{sem['info']}_\n\n"
            "👇 Select a subject:",
            parse_mode="Markdown", reply_markup=sem_kb(sem_num))

    elif act == "sub" and len(pts) == 3:
        sem_num, sub_id = pts[1], pts[2]
        sub = MATERIALS.get(sem_num, {}).get("subjects", {}).get(sub_id)
        if not sub:
            await q.edit_message_text("❌ Subject not found."); return
        await q.edit_message_text(
            f"📖 *{sub['name']}*\n"
            f"🆔 Code: `{sub.get('code','N/A')}`\n\n"
            f"📌 _{sub.get('description','')}_\n\n"
            "Choose a resource type 👇",
            parse_mode="Markdown", reply_markup=sub_kb(sem_num, sub_id))

    elif act == "res" and len(pts) == 4:
        sem_num, sub_id, res_type = pts[1], pts[2], pts[3]
        sub = MATERIALS.get(sem_num, {}).get("subjects", {}).get(sub_id)
        if not sub:
            await q.edit_message_text("❌ Subject not found."); return

        # ── NOTES: show file selection buttons ─────────────────────────────────
        if res_type == "notes":
            all_note_pdfs = (
                [p for p in NOTES_PDF.get(sub_id, [])         if p.get("msg_id", 0) != 0] +
                [p for p in NOTES_PDF_CHANNEL.get(sub_id, []) if p.get("msg_id", 0) != 0]
            )
            drive_link = NOTES_DRIVE.get(sub_id)

            if all_note_pdfs:
                # Build a button for each PDF
                buttons = []
                for pdf in all_note_pdfs:
                    cap = pdf.get("caption", "PDF")
                    # Keep button text under ~50 chars to avoid truncation
                    short_cap = cap if len(cap) <= 50 else cap[:47] + "..."
                    cb_data = f"note_file|{sem_num}|{sub_id}|{pdf['msg_id']}"
                    buttons.append([InlineKeyboardButton(short_cap, callback_data=cb_data)])

                # Add back/menu row
                buttons.append([
                    InlineKeyboardButton("🔙 Back to Subject", callback_data=f"sub|{sem_num}|{sub_id}"),
                    InlineKeyboardButton("🏠 Menu", callback_data="main")
                ])
                await q.edit_message_text(
                    f"📝 *{sub['name']}* — Notes / PDFs\n\n"
                    f"📚 Choose a file to receive 👇",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(buttons))

            elif drive_link:
                await q.edit_message_text(
                    f"📝 *{sub['name']}* — Notes / PDFs\n\n"
                    f"📁 Notes are available on Google Drive:\n"
                    f"[🔗 Open Notes Folder]({drive_link})",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📁 Open Notes on Drive", url=drive_link)],
                        [InlineKeyboardButton("🔙 Back to Subject", callback_data=f"sub|{sem_num}|{sub_id}")],
                        [InlineKeyboardButton("📚 Semester", callback_data=f"sem|{sem_num}"),
                         InlineKeyboardButton("🏠 Menu",     callback_data="main")],
                    ]))

            else:
                await q.edit_message_text(
                    f"📝 *{sub['name']}* — Notes / PDFs\n\n"
                    "🚧 *Coming Soon!*\n"
                    "_PDFs for this subject will be uploaded shortly._",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup=back_kb(sem_num, sub_id))

        # ── LECTURES: copy from Storage Channel or show YouTube ─────────────
        elif res_type == "lectures":
            tg_videos = LECTURE_VIDEOS.get(sub_id, [])
            yt_links  = YOUTUBE_LINKS.get(sub_id, [])
            tg_videos = [v for v in tg_videos if v.get("msg_id", 0) != 0]

            if tg_videos:
                await q.edit_message_text(
                    f"📤 *Sending lecture videos for {sub['name']}…*\n"
                    f"_{len(tg_videos)} video(s) incoming below_ 👇\n"
                    "_⚠️ Large files — each appears instantly from our channel storage._",
                    parse_mode="Markdown")
                chat_id = q.message.chat_id
                for idx, vid in enumerate(tg_videos, 1):
                    caption      = vid.get("caption", f"{sub['name']} – Lecture {idx}")
                    caption_full = f"🎬 *{caption}*\n_{sub['name']} | {sub.get('code','')}_"
                    try:
                        await context.bot.copy_message(
                            chat_id=chat_id,
                            from_chat_id=STORAGE_CHANNEL_ID,
                            message_id=vid["msg_id"],
                            caption=caption_full,
                            parse_mode="Markdown")
                    except Exception as e:
                        logger.error(f"Failed to copy video for {sub_id} msg_id={vid.get('msg_id')}: {e}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⚠️ Could not send *{caption}*.\n_Ensure the bot is Admin in the Storage Channel._",
                            parse_mode="Markdown")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ All {len(tg_videos)} lecture video(s) sent for *{sub['name']}*!",
                    parse_mode="Markdown",
                    reply_markup=back_kb(sem_num, sub_id))

            elif yt_links:
                lines = [f"▶️ [{item['title']}]({item['url']})" for item in yt_links]
                body  = "\n\n".join(lines)
                await q.edit_message_text(
                    f"🎬 *{sub['name']}*\nYouTube Lectures\n\n{body}",
                    parse_mode="Markdown",
                    reply_markup=back_kb(sem_num, sub_id),
                    disable_web_page_preview=True)

            else:
                await q.edit_message_text(
                    f"🎬 *{sub['name']}* — Lectures\n\n"
                    "🚧 *Coming Soon!*\n"
                    "_Lecture videos & playlists will be added shortly._",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup=back_kb(sem_num, sub_id))

        # ── BOOKS / PYQ / ORGANIZERS ───────────────────────────────────────
        else:
            items  = sub.get("resources", {}).get(res_type, [])
            labels = {"books":     "📚 Reference Books",
                      "pyq":       "❓ PYQs / Practice Questions",
                      "organizers":"📋 Organizers / Handouts"}
            icons  = {"books":"📗", "pyq":"📝", "organizers":"📋"}
            label  = labels.get(res_type, res_type.title())
            icon   = icons.get(res_type, "🔗")

            if res_type == "books":
                all_book_pdfs = (
                    [b for b in BOOKS_PDF.get(sub_id, [])         if b.get("msg_id", 0) != 0] +
                    [b for b in BOOKS_PDF_CHANNEL.get(sub_id, []) if b.get("msg_id", 0) != 0]
                )
                if all_book_pdfs:
                    total = len(all_book_pdfs)
                    await q.edit_message_text(
                        f"📤 *Sending reference books for {sub['name']}…*\n"
                        f"_{total} book(s) incoming below_ 👇",
                        parse_mode="Markdown")
                    chat_id = q.message.chat_id
                    for idx, book in enumerate(all_book_pdfs, 1):
                        caption      = book.get("caption", f"{sub['name']} – Book {idx}")
                        caption_full = f"📗 *{caption}*\n_{sub['name']} | {sub.get('code','')}_"
                        try:
                            await context.bot.copy_message(
                                chat_id=chat_id,
                                from_chat_id=STORAGE_CHANNEL_ID,
                                message_id=book["msg_id"],
                                caption=caption_full,
                                parse_mode="Markdown")
                        except Exception as e:
                            logger.error(f"Failed to copy book for {sub_id} msg_id={book.get('msg_id')}: {e}")
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"⚠️ Could not send *{caption}*.\n_Ensure the bot is Admin in the Storage Channel._",
                                parse_mode="Markdown")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ All {total} book(s) sent for *{sub['name']}*!",
                        parse_mode="Markdown",
                        reply_markup=back_kb(sem_num, sub_id))
                    return

            if not items:
                body = "🚧 *Coming Soon!*\n_This resource will be added shortly._"
            else:
                lines = []
                for idx, item in enumerate(items, 1):
                    title = item.get("title", f"Resource {idx}")
                    url   = item.get("url", "")
                    desc  = item.get("description", "")
                    if url in ("", CS):
                        lines.append(f"🚧 *{title}*\n   _Coming Soon_")
                    else:
                        entry = f"{icon} [{title}]({url})"
                        if desc: entry += f"\n   _{desc}_"
                        lines.append(entry)
                body = "\n\n".join(lines)

            await q.edit_message_text(
                f"*{sub['name']}*\n{label}\n\n{body}",
                parse_mode="Markdown",
                reply_markup=back_kb(sem_num, sub_id),
                disable_web_page_preview=True)

    # ── NOTE FILE BUTTON HANDLER ───────────────────────────────────────────
    elif act == "note_file" and len(pts) == 4:
        sem_num, sub_id, msg_id_str = pts[1], pts[2], pts[3]
        try:
            msg_id = int(msg_id_str)
        except ValueError:
            await q.answer("❌ Invalid file ID."); return

        sub = MATERIALS.get(sem_num, {}).get("subjects", {}).get(sub_id)
        if not sub:
            await q.answer("❌ Subject not found."); return

        await q.answer("📄 Sending file...")
        chat_id = q.message.chat_id
        try:
            # We don't have the original caption stored here, but we can infer from the dictionaries.
            # Just send with a generic caption or look it up.
            # We'll search for the msg_id in the merged list.
            caption = None
            for pdf in NOTES_PDF.get(sub_id, []) + NOTES_PDF_CHANNEL.get(sub_id, []):
                if pdf.get("msg_id") == msg_id:
                    caption = pdf.get("caption", "Notes PDF")
                    break
            caption_full = f"📄 *{caption}*\n_{sub['name']} | {sub.get('code','')}_"
            await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=STORAGE_CHANNEL_ID,
                message_id=msg_id,
                caption=caption_full,
                parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to copy note file msg_id={msg_id}: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="⚠️ Could not send that file. Ensure the bot is Admin in the Storage Channel.",
                parse_mode="Markdown")

    else:
        await q.edit_message_text("❓ Unknown action. Use /start.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main")]]))

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _enforce_join(update, context):
        return
    await update.message.reply_text("❓ Unknown command. Use /start or /help.")

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await _enforce_join(update, context):
        return
    await update.message.reply_text(
        "👋 Use /start to open the menu or /help for instructions.",
        reply_markup=main_menu_kb()
    )

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    Thread(target=_start_http, daemon=True).start()
    logger.info(f"🌐 Flask keep-alive server started on port {os.environ.get('PORT', 8080)}")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    logger.info("🤖 MAKAUT ME Bot started.")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
