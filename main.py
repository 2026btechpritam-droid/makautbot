"""
MAKAUT Mechanical Engineering Study Bot
2018-19 Syllabus | Semesters 1–8 | All Theory + All Electives
python-telegram-bot v21 | @GURU_HOSTING_TGBOT compatible

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADMIN GUIDE — HOW TO ADD CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 ADD PDF NOTES  →  NOTES_PDF dict  (below)
   • Get file_id: send PDF to bot → forward to @getidsbot → copy file_id
   • Each entry: {"file_id": "BQACAgI...", "caption": "Unit 1 – Topic"}
   • For subjects with only a Drive folder → add to NOTES_DRIVE dict

🎬 ADD LECTURE VIDEOS (large, >50 MB) — CHANNEL STORAGE METHOD
   • Upload the video to your PRIVATE Storage Channel (as a human, not the bot).
   • Right-click → "Copy Post Link" → https://t.me/c/CHANNEL_ID/MSG_ID
   • The last number is the msg_id. Set STORAGE_CHANNEL_ID at the top of the file.
   • Each entry in LECTURE_VIDEOS: {"msg_id": 45, "caption": "Subject – Unit X Lec Y"}
   • The bot uses copy_message() — instant delivery, zero bandwidth, up to 2 GB.

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
# 1. Create a PRIVATE Telegram channel and add this bot as Admin (Read Messages).
# 2. Upload lecture videos there manually (up to 2 GB each).
# 3. Right-click a video → "Copy Post Link" → https://t.me/c/XXXXXXXXXX/YY
#    • XXXXXXXXXX  → your channel ID  (prepend -100 → e.g. -1001234567890)
#    • YY          → the message_id for that video
# 4. Set STORAGE_CHANNEL_ID below and update LECTURE_VIDEOS to use msg_id keys.
STORAGE_CHANNEL_ID = int(os.environ.get("STORAGE_CHANNEL_ID", "-1003810204452"))

# ── Shared Links ───────────────────────────────────────────────────────────────
TG       = "https://t.me/+z3X6dsDlONs4OWQ1"
GATE_CH  = "https://t.me/mechanical_Gate_ese_je_notes2027"
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
        "verify": False,  # YouTube cannot be verified via Telegram API
    },
]

async def check_membership(user_id: int, context) -> list:
    """Returns list of channels the user has NOT joined."""
    not_joined = []
    for ch in FORCE_JOIN_CHANNELS:
        if not ch.get("verify", True):
            continue  # e.g. YouTube — cannot verify via Telegram API
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
            # Bot lost admin / chat unreachable → fail open so users aren't locked out
            if any(s in msg for s in ("member list is inaccessible",
                                      "chat not found",
                                      "bot is not a member",
                                      "bot was kicked",
                                      "chat_admin_required")):
                logging.warning("Skipping force-join check for @%s: %s", ch["username"], e)
                continue
            # Otherwise (e.g., user-specific lookup error) treat as not joined
            not_joined.append(ch)
    return not_joined

def join_keyboard(not_joined: list):
    """Keyboard with join buttons + a check button."""
    rows = [[InlineKeyboardButton("➕ Join " + ch["title"], url=ch["url"])]
            for ch in not_joined]
    rows.append([InlineKeyboardButton("✅ I Have Joined — Check Again", callback_data="check_join")])
    return InlineKeyboardMarkup(rows)
# ─────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# 📂  NOTES PDF  ——  Telegram file_ids, grouped unit-wise where available
# ══════════════════════════════════════════════════════════════════════════════
NOTES_PDF = {

    # ── Semester 1 ── (paste file_ids when ready)
    # "ph1":  [{"file_id": "PASTE_HERE", "caption": "Physics I – Notes Part 1"}],
    # "m1b":  [{"file_id": "PASTE_HERE", "caption": "Mathematics IB – Notes Part 1"}],
    # "bee1": [{"file_id": "PASTE_HERE", "caption": "Basic Electrical Engineering – Notes Part 1"}],

    # ── Semester 2 ──
    "ch2": [
        # Unit 1
        {"file_id": "BQACAgUAAxkBAAFHqL9p5l-d9KWjcxXRRRE_SHKIGxYrsAACuR0AAnAxMVZs_2F_KnvGETsE", "caption": "Chemistry I – Unit 1 Hand Written Notes"},
        # Unit 2
        {"file_id": "BQACAgUAAxkBAAFHqMBp5l-dh1CS_90lsabEEh7DQTJlygACuh0AAnAxMVYWzmuJvA2dUTsE", "caption": "Chemistry I – Unit 2 Combined Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqMFp5l-d0LaCM0njaESDBtJG2wSGdQACux0AAnAxMVZY7vgeHnRk6DsE", "caption": "Chemistry I – Unit 2 Hand Written Notes (One Shot)"},
        # Unit 3
        {"file_id": "BQACAgUAAxkBAAFHqL1p5l-dhONzctfXtUU_00nHzfQ0IQACtR0AAnAxMVZSpeWeJ5W8LDsE", "caption": "Chemistry I – Unit 3 Combined Notes"},
        # Unit 4
        {"file_id": "BQACAgUAAxkBAAFHqLxp5l-dfGdx4PSQUgxzByQVKEvZ-gACrR0AAnAxMVZTL31whIjsVTsE", "caption": "Chemistry I – Unit 4 Hand Written Notes"},
        # Unit 5
        {"file_id": "BQACAgUAAxkBAAFHqLtp5l-dcPq4pXGJpO5sbD78BAeslwACqR0AAnAxMVYXixVpZ5NKRjsE", "caption": "Chemistry I – Unit 5 Hand Written Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqL5p5l-dsNGx-_HfeX2OuJSF00oIawACuB0AAnAxMVYAAdzYu_RwVAY7BA", "caption": "Chemistry I – Unit 5 Hand Written Notes (Part 2)"},
    ],
    # "m2b": [{"file_id": "PASTE_HERE", "caption": "Mathematics IIB – Notes Part 1"}],
    "pps": [
        # Unit 1
        {"file_id": "BQACAgUAAxkBAAFHqMdp5l-dNCdwG_kCI2nkF9qPcf270QACSCUAAnAxOVaBHoDdC_lsnTsE", "caption": "Programming for Problem Solving – Unit 1 Hand Written Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqMZp5l-dqL0AASuuvIDRzt9KgYDYbIoAAkclAAJwMTlWiY2cnjIPZ8g7BA", "caption": "Programming for Problem Solving – Unit 1 Combined Notes"},
        # Unit 2
        {"file_id": "BQACAgUAAxkBAAFHqMhp5l-dXuvDTqB11Pvi2eyxWEJpigACSSUAAnAxOVb7BHMCp7CIFjsE", "caption": "Programming for Problem Solving – Unit 2 Combined Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqMtp5l-deDGfBMbqzxNcaLTAx7VA4wACTCUAAnAxOVYqOw0K-_62-zsE", "caption": "Programming for Problem Solving – Unit 2 Hand Written Notes"},
        # Unit 3
        {"file_id": "BQACAgUAAxkBAAFHqMlp5l-dKEZxS8RKA2S-iuLqMlkR9gACSiUAAnAxOVYi3go5fleUmzsE", "caption": "Programming for Problem Solving – Unit 3 Hand Written Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqMpp5l-ddSVxmVzh4-GaGjnT5PCHIgACSyUAAnAxOVYvOe52pLb7bzsE", "caption": "Programming for Problem Solving – Unit 3 Combined Notes"},
        # Unit 4
        {"file_id": "BQACAgUAAxkBAAFHqMVp5l-d3X6JBx4TKcZDMPErif56RgACRiUAAnAxOVahLqJv5fUfATsE", "caption": "Programming for Problem Solving – Unit 4 Hand Written Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqM9p5l-d_RMrnn7VgLu6NB_DkagIuQACUCUAAnAxOVZeGnVp1lvcpzsE", "caption": "Programming for Problem Solving – Unit 4 Combined Notes"},
        # Unit 5
        {"file_id": "BQACAgUAAxkBAAFHqNNp5l-d0mrmWOxh0yjBJt-S5z_NBAACVCUAAnAxOVaOJnKbRyeCMzsE", "caption": "Programming for Problem Solving – Unit 5 Combined Notes"},
        # Important Questions
        {"file_id": "BQACAgUAAxkBAAFHqMxp5l-dKnEw1DJ7daMGtEtr_BlYzgACTSUAAnAxOVbSAWiCUWXx9DsE", "caption": "Programming for Problem Solving – Most Important Questions"},
    ],
    # "eng": [{"file_id": "PASTE_HERE", "caption": "English – Notes Part 1"}],

    # ── Semester 3 ── (paste file_ids when ready)
    # "m3":   [{"file_id": "PASTE_HERE", "caption": "Mathematics III – Notes Part 1"}],
    # "bio":  [{"file_id": "PASTE_HERE", "caption": "Biology – Notes Part 1"}],
    # "ece3": [{"file_id": "PASTE_HERE", "caption": "Basic Electronics – Notes Part 1"}],
    # "em3":  [{"file_id": "PASTE_HERE", "caption": "Engineering Mechanics – Notes Part 1"}],
    # "thm3": [{"file_id": "PASTE_HERE", "caption": "Thermodynamics – Notes Part 1"}],
    # "mfg3": [{"file_id": "PASTE_HERE", "caption": "Manufacturing Processes – Notes Part 1"}],

    # ── Semester 4 ──
    # "mat4": [{"file_id": "PASTE_HERE", "caption": "Materials Engineering – Notes Part 1"}],

    "at4": [
        # Unit 1
        {"file_id": "BQACAgUAAxkBAAFHqPxp5l-dQpcuKMCWpi86EN9gjrTVaAACgxoAAoLlSFb7wPkFzGxXYzsE", "caption": "Applied Thermodynamics – Unit 1 IMP Questions"},
        {"file_id": "BQACAgUAAxkBAAFHqP5p5l-dtDcTLqMp6AZHzOD6tasEgAAChRoAAoLlSFaACfQ1Xe7E8DsE", "caption": "Applied Thermodynamics – Unit 1 Lec 1"},
        {"file_id": "BQACAgUAAxkBAAFHqP9p5l-dvhKwgGAF6CPkzUp2tsUduAAChhoAAoLlSFZ6htMnCH3w-jsE", "caption": "Applied Thermodynamics – Unit 1 Lec 2"},
        {"file_id": "BQACAgUAAxkBAAFHqQABaeZfndLjQ6yKijqOnet-0bvituoAAocaAAKC5UhWiQZFhqryqGM7BA", "caption": "Applied Thermodynamics – Unit 1 Lec 3"},
        {"file_id": "BQACAgUAAxkBAAFHqQFp5l-d4IoFUbnwCm5UBp4zk1JNtwACiBoAAoLlSFZYkI4HldTEyzsE", "caption": "Applied Thermodynamics – Unit 1 Lec 4"},
        {"file_id": "BQACAgUAAxkBAAFHqQJp5l-dAzAJVKd5Tcy2NM2PFt1BYQACiRoAAoLlSFYDUwulU15z6DsE", "caption": "Applied Thermodynamics – Unit 1 Lec 5"},
        {"file_id": "BQACAgUAAxkBAAFHqQNp5l-dVK7a4r_AZlRPZ_pnHIaY6QACihoAAoLlSFZ0PoemhG0uAzsE", "caption": "Applied Thermodynamics – Unit 1 Lec 6"},
        {"file_id": "BQACAgUAAxkBAAFHqQRp5l-dFaQs-btso4bz9ttrO71tnAACixoAAoLlSFYTIUc5oikIojsE", "caption": "Applied Thermodynamics – Unit 1 Turbocharger & Supercharger (One Shot)"},
        # Unit 2
        {"file_id": "BQACAgUAAxkBAAFHqP1p5l-dhg_q6LInO4GXwizaud1r4wAChBoAAoLlSFai7zVzHUK40jsE", "caption": "Applied Thermodynamics – Unit 2 Combined Notes"},
        # Unit 3
        {"file_id": "BQACAgUAAxkBAAFHqQVp5l-d392eyqYqJsipOXm0xnx_GwACjBoAAoLlSFZGnfLWTJPe1zsE", "caption": "Applied Thermodynamics – Unit 3 Complete Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqQZp5l-dYO-9gdpzRE0aPkEYa6Wy3wACjRoAAoLlSFZem1rjQ60hfjsE", "caption": "Applied Thermodynamics – Unit 3 Boiler Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqQdp5l-dGspXYAl8vFvEgMkPDahDnwACjhoAAoLlSFaah4Jt_E6InjsE", "caption": "Applied Thermodynamics – Unit 3 Boiler Notes Part 1"},
        {"file_id": "BQACAgUAAxkBAAFHqQhp5l-d-Kk2ilQieY5N-c44D3Q2bAACjxoAAoLlSFZU6WB1XieurzsE", "caption": "Applied Thermodynamics – Unit 3 Boiler Part 2 Draught Notes"},
        # Unit 4
        {"file_id": "BQACAgUAAxkBAAFHqQlp5l-dMS85sQwXm-JsEqTlmtDTcgACkBoAAoLlSFbvu3teUxFpAAE7BA", "caption": "Applied Thermodynamics – Unit 4 Notes"},
        {"file_id": "BQACAgUAAxkBAAFHqQpp5l-dxYuQl3yDeseOlKa7MUbk2QACkRoAAoLlSFYSzRL51MdpEDsE", "caption": "Applied Thermodynamics – Unit 4 Steam Nozzle Numericals"},
        # Unit 5
        {"file_id": "BQACAgUAAxkBAAFHqXFp5l_0yVsI2Abhx7rThytIif-KCQACkhoAAoLlSFbMJ3fhXtPeyzsE", "caption": "Applied Thermodynamics – Unit 5 Lec 1"},
        {"file_id": "BQACAgUAAxkBAAFHqXJp5l_0FhUL2w5uzgQJ5fO93b0hhQACkxoAAoLlSFa-bDB0bi0a5DsE", "caption": "Applied Thermodynamics – Unit 5 Lec 3"},
        {"file_id": "BQACAgUAAxkBAAFHqXNp5l_0-kObgEUclW-tMWQx19yh3QAClBoAAoLlSFbxN1aOh5zjODsE", "caption": "Applied Thermodynamics – Unit 5 Lec 5"},
        {"file_id": "BQACAgUAAxkBAAFHqXRp5l_0gtjdC0UPLYjex6yUaVoRBwAClRoAAoLlSFaQ-OxFBT820DsE", "caption": "Applied Thermodynamics – Unit 5 Lec 6"},
        {"file_id": "BQACAgUAAxkBAAFHqXVp5l_0HZ6072MCGAuSkjWYKdBbPgAClhoAAoLlSFZU4g1oqh9AbTsE", "caption": "Applied Thermodynamics – Unit 5 Lec 7"},
        {"file_id": "BQACAgUAAxkBAAFHqXZp5l_0IooPYYlWnDlH37jD8bVANwAClxoAAoLlSFZJwdVKfeb00zsE", "caption": "Applied Thermodynamics – Unit 5 Jet Propulsion"},
    ],

    # "fm4": [{"file_id": "PASTE_HERE", "caption": "Fluid Mechanics – Notes Part 1"}],

    "som4": [
        {"file_id": "BQACAgUAAxkBAAFHp2hp5k4AAXaPY0fRmr7acERt3okuJcAAArcaAAKC5UhWHnkK27BI_Cg7BA", "caption": "Strength of Materials – Notes Part 1"},
        {"file_id":"BQACAgUAAxkBAAFHp2lp5k4AAc-ROnl7JTNU6lRFdUzWn4EAAiIbAAKC5UhW5L6hZB9bHCY7BA", "caption": "Strength of Materials – Notes Part 2"},
        {"file_id": "BQACAgUAAxkBAAFHp2pp5k4AAbXAWmggORZYoNc200HQSyEAAq8bAAKC5UhWngGkwXMHDyk7BA", "caption": "Strength of Materials – Notes Part 3"},
        {"file_id": "BQACAgUAAxkBAAFHp2tp5k4AAehIV9e2SLokPV3kEue6jbwAArAbAAKC5UhW2_ErOBtGgAc7BA","caption": "Strength of Materials – Notes Part 4"},
        {"file_id":"BQACAgUAAxkBAAFHp2xp5k4AAaa6LREwO06RP6jeUv6XNzgAArEbAAKC5UhWn9OlAhLtwbk7BA", "caption": "Strength of Materials – Notes Part 5"},
        {"file_id": "BQACAgUAAxkBAAFHp25p5k4AAVzmhN3x8ZWKBWNO14ylUcMAAlIcAAJn_pBW5UHYtNx3LJQ7BA",  "caption": "Strength of Materials – Notes Part 6"},
        {"file_id":"BQACAgUAAxkBAAFHp21p5k4AAc2xafrz7R5N-p8O_M867fgAAlEcAAJn_pBWQb0-K4UZoqg7BA","caption": "Strength of Materials – Notes Part 7"},
        {"file_id": "BQACAgUAAxkBAAFHp29p5k4AAX1EZy0V-Hl1uHC9ezlW6fIAAlMcAAJn_pBW8eXyUZOT2hg7BA", "caption": "Strength of Materials – Notes Part 8"},
        {"file_id": "BQACAgUAAxkBAAFHp21p5k4AAc2xafrz7R5N-p8O_M867fgAAlEcAAJn_pBWQb0-K4UZoqg7BA","caption": "Strength of Materials – Notes Part 9"},
    ],

    # met4 → Google Drive folder (see NOTES_DRIVE below)

    # ── Semester 5 ── (paste file_ids when ready)
    # "ht5":  [{"file_id": "PASTE_HERE", "caption": "Heat Transfer – Notes Part 1"}],
    # "sm5":  [{"file_id": "PASTE_HERE", "caption": "Solid Mechanics – Notes Part 1"}],
    # "ktm5": [{"file_id": "PASTE_HERE", "caption": "KTM – Notes Part 1"}],
    # "etc5": [{"file_id": "PASTE_HERE", "caption": "Technical Communication – Notes Part 1"}],

    # ── Semester 6 ──
    "e6b": [
        {"file_id": "BQACAgUAAxkBAAFHp0hp5kwjCukXK7Ru1T7K8_UNQA9b1gACDiAAAmf-mFbiblfk-ALBxzsE", "caption": "Refrigeration & Air Conditioning – Notes Part 1"},
        {"file_id": "BQACAgUAAxkBAAFHp0lp5kwjF3xSqNSlwbI0jIVVKs4WtgACESAAAmf-mFa4LcNW2SijajsE", "caption": "Refrigeration & Air Conditioning – Notes Part 2"},
        {"file_id": "BQACAgUAAxkBAAFHpzJp5ksPr6-dN53zieJCYxY7n5IP1QACEiAAAmf-mFaTl3UNlpwHQjsE", "caption": "Refrigeration & Air Conditioning – Notes Part 3"},
        {"file_id":"BQACAgUAAxkBAAFHp0pp5kwjqbtbu0mp5FWmsPQJY3RSUgACEyAAAmf-mFZL0QlMILeAtTsE", "caption": "Refrigeration & Air Conditioning – Notes Part 4"},
    ],
    # "mfgt6": [{"file_id": "PASTE_HERE", "caption": "Manufacturing Technology – Notes Part 1"}],
    # "dme6":  [{"file_id": "PASTE_HERE", "caption": "Design of Machine Elements – Notes Part 1"}],
    # "or6":   [{"file_id": "PASTE_HERE", "caption": "Operations Research – Notes Part 1"}],
    # "e6a":   [{"file_id": "PASTE_HERE", "caption": "IC Engines & Gas Turbines – Notes Part 1"}],
    # "e6c":   [{"file_id": "PASTE_HERE", "caption": "Turbo Machinery – Notes Part 1"}],
    # "e6d":   [{"file_id": "PASTE_HERE", "caption": "Fluid Power Control – Notes Part 1"}],
    # "e6e":   [{"file_id": "PASTE_HERE", "caption": "Advanced Fluid Mechanics – Notes Part 1"}],
    # "e6f":   [{"file_id": "PASTE_HERE", "caption": "Composite Materials – Notes Part 1"}],
    # "e6g":   [{"file_id": "PASTE_HERE", "caption": "Mechatronics – Notes Part 1"}],
    # "e6h":   [{"file_id": "PASTE_HERE", "caption": "Robotics – Notes Part 1"}],
    # "e6i":   [{"file_id": "PASTE_HERE", "caption": "Material Handling – Notes Part 1"}],
    # "e6j":   [{"file_id": "PASTE_HERE", "caption": "Principles of Management – Notes Part 1"}],

    # ── Semester 7 ── (paste file_ids when ready)
    # "amt7":  [{"file_id": "PASTE_HERE", "caption": "Adv. Manufacturing Technology – Notes Part 1"}],
    # "eco7":  [{"file_id": "PASTE_HERE", "caption": "Economics for Engineers – Notes Part 1"}],
    # "e7a":   [{"file_id": "PASTE_HERE", "caption": "Automobile Engineering – Notes Part 1"}],
    # "e7f":   [{"file_id": "PASTE_HERE", "caption": "Mechanical Vibration – Notes Part 1"}],
    # "e7g":   [{"file_id": "PASTE_HERE", "caption": "Finite Element Analysis – Notes Part 1"}],

    # ── Semester 8 ── (paste file_ids when ready)
    # "e8b":   [{"file_id": "PASTE_HERE", "caption": "Power Plant Engineering – Notes Part 1"}],
    # "e8e":   [{"file_id": "PASTE_HERE", "caption": "Tribology – Notes Part 1"}],
}

# ══════════════════════════════════════════════════════════════════════════════
# 📁  NOTES DRIVE  ——  Google Drive folder links (when no individual PDFs yet)
# ══════════════════════════════════════════════════════════════════════════════
NOTES_DRIVE = {
    "met4": "https://drive.google.com/drive/folders/1EnmL93MnVJplEmg4CbVG2gds5ZR1MqV9",
    # "ht5":  "PASTE_DRIVE_LINK_HERE",
    # "sm5":  "PASTE_DRIVE_LINK_HERE",
    # "ktm5": "PASTE_DRIVE_LINK_HERE",
}

# ══════════════════════════════════════════════════════════════════════════════
# 📄  NOTES PDF — CHANNEL STORAGE  (large notes; bypasses 50 MB bot limit)
#
#  HOW TO GET msg_id:
#  Upload PDF to your private Storage Channel → Right-click → Copy Post Link
#  https://t.me/c/CHANNEL_ID/MSG_ID  ← last number is msg_id
#  Use 0 as placeholder until uploaded.
# ══════════════════════════════════════════════════════════════════════════════
NOTES_PDF_CHANNEL = {

    # ── Semester 1 ──
    "ph1":  [],   # [{"msg_id": 0, "caption": "Physics I – Notes Part 1"}]
    "m1b":  [],   # [{"msg_id": 0, "caption": "Mathematics IB – Notes Part 1"}]
    "bee1": [],   # [{"msg_id": 0, "caption": "Basic Electrical Engg – Notes Part 1"}]

    # ── Semester 2 ──
    "ch2":  [],   # [{"msg_id": 0, "caption": "Engineering Chemistry – Notes Part 1"}]
    "m2b":  [],   # [{"msg_id": 0, "caption": "Mathematics IIB – Notes Part 1"}]
    "pps":  [],   # [{"msg_id": 0, "caption": "PPS – Notes Part 1"}]
    "eng":  [],   # [{"msg_id": 0, "caption": "English – Notes Part 1"}]

    # ── Semester 3 ──
    "m3":   [],   # [{"msg_id": 0, "caption": "Mathematics III – Notes Part 1"}]
    "bio":  [],   # [{"msg_id": 0, "caption": "Biology – Notes Part 1"}]
    "ece3": [],   # [{"msg_id": 0, "caption": "Basic Electronics – Notes Part 1"}]
    "em3":  [],   # [{"msg_id": 0, "caption": "Engineering Mechanics – Notes Part 1"}]
    "thm3": [],   # [{"msg_id": 0, "caption": "Thermodynamics – Notes Part 1"}]
    "mfg3": [],   # [{"msg_id": 0, "caption": "Manufacturing Processes – Notes Part 1"}]

    # ── Semester 4 ──
    "mat4": [],   # [{"msg_id": 0, "caption": "Materials Engineering – Notes Part 1"}]
    "at4": [
        {"msg_id": 203, "caption": "Applied Thermodynamics – Notes Part 1"},
        {"msg_id": 229, "caption": "Applied Thermodynamics – Notes Part 2"},
        {"msg_id": 230, "caption": "Applied Thermodynamics – Notes Part 3"},
        {"msg_id": 231, "caption": "Applied Thermodynamics – Notes Part 4"},
        {"msg_id": 232, "caption": "Applied Thermodynamics – Notes Part 5"},
    ],
    "fm4":  [],   # [{"msg_id": 0, "caption": "Fluid Mechanics – Notes Part 1"}]
    "som4": [],   # [{"msg_id": 0, "caption": "Strength of Materials – Notes Part 1"}]
    "met4": [],   # [{"msg_id": 0, "caption": "Metrology – Notes Part 1"}]

    # ── Semester 5 ──
    "ht5":  [],   # [{"msg_id": 0, "caption": "Heat Transfer – Notes Part 1"}]
    "sm5":  [],   # [{"msg_id": 0, "caption": "Solid Mechanics – Notes Part 1"}]
    "ktm5": [],   # [{"msg_id": 0, "caption": "KTM – Notes Part 1"}]
    "etc5": [],   # [{"msg_id": 0, "caption": "Technical Communication – Notes Part 1"}]

    # ── Semester 6 ──
    "mfgt6": [],  # [{"msg_id": 0, "caption": "Manufacturing Technology – Notes Part 1"}]
    "dme6":  [],  # [{"msg_id": 0, "caption": "Design of Machine Elements – Notes Part 1"}]
    "or6":   [],  # [{"msg_id": 0, "caption": "Operations Research – Notes Part 1"}]
    "e6a":   [],  # [{"msg_id": 0, "caption": "IC Engines & Gas Turbines – Notes Part 1"}]
    "e6b":   [],  # [{"msg_id": 0, "caption": "Refrigeration & AC – Notes Part 1"}]
    "e6c":   [],  # [{"msg_id": 0, "caption": "Turbo Machinery – Notes Part 1"}]
    "e6d":   [],  # [{"msg_id": 0, "caption": "Fluid Power Control – Notes Part 1"}]
    "e6e":   [],  # [{"msg_id": 0, "caption": "Advanced Fluid Mechanics – Notes Part 1"}]
    "e6f":   [],  # [{"msg_id": 0, "caption": "Composite Materials – Notes Part 1"}]
    "e6g":   [],  # [{"msg_id": 0, "caption": "Mechatronics – Notes Part 1"}]
    "e6h":   [],  # [{"msg_id": 0, "caption": "Robotics – Notes Part 1"}]
    "e6i":   [],  # [{"msg_id": 0, "caption": "Material Handling – Notes Part 1"}]
    "e6j":   [],  # [{"msg_id": 0, "caption": "Principles of Management – Notes Part 1"}]

    # ── Semester 7 ──
    "amt7":  [],  # [{"msg_id": 0, "caption": "Adv. Manufacturing Technology – Notes Part 1"}]
    "eco7":  [],  # [{"msg_id": 0, "caption": "Economics for Engineers – Notes Part 1"}]
    "e7a":   [],  # [{"msg_id": 0, "caption": "Automobile Engineering – Notes Part 1"}]
    "e7b":   [],  # [{"msg_id": 0, "caption": "E7b – Notes Part 1"}]
    "e7c":   [],  # [{"msg_id": 0, "caption": "E7c – Notes Part 1"}]
    "e7d":   [],  # [{"msg_id": 0, "caption": "E7d – Notes Part 1"}]
    "e7e":   [],  # [{"msg_id": 0, "caption": "E7e – Notes Part 1"}]
    "e7f":   [],  # [{"msg_id": 0, "caption": "Mechanical Vibration – Notes Part 1"}]
    "e7g":   [],  # [{"msg_id": 0, "caption": "Finite Element Analysis – Notes Part 1"}]
    "e7h":   [],  # [{"msg_id": 0, "caption": "E7h – Notes Part 1"}]
    "e7i":   [],  # [{"msg_id": 0, "caption": "E7i – Notes Part 1"}]
    "e7j":   [],  # [{"msg_id": 0, "caption": "E7j – Notes Part 1"}]

    # ── Semester 8 ──
    "e8a":   [],  # [{"msg_id": 0, "caption": "E8a – Notes Part 1"}]
    "e8b":   [],  # [{"msg_id": 0, "caption": "Power Plant Engineering – Notes Part 1"}]
    "e8c":   [],  # [{"msg_id": 0, "caption": "E8c – Notes Part 1"}]
    "e8d":   [],  # [{"msg_id": 0, "caption": "E8d – Notes Part 1"}]
    "e8e":   [],  # [{"msg_id": 0, "caption": "Tribology – Notes Part 1"}]
    "e8f":   [],  # [{"msg_id": 0, "caption": "E8f – Notes Part 1"}]
    "e8g":   [],  # [{"msg_id": 0, "caption": "E8g – Notes Part 1"}]
    "e8h":   [],  # [{"msg_id": 0, "caption": "E8h – Notes Part 1"}]
    "e8i":   [],  # [{"msg_id": 0, "caption": "E8i – Notes Part 1"}]
}

# ══════════════════════════════════════════════════════════════════════════════
# 📹  LECTURE VIDEOS  ——  Channel Storage method (bypasses 50 MB bot limit)
#
#  HOW TO GET THE msg_id:
#  1. Upload video to your private Storage Channel (using your personal account).
#  2. Right-click the posted video → "Copy Post Link".
#     Link format: https://t.me/c/1234567890/45
#     The LAST number (45) is the msg_id.
#  3. Add an entry below:  {"msg_id": 45, "caption": "Subject – Unit X Lecture Y"}
#  4. Make sure STORAGE_CHANNEL_ID at the top matches your channel.
#
#  The bot uses copy_message() — no re-upload, instant delivery, supports 2 GB.
# ══════════════════════════════════════════════════════════════════════════════
LECTURE_VIDEOS = {

    # ── Semester 4 ──
    # HOW TO FILL: Upload each video to your Storage Channel, get Post Link,
    # extract the last number = msg_id. Replace 0 with real msg_id values.
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

    # ── Semester 5 ── (paste video file_ids when ready)
    # "ht5":  [{"file_id": "PASTE_HERE", "caption": "Heat Transfer – Unit X Lecture Y"}],
    # "ktm5": [{"file_id": "PASTE_HERE", "caption": "KTM – Unit X Lecture Y"}],
}

# ══════════════════════════════════════════════════════════════════════════════
# 📚  BOOKS PDF  ——  Telegram file_ids for reference book PDFs per subject
# ══════════════════════════════════════════════════════════════════════════════
BOOKS_PDF = {

    # ── Semester 3 ──
    "em3": [
        {"file_id": "BQACAgUAAxkBAAFHtgABaedMGwclAvuU4Z9XPUoUAZ0M_YQAAlECAAJ-i4lUDDAUUp8fs7A7BA", "caption": "Engineering Mechanics – RS Khurmi"},
        {"file_id": "BQACAgUAAxkBAAFHtdxp50uMCZMuNaC2oM0e8flI3EFNxgACSgEAAgHlKFUiKbKROVh00TsE", "caption": "Engineering Mechanics – KL Kumar"},
        {"file_id": "BQACAgUAAxkBAAFHtd9p50uMpfOr0EiW2TwguGCgkZdixwACUgEAAgHlKFUW_K3-l9pXXDsE", "caption": "Engineering Mechanics – RK Bansal"},
    ],
    "thm3": [
        {"file_id": "BQACAgUAAxkBAAFHtcdp50svY334cF5Y8sTAPZwk3AjzDwACvAMAAlwI-FavpURYczx7XzsE", "caption": "Engineering Thermodynamics – PK Nag (5th Ed.)"},
        {"file_id": "BQACAgUAAxkBAAFHtchp50svMfllwqL5akC8niTv0Ykd_gAC4woAAlJPyVTUtrL2aUYd3zsE", "caption": "Engineering Thermodynamics – PK Nag Solutions"},
        {"file_id": "BQACAgUAAxkBAAFHthRp50yMGigi03lEjRtRNXcSn7rzxwACkgIAAn6LiVTslfXepikcpzsE", "caption": "Engineering Thermodynamics – RK Rajput"},
    ],
    "mfg3": [
        {"file_id": "BQACAgUAAxkBAAFHteBp50uMaomdb2gnxjOAqprEQXF4CwACVAEAAgHlKFVJ1kisxYgDKDsE", "caption": "Manufacturing Technology – PN Rao (Vol. 1)"},
        {"file_id": "BQACAgUAAxkBAAFHteFp50uMzVZuuF3bCydN7T9y_Z4YMwACVgEAAgHlKFV7IeADTiD3ATsE", "caption": "Manufacturing Technology – PN Rao (Vol. 2)"},
        {"file_id": "BQACAgUAAxkBAAFHteNp50uMJgVSgVgzebeno7P2hwbtowACKQEAAiU9MVUvTMZbAAFhmoY7BA", "caption": "Manufacturing Science – Ghosh & Malik"},
        {"file_id": "BQACAgUAAxkBAAFHteVp50uMJ1B4GB8cfJcG0i58BkesVAAC5AEAAllK-FbDa0GmYhLl7jsE", "caption": "Fundamentals of Modern Manufacturing – Groover"},
    ],

    # ── Semester 4 ──
    "mat4": [
        {"file_id": "BQACAgUAAxkBAAFHtf1p50wbnPe1Nm34q5DudUb_obbBmAACgAIAAmMbIFW0Pb-MYPPDXjsE", "caption": "Materials Science – RS Khurmi"},
    ],
    "at4": [
        {"file_id": "BQACAgUAAxkBAAFHtcdp50svY334cF5Y8sTAPZwk3AjzDwACvAMAAlwI-FavpURYczx7XzsE", "caption": "Engineering Thermodynamics – PK Nag (5th Ed.)"},
        {"file_id": "BQACAgUAAxkBAAFHtchp50svMfllwqL5akC8niTv0Ykd_gAC4woAAlJPyVTUtrL2aUYd3zsE", "caption": "Engineering Thermodynamics – PK Nag Solutions"},
    ],
    "fm4": [
        {"file_id": "BQACAgUAAxkBAAFHtfxp50wb-E0hXg4yFa_DHqJ6-rZDqgACvAIAAngCaFVPhBMLy_1FqDsE", "caption": "Fluid Mechanics – RS Khurmi (19th Ed.)"},
        {"file_id": "BQACAgUAAxkBAAFHtdpp50uMVX5fmkCeB5rx66rAMxhBRAACRwEAAgHlKFWLGuvIx7531TsE", "caption": "Fluid Mechanics – RK Bansal"},
        {"file_id": "BQACAgUAAxkBAAFHthBp50yMtS1u0Vx8P78hhRJi4YDwnAACjAIAAn6LiVQPsrieCKJ3FzsE", "caption": "Fluid Mechanics & Hydraulic Machines – RK Rajput (5th Ed.)"},
        {"file_id": "BQACAgIAAxkBAAFHthVp50yM43sSQ8ma4-regdA4Ccr3yAACMwQAAreJoUq4WFHJNcomwjsE", "caption": "Fluid Mechanics (Advanced) – Rajput & Tabatabaian"},
    ],
    "som4": [
        {"file_id": "BQACAgUAAxkBAAFHtf5p50wbvrFkYHUmn9Dvsk6M90yB3AACZwIAAn6LiVRB_blMMnxm8jsE", "caption": "Strength of Materials – RS Khurmi"},
        {"file_id": "BQACAgUAAxkBAAFHtd5p50uMpAL333J-G_eZ1irTub7t5wACUAEAAgHlKFV60vxYm_M0dzsE", "caption": "Mechanics of Materials – BC Punmia"},
        {"file_id": "BQACAgUAAxkBAAFHthtp50yMPwABT-t7xEkCCqNI4eDfJy8AAr8KAAKCLrFX_-yVHI3XGqs7BA", "caption": "Strength of Materials – RK Rajput"},
    ],
    "met4": [
        {"file_id": "BQACAgUAAxkBAAFHthlp50yMHWrMdz88zLXM8cBm8EshpAAC1goAAoIusVdoj-lE73Xm7TsE", "caption": "Mechanical Measurements & Instrumentation – RK Rajput"},
    ],

    # ── Semester 5 ──
    "ht5": [
        {"file_id": "BQACAgUAAxkBAAFHtdhp50uMrck7v7z_q_CiYP8xDNq4LQACNgEAAgHlKFWf1yyjj6YBhTsE", "caption": "Heat Transfer – SK Som"},
        {"file_id": "BQACAgUAAxkBAAFHthZp50yMBueggV3eczeyYV7cjcHYMwACnQIAAn6LiVQ7hE8HlxPuDTsE", "caption": "Heat & Mass Transfer – RK Rajput (5th Ed.)"},
    ],
    "ktm5": [
        {"file_id": "BQACAgUAAxkBAAFHtf9p50wbvrW10OiuxjXz5ZVdZuJLiAACewIAAgH8kFRqpU_hnBSXJzsE", "caption": "Theory of Machines – RS Khurmi"},
        {"file_id": "BQACAgUAAxkBAAFHtdlp50uMX8ykMuCX8oYPFGp6VESdXwACNwEAAgHlKFVXCLwZjG2lPjsE", "caption": "Theory of Machines – SS Ratan"},
    ],

    # ── Semester 6 ──
    "mfgt6": [
        {"file_id": "BQACAgUAAxkBAAFHteBp50uMaomdb2gnxjOAqprEQXF4CwACVAEAAgHlKFVJ1kisxYgDKDsE", "caption": "Manufacturing Technology – PN Rao (Vol. 1)"},
        {"file_id": "BQACAgUAAxkBAAFHteFp50uMzVZuuF3bCydN7T9y_Z4YMwACVgEAAgHlKFV7IeADTiD3ATsE", "caption": "Manufacturing Technology – PN Rao (Vol. 2)"},
        {"file_id": "BQACAgUAAxkBAAFHthdp50yMLhamL0nB8bWCwni2Dw4NMQACAQQAAhYJmFUwwc4N_XCoAAE7BA", "caption": "Manufacturing Technology – RK Rajput"},
        {"file_id": "BQACAgUAAxkBAAFHteNp50uMJgVSgVgzebeno7P2hwbtowACKQEAAiU9MVUvTMZbAAFhmoY7BA", "caption": "Manufacturing Science – Ghosh & Malik"},
    ],
    "dme6": [
        {"file_id": "BQACAgUAAxkBAAFHtc1p50svwM9udb1nuhOan1nXRq0BEgACZQsAAr7iGFff6l-y-8w8fjsE", "caption": "Design of Machine Elements – VB Bhandari"},
        {"file_id": "BQACAgUAAxkBAAFHtgJp50wb7lzA_Uc7eIvQuKluXsCntgACbgIAAgH8kFSfGz-uPxKUwTsE", "caption": "Machine Design – RS Khurmi & JK Gupta"},
    ],
    "or6": [
        {"file_id": "BQACAgUAAxkBAAFHtcxp50svrluHWPPR0i7cLS4TleTxngACawwAAmWvKFYWbESqCD0WLDsE", "caption": "Operations Research – Hillier & Lieberman (7th Ed.)"},
    ],
    "e6a": [
        {"file_id": "BQACAgUAAxkBAAFHtclp50svBrgihve7stzBojb71T6TswAC5AwAAstgEFZU9RB8c259VTsE", "caption": "Refrigeration & Air Conditioning – CP Arora (3rd Ed.)"},
        {"file_id": "BQACAgUAAxkBAAFHtctp50svIVEloqsF-SDSZm80lLzqSQACXAwAAmWvKFblM_MpGeS14jsE", "caption": "Gas Turbines – V. Ganesan"},
        {"file_id": "BQACAgUAAxkBAAFHthNp50yMQ5iXSxynh6qHqRShPArCgwAC9gIAApkaMVe0cqcKKQ_X0DsE", "caption": "IC Engines – RK Rajput"},
    ],
    "e6b": [
        {"file_id": "BQACAgUAAxkBAAFHtclp50svBrgihve7stzBojb71T6TswAC5AwAAstgEFZU9RB8c259VTsE", "caption": "Refrigeration & Air Conditioning – CP Arora (3rd Ed.)"},
        {"file_id": "BQACAgUAAxkBAAFHtdtp50uM3RuNxAXeRaGma8YFiWaH4gACSAEAAgHlKFWG1eZOfEq_nTsE", "caption": "Refrigeration & Air Conditioning – CP Arora (Compact)"},
        {"file_id": "BQACAgUAAxkBAAFHtgFp50wbL49-f5KWsPpsrrGMySqm4QACUwIAAgH8kFQQqV9IpLeG6jsE", "caption": "Refrigeration & Air Conditioning – RS Khurmi"},
        {"file_id": "BQACAgUAAxkBAAFHthpp50yMnKRZKV4IxcBO1P0iUkGcgwACyAoAAoIusVc-AuuAcCxBaTsE", "caption": "Refrigeration & Air Conditioning – RK Rajput"},
    ],
    "e6g": [
        {"file_id": "BQACAgUAAxkBAAFHthFp50yMipjufIg4-1f99Nn3XyrgngACmAMAAgH8mFSZGSJ2x8IOvDsE", "caption": "Mechatronics – RK Rajput"},
    ],
    "e6h": [
        {"file_id": "BQACAgUAAxkBAAFHteZp50uMFRW5Rl4o8xemd1mg37MZaAACuAIAAjbxqVQpC46e1uppPjsE", "caption": "Robotics – Mihelj et al. (2019)"},
        {"file_id": "BQACAgUAAxkBAAFHtedp50uMUHiyDsFfb_jklm6PY8dXzAAChAIAAv6KwVSG6GgMnXaP3TsE", "caption": "Introduction to Robotics – John Craig"},
    ],

    # ── Semester 7 ──
    "e7f": [
        {"file_id": "BQACAgUAAxkBAAFHteJp50uM7H-SPdMP9KYb3olJaawZ5gACMwEAAtGDuFcUIs6NTHDV1TsE", "caption": "Mechanical Vibrations – W.T. Thomson"},
    ],
    "oe7a": [
        {"file_id": "BQACAgUAAxkBAAFHteRp50uMnJn7pmrqdzFXTUSy187NLAAC4gEAAllK-FbiwpDIVr1uyDsE", "caption": "Industrial Engineering & Management – OP Khanna"},
    ],
    "oe7d": [
        {"file_id": "BQACAgUAAxkBAAFHthhp50yMtlllL17C6U7UClrYqtxsvgACywoAAoIusVdu1P_Gz1JScjsE", "caption": "Non-Conventional Energy Sources – RK Rajput"},
    ],

    # ── Semester 8 ──
    "e8b": [
        {"file_id": "BQACAgUAAxkBAAFHthJp50yMLfQ6eYVxFL9KsVhT6A4wmwACQgIAAgH8kFTie2EiwiWQmjsE", "caption": "Power Plant Engineering – RK Rajput"},
        {"file_id": "BQACAgUAAxkBAAFHtd1p50uMZ1grj6YF_pYjAZ_BgnuatgACSwEAAgHlKFUWITgnLUyuKDsE", "caption": "Power Plant Engineering – PK Nag"},
    ],
    "e8h": [
        {"file_id": "BQACAgUAAxkBAAFHtmJp51A5HmtlfXpGnpUHFklqtBjMVAACax0AAqCQQFebwDZdgvUarTsE", "caption": "Process Planning & Cost Estimation – Reference Notes"},
    ],
    "oe8d": [
        {"file_id": "BQACAgUAAxkBAAFHtmRp51A5j_uIBOZ7Zx09JS0HdOcGdgACbR0AAqCQQFcT6yAkNuFO-zsE", "caption": "Industrial Pollution & Control – Notes (Part 1)"},
        {"file_id": "BQACAgUAAxkBAAFHtmVp51A5FkdSiNSL3kVsMKCtkZN-vwACbh0AAqCQQFe8BElOtHahETsE", "caption": "Industrial Pollution & Control – Notes (Part 2)"},
    ],
    "oe8f": [
        {"file_id": "BQACAgUAAxkBAAFHtmNp51A5BUA4-XSKKaSLgKOmxUXsigACbB0AAqCQQFeT5va-bkfiyDsE", "caption": "Waste to Energy – Notes"},
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# 📚  BOOKS PDF — CHANNEL STORAGE  (large books; bypasses 50 MB bot limit)
#
#  Same channel storage method as LECTURE_VIDEOS.
#  Use 0 as placeholder until uploaded. Sequential order matches BOOKS_PDF above.
# ══════════════════════════════════════════════════════════════════════════════
BOOKS_PDF_CHANNEL = {

    # ── Semester 3 ──
    "em3": [
        {"msg_id": 175, "caption": "Engineering Mechanics – RS Khurmi"},
        {"msg_id": 176, "caption": "Engineering Mechanics – KL Kumar"},
        {"msg_id": 178, "caption": "Engineering Mechanics – RK Bansal"},          # 177 unused
    ],
    "thm3": [
        {"msg_id": 179, "caption": "Engineering Thermodynamics – PK Nag (5th Ed.)"},
        {"msg_id": 180, "caption": "Engineering Thermodynamics – PK Nag Solutions"},
        {"msg_id": 181, "caption": "Engineering Thermodynamics – RK Rajput"},
    ],
    "mfg3": [
        {"msg_id": 182, "caption": "Manufacturing Technology – PN Rao (Vol. 1)"},
        {"msg_id": 204, "caption": "Manufacturing Technology – PN Rao (Vol. 2)"},  # gap 183-203 = other content
        {"msg_id": 205, "caption": "Manufacturing Science – Ghosh & Malik"},
        {"msg_id": 206, "caption": "Fundamentals of Modern Manufacturing – Groover"},
    ],
    "bio":  [],   # [{"msg_id": 0, "caption": "Biology – Reference Book"}]
    "ece3": [],   # [{"msg_id": 0, "caption": "Basic Electronics – Reference Book"}]
    "m3":   [],   # [{"msg_id": 0, "caption": "Mathematics III – Reference Book"}]

    # ── Semester 4 ──
    "mat4": [
        {"msg_id": 207, "caption": "Materials Science – RS Khurmi"},
    ],
    "at4": [
        {"msg_id": 208, "caption": "Engineering Thermodynamics – PK Nag (5th Ed.)"},
        {"msg_id": 209, "caption": "Engineering Thermodynamics – PK Nag Solutions"},
    ],
    "fm4": [
        {"msg_id": 210, "caption": "Fluid Mechanics – RS Khurmi (19th Ed.)"},
        {"msg_id": 211, "caption": "Fluid Mechanics – RK Bansal"},
        {"msg_id": 212, "caption": "Fluid Mechanics & Hydraulic Machines – RK Rajput (5th Ed.)"},
        {"msg_id": 214, "caption": "Fluid Mechanics (Advanced) – Rajput & Tabatabaian"},  # 213 unused
    ],
    "som4": [
        {"msg_id": 215, "caption": "Strength of Materials – RS Khurmi"},
        {"msg_id": 216, "caption": "Mechanics of Materials – BC Punmia"},
        {"msg_id": 217, "caption": "Strength of Materials – RK Rajput"},
    ],
    "met4": [
        {"msg_id": 218, "caption": "Mechanical Measurements & Instrumentation – RK Rajput"},
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
    "sm5":  [],   # [{"msg_id": 0, "caption": "Solid Mechanics – Reference Book"}]
    "etc5": [],   # [{"msg_id": 0, "caption": "Technical Communication – Reference Book"}]

    # ── Semester 6 ──
    "mfgt6": [
        {"msg_id": 223, "caption": "Manufacturing Technology – PN Rao (Vol. 1)"},
        {"msg_id": 224, "caption": "Manufacturing Technology – PN Rao (Vol. 2)"},
        {"msg_id": 225, "caption": "Manufacturing Technology – RK Rajput"},
        {"msg_id": 226, "caption": "Manufacturing Science – Ghosh & Malik"},
    ],
    "dme6": [
        {"msg_id": 227, "caption": "Design of Machine Elements – VB Bhandari"},
        {"msg_id": 228, "caption": "Machine Design – RS Khurmi & JK Gupta"},
    ],
    "or6":  [],   # [{"msg_id": 0, "caption": "Operations Research – Hillier & Lieberman"}]
    "e6a":  [],   # [{"msg_id": 0, "caption": "IC Engines & Gas Turbines – Reference Book"}]
    "e6b":  [],   # [{"msg_id": 0, "caption": "Refrigeration & AC – CP Arora"}]
    "e6c":  [],   # [{"msg_id": 0, "caption": "Turbo Machinery – Reference Book"}]
    "e6d":  [],   # [{"msg_id": 0, "caption": "Fluid Power Control – Reference Book"}]
    "e6e":  [],   # [{"msg_id": 0, "caption": "Advanced Fluid Mechanics – Reference Book"}]
    "e6f":  [],   # [{"msg_id": 0, "caption": "Composite Materials – Reference Book"}]
    "e6g":  [],   # [{"msg_id": 0, "caption": "Mechatronics – RK Rajput"}]
    "e6h":  [],   # [{"msg_id": 0, "caption": "Robotics – Mihelj et al."}]
    "e6i":  [],   # [{"msg_id": 0, "caption": "Material Handling – Reference Book"}]
    "e6j":  [],   # [{"msg_id": 0, "caption": "Principles of Management – Reference Book"}]

    # ── Semester 7 ──
    "amt7":  [],  # [{"msg_id": 0, "caption": "Adv. Manufacturing Technology – Reference Book"}]
    "eco7":  [],  # [{"msg_id": 0, "caption": "Economics for Engineers – Reference Book"}]
    "e7a":   [],  # [{"msg_id": 0, "caption": "Automobile Engineering – Reference Book"}]
    "e7f":   [],  # [{"msg_id": 0, "caption": "Mechanical Vibrations – W.T. Thomson"}]
    "e7g":   [],  # [{"msg_id": 0, "caption": "FEA – Reference Book"}]
    "oe7a":  [],  # [{"msg_id": 0, "caption": "Industrial Engineering – OP Khanna"}]
    "oe7d":  [],  # [{"msg_id": 0, "caption": "Non-Conventional Energy – RK Rajput"}]

    # ── Semester 8 ──
    "e8b":   [],  # [{"msg_id": 0, "caption": "Power Plant Engineering – RK Rajput"}]
    "e8h":   [],  # [{"msg_id": 0, "caption": "Process Planning & Cost Estimation – Reference"}]
    "oe8d":  [],  # [{"msg_id": 0, "caption": "Industrial Pollution & Control – Reference Book"}]
    "oe8f":  [],  # [{"msg_id": 0, "caption": "Waste to Energy – Reference Book"}]
}

# ══════════════════════════════════════════════════════════════════════════════
# 🎬  YOUTUBE LINKS  ——  Playlists & videos per subject
# ══════════════════════════════════════════════════════════════════════════════
YOUTUBE_LINKS = {

    # ── Semester 1 ── (paste links when ready)
    # "ph1":  [{"title": "▶️ Physics I – Playlist 1", "url": "PASTE_HERE"}],
    # "m1b":  [{"title": "▶️ Mathematics IB – Playlist 1", "url": "PASTE_HERE"}],
    # "bee1": [{"title": "▶️ Basic Electrical Engg – Playlist 1", "url": "PASTE_HERE"}],

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
    # "eng": [{"title": "▶️ English – Playlist 1", "url": "PASTE_HERE"}],

    # ── Semester 3 ── (paste links when ready)
    # "m3":   [{"title": "▶️ Mathematics III – Playlist 1", "url": "PASTE_HERE"}],
    # "bio":  [{"title": "▶️ Biology – Playlist 1", "url": "PASTE_HERE"}],
    # "ece3": [{"title": "▶️ Basic Electronics – Playlist 1", "url": "PASTE_HERE"}],
    # "em3":  [{"title": "▶️ Engineering Mechanics – Playlist 1", "url": "PASTE_HERE"}],
    # "thm3": [{"title": "▶️ Thermodynamics – Playlist 1", "url": "PASTE_HERE"}],
    # "mfg3": [{"title": "▶️ Manufacturing Processes – Playlist 1", "url": "PASTE_HERE"}],

    # ── Semester 4 ──
    "mat4": [
        {"title": "▶️ Materials Engineering – Playlist 1", "url": "https://youtube.com/playlist?list=PLjMQ11sM-5iwWYbnSsBxUus1HawGg0HGa"},
        {"title": "▶️ Materials Engineering – Video",      "url": "https://youtu.be/nCBUwiib0Xo"},
        {"title": "▶️ Materials Engineering – Playlist 2", "url": "https://youtube.com/playlist?list=PLWo-ERPOfIbbOV1slvh62wHgcxaB2-mDT"},
    ],
    # "at4":  [{"title": "▶️ Applied Thermodynamics – Playlist 1", "url": "PASTE_HERE"}],

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

    # ── Semester 5 ── (paste links when ready)
    # "ht5":  [{"title": "▶️ Heat Transfer – Playlist 1", "url": "PASTE_HERE"}],
    # "sm5":  [{"title": "▶️ Solid Mechanics – Playlist 1", "url": "PASTE_HERE"}],
    # "ktm5": [{"title": "▶️ KTM – Playlist 1", "url": "PASTE_HERE"}],
    # "etc5": [{"title": "▶️ Technical Communication – Playlist 1", "url": "PASTE_HERE"}],

    # ── Semester 6 ── (paste links when ready)
    # "mfgt6": [{"title": "▶️ Manufacturing Technology – Playlist 1", "url": "PASTE_HERE"}],
    # "dme6":  [{"title": "▶️ Design of Machine Elements – Playlist 1", "url": "PASTE_HERE"}],
    # "or6":   [{"title": "▶️ Operations Research – Playlist 1", "url": "PASTE_HERE"}],
    # "e6a":   [{"title": "▶️ IC Engines & Gas Turbines – Playlist 1", "url": "PASTE_HERE"}],
    # "e6b":   [{"title": "▶️ Refrigeration & AC – Playlist 1", "url": "PASTE_HERE"}],
    # "e6c":   [{"title": "▶️ Turbo Machinery – Playlist 1", "url": "PASTE_HERE"}],
    # "e6d":   [{"title": "▶️ Fluid Power Control – Playlist 1", "url": "PASTE_HERE"}],
    # "e6g":   [{"title": "▶️ Mechatronics – Playlist 1", "url": "PASTE_HERE"}],
    # "e6h":   [{"title": "▶️ Robotics – Playlist 1", "url": "PASTE_HERE"}],

    # ── Semester 7 ── (paste links when ready)
    # "amt7":  [{"title": "▶️ Adv. Manufacturing Technology – Playlist 1", "url": "PASTE_HERE"}],
    # "e7c":   [{"title": "▶️ CFD – Playlist 1", "url": "PASTE_HERE"}],
    # "e7f":   [{"title": "▶️ Mechanical Vibration – Playlist 1", "url": "PASTE_HERE"}],
    # "e7g":   [{"title": "▶️ Finite Element Analysis – Playlist 1", "url": "PASTE_HERE"}],

    # ── Semester 8 ── (paste links when ready)
    # "e8b":  [{"title": "▶️ Power Plant Engineering – Playlist 1", "url": "PASTE_HERE"}],
    # "e8e":  [{"title": "▶️ Tribology – Playlist 1", "url": "PASTE_HERE"}],
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
            {"title": "📢 PYQs & Practice Qs — Telegram Channel", "url": TG},
            {"title": "📂 PYQ — Google Drive", "url": pyq, "description": "Previous year question papers on Drive"},
        ],
        "books": [
            {"title": "📢 Reference Books — Telegram Channel", "url": TG, "description": "Book PDFs shared in the channel"},
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
            "e6b":   s("Refrigeration & Air Conditioning  [Elec-I/II-B]",   "PE-ME601B/602B", "Vapour compression/absorption cycles, psychrometry, cooling load, AC systems."),
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
    """If the user hasn't joined required channels, reply with the join prompt and return True."""
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
            f"[🔗 Mechanical GATE / ESE / JE Notes 2027]({GATE_CH})\n\n"
            "✅ Handwritten notes\n✅ Video lectures\n"
            "✅ Daily Practice Problems\n✅ Mock tests & solutions",
            parse_mode="Markdown", disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📲 Join GATE / ESE / JE Channel", url=GATE_CH)],
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
            f"📢 [Study Materials Channel]({TG})\n"
            f"📂 [PYQ & Organizers — Drive]({DR38})\n"
            f"🎯 [GATE / ESE / JE Channel]({GATE_CH})",
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

        # ── NOTES: send PDFs directly or show Drive link ───────────────────
        if res_type == "notes":
            pdfs       = NOTES_PDF.get(sub_id, [])
            ch_pdfs    = [p for p in NOTES_PDF_CHANNEL.get(sub_id, []) if p.get("msg_id", 0) != 0]
            drive_link = NOTES_DRIVE.get(sub_id)

            if pdfs or ch_pdfs:
                total = len(pdfs) + len(ch_pdfs)
                await q.edit_message_text(
                    f"📤 *Sending notes for {sub['name']}…*\n"
                    f"_{total} PDF(s) incoming below_ 👇",
                    parse_mode="Markdown")
                chat_id = q.message.chat_id
                # ── file_id PDFs (direct send) ──
                for idx, pdf in enumerate(pdfs, 1):
                    caption      = pdf.get("caption", f"{sub['name']} – Part {idx}")
                    caption_full = f"📄 *{caption}*\n_{sub['name']} | {sub.get('code','')}_"
                    try:
                        await context.bot.send_document(
                            chat_id=chat_id,
                            document=pdf["file_id"],
                            caption=caption_full,
                            parse_mode="Markdown")
                    except Exception as e:
                        logger.error(f"Failed to send PDF for {sub_id}: {e}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⚠️ Could not send *{caption}*. Check channel for this file.",
                            parse_mode="Markdown")
                # ── channel storage PDFs (copy_message) ──
                for idx, pdf in enumerate(ch_pdfs, 1):
                    caption      = pdf.get("caption", f"{sub['name']} – Notes Part {idx}")
                    caption_full = f"📄 *{caption}*\n_{sub['name']} | {sub.get('code','')}_"
                    try:
                        await context.bot.copy_message(
                            chat_id=chat_id,
                            from_chat_id=STORAGE_CHANNEL_ID,
                            message_id=pdf["msg_id"],
                            caption=caption_full,
                            parse_mode="Markdown")
                    except Exception as e:
                        logger.error(f"Failed to copy channel note for {sub_id} msg_id={pdf.get('msg_id')}: {e}")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⚠️ Could not send *{caption}*.\n_Ensure the bot is Admin in the Storage Channel._",
                            parse_mode="Markdown")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ All {total} note(s) sent for *{sub['name']}*!",
                    parse_mode="Markdown",
                    reply_markup=back_kb(sem_num, sub_id))

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
                    "_PDFs for this subject will be uploaded shortly._\n\n"
                    f"📢 Meanwhile, check the [Telegram Channel]({TG}) for notes.",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup=back_kb(sem_num, sub_id))

        # ── LECTURES: copy from Storage Channel (large videos) or show YouTube ─
        elif res_type == "lectures":
            tg_videos = LECTURE_VIDEOS.get(sub_id, [])
            yt_links  = YOUTUBE_LINKS.get(sub_id, [])

            # Filter out placeholder entries (msg_id == 0 means not yet uploaded)
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
                        # copy_message pulls the video from the private Storage Channel
                        # instantly — no re-upload, no bandwidth used, supports up to 2 GB.
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

            # ── For BOOKS: send PDFs first if available ──
            if res_type == "books":
                book_pdfs = BOOKS_PDF.get(sub_id, [])
                ch_books  = [b for b in BOOKS_PDF_CHANNEL.get(sub_id, []) if b.get("msg_id", 0) != 0]
                if book_pdfs or ch_books:
                    total = len(book_pdfs) + len(ch_books)
                    await q.edit_message_text(
                        f"📤 *Sending reference books for {sub['name']}…*\n"
                        f"_{total} book(s) incoming below_ 👇",
                        parse_mode="Markdown")
                    chat_id = q.message.chat_id
                    # ── file_id books (direct send) ──
                    for idx, book in enumerate(book_pdfs, 1):
                        caption      = book.get("caption", f"{sub['name']} – Book {idx}")
                        caption_full = f"📗 *{caption}*\n_{sub['name']} | {sub.get('code','')}_"
                        try:
                            await context.bot.send_document(
                                chat_id=chat_id,
                                document=book["file_id"],
                                caption=caption_full,
                                parse_mode="Markdown")
                        except Exception as e:
                            logger.error(f"Failed to send book PDF for {sub_id}: {e}")
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"⚠️ Could not send *{caption}*.",
                                parse_mode="Markdown")
                    # ── channel storage books (copy_message) ──
                    for idx, book in enumerate(ch_books, 1):
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
                            logger.error(f"Failed to copy channel book for {sub_id} msg_id={book.get('msg_id')}: {e}")
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"⚠️ Could not send *{caption}*.\n_Ensure the bot is Admin in the Storage Channel._",
                                parse_mode="Markdown")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ All {total} book(s) sent for *{sub['name']}*!",
                        parse_mode="Markdown",
                        reply_markup=back_kb(sem_num, sub_id))
                    return   # skip the URL-only block below

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
    # Start the lightweight HTTP health-check server in a background thread
    # (required for Render Web Service — without this the deploy fails)
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
