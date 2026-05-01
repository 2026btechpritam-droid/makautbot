"""
MAKAUT Mechanical Engineering Study Bot
2018-19 Syllabus | Semesters 1–8 | All Theory + All Electives
python-telegram-bot v21 | @GURU_HOSTING_TGBOT compatible

... (header unchanged) ...
"""

import os, asyncio, logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           ContextTypes, MessageHandler, filters)

# ── Flask keep‑alive server ─────────────────────────────────────────────────
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

# ── Channel Storage ────────────────────────────────────────────────────────
STORAGE_CHANNEL_ID = int(os.environ.get("STORAGE_CHANNEL_ID", "-1003810204452"))

# ── Shared Links ──────────────────────────────────────────────────────────
PYQ_2ND  = "https://drive.google.com/drive/folders/1pqOU462w0HneTlVK7b0Kq3W-0SnPT6wh"
ORG_2ND  = "https://drive.google.com/drive/folders/10UYEM1xmZBBWWGjbvoyyiL10ooURfi8N"
DR38     = "https://drive.google.com/drive/folders/1W46fCm1ysdJENxCazCI_ZWqsAqUxnXRy"
CS       = "coming_soon"

# ── Force Join Channels ────────────────────────────────────────────────────
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

# ════════════════════════════════════════════════════════════════════════════
# STATISTICS TRACKER
# ════════════════════════════════════════════════════════════════════════════
unique_users = set()

# ════════════════════════════════════════════════════════════════════════════
# NOTES / BOOKS / VIDEOS DATA (unchanged from previous message)
# ════════════════════════════════════════════════════════════════════════════
# ... all NOTES_PDF, NOTES_PDF_CHANNEL, NOTES_DRIVE, LECTURE_VIDEOS,
#     BOOKS_PDF_CHANNEL, YOUTUBE_LINKS definitions remain exactly the same ...

# (I will not repeat them here to keep the answer compact; they are as in the
#  previous fully updated file. Only the changed parts are shown below.)

# ── Resource builder ───────────────────────────────────────────────────────
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

# ... MATERIALS dictionary (unchanged) ...

# ─────────────────────────────────────────────────────────────────────────────
# KEYBOARDS (modified main_menu_kb)
# ─────────────────────────────────────────────────────────────────────────────

def main_menu_kb():
    sems = list(MATERIALS.items())
    rows = []
    for i in range(0, len(sems), 2):
        rows.append([InlineKeyboardButton(f"📚 {d['name']}", callback_data=f"sem|{n}")
                     for n, d in sems[i:i+2]])
    # GATE + About
    rows.append([InlineKeyboardButton("🎯 GATE / ESE / JE Prep", callback_data="gate"),
                 InlineKeyboardButton("ℹ️ About Bot",             callback_data="about")])
    # Statistics + Request Materials
    rows.append([InlineKeyboardButton("📊 Statistics",            callback_data="stats"),
                 InlineKeyboardButton("📩 Request Materials",     url="https://t.me/SemesterMaterials_bot")])
    return InlineKeyboardMarkup(rows)

# ... sem_kb, sub_kb, back_kb unchanged ...

# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS (modified to record users and handle stats)
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
    # Track user
    unique_users.add(user_id)
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
            unique_users.add(user_id)
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

    # Track this user (once they are verified)
    unique_users.add(user_id)

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

    elif act == "stats":
        count = len(unique_users)
        await q.edit_message_text(
            f"📊 *Bot Statistics*\n\n"
            f"👥 Unique users: *{count}*\n\n"
            "_This count includes everyone who has interacted with the bot._",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Main Menu", callback_data="main")]]))

    elif act == "sem" and len(pts) == 2:
        # ... unchanged ...
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
        # ... unchanged ...
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
        # ... same as before (notes with buttons, lectures, books, etc.) ...
        # No change needed here; the code from the previous version is correct.
        # (I'm omitting the full repetition to save space; use the handler
        #  from the previous fully updated bot. The only addition is
        #  the note_file handler and the rest is identical.)
        ...

    elif act == "note_file" and len(pts) == 4:
        # ... handler as defined earlier ...
        ...

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
