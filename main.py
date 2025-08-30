# ITeach Academy Registration Bot
# Railway variables: BOT_TOKEN, ADMIN_ID, DATABASE_URL

import os
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from zoneinfo import ZoneInfo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from models import Base, Registration

# ----------------------- Config & Setup -----------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_RAW = os.environ.get("ADMIN_ID")
DATABASE_URL = os.environ.get("DATABASE_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")
if not ADMIN_ID_RAW or not ADMIN_ID_RAW.isdigit():
    raise RuntimeError("ADMIN_ID environment variable is missing or invalid.")
ADMIN_ID = int(ADMIN_ID_RAW)
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("iteach_bot")

# DB setup
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Create all tables
Base.metadata.create_all(bind=engine)

# ----------------------- Constants & Labels -----------------------
COURSES = {
    "english": "🇬🇧 Ingliz tili",
    "german": "🇩🇪 Nemis tili",
    "math": "🧮 Matematika",
    "uzbek": "🇺🇿 Ona tili",
    "history": "📜 Tarix",
    "biology": "🧬 Biologiya",
    "chemistry": "⚗️ Kimyo",
}
COURSES_WITH_LEVEL = {"english", "german"}

LEVELS = {
    "A1": "A1 • Boshlang'ich",
    "A2": "A2 • Elementar",
    "B1": "B1 • O'rta",
    "B2": "B2 • Yuqori o'rta",
    "C1": "C1 • Ilg'or",
    "C2": "C2 • Mukammal",
}

SECTIONS_ENGLISH = {
    "kids": "👶 Bolalar",
    "general": "📘 Umumiy",
    "cefr": "🧭 CEFR",
    "ielts": "🎓 IELTS",
}
SECTIONS_GERMAN = {
    "kids": "👶 Bolalar",
    "general": "📘 Umumiy",
    "certificate": "🏅 Sertifikat",
}
SECTIONS_OTHERS = {
    "kids": "👶 Bolalar",
    "general": "📘 Umumiy",
    "certificate": "🏅 Sertifikat",
}

TASHKENT_TZ = ZoneInfo("Asia/Tashkent")

# ----------------------- Helpers: Keyboards -----------------------
def kb_register() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Ro'yxatdan o'tish", callback_data="reg:start")
    ]])

def kb_courses() -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    items = list(COURSES.items())
    for i in range(0, len(items), 2):
        row = []
        for key, label in items[i:i + 2]:
            row.append(InlineKeyboardButton(label, callback_data=f"reg:course:{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="reg:cancel")])
    return InlineKeyboardMarkup(rows)

def kb_levels() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(LEVELS["A1"], callback_data="reg:level:A1"),
            InlineKeyboardButton(LEVELS["A2"], callback_data="reg:level:A2"),
        ],
        [
            InlineKeyboardButton(LEVELS["B1"], callback_data="reg:level:B1"),
            InlineKeyboardButton(LEVELS["B2"], callback_data="reg:level:B2"),
        ],
        [
            InlineKeyboardButton(LEVELS["C1"], callback_data="reg:level:C1"),
            InlineKeyboardButton(LEVELS["C2"], callback_data="reg:level:C2"),
        ],
        [
            InlineKeyboardButton("⬅️ Ortga (Kurslar)", callback_data="reg:back:courses")
        ],
    ]
    return InlineKeyboardMarkup(rows)

def kb_sections(course_key: str) -> InlineKeyboardMarkup:
    if course_key == "english":
        sections = SECTIONS_ENGLISH
        back = "reg:back:levels"
    elif course_key == "german":
        sections = SECTIONS_GERMAN
        back = "reg:back:levels"
    else:
        sections = SECTIONS_OTHERS
        back = "reg:back:courses"

    rows: List[List[InlineKeyboardButton]] = []
    items = list(sections.items())
    for i in range(0, len(items), 2):
        row = []
        for key, label in items[i:i + 2]:
            row.append(InlineKeyboardButton(label, callback_data=f"reg:section:{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Ortga", callback_data=back)])
    rows.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="reg:cancel")])
    return InlineKeyboardMarkup(rows)

def kb_review() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="reg:confirm"),
            InlineKeyboardButton("✏️ O'zgartirish", callback_data="reg:edit"),
        ],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="reg:cancel")],
    ])

def kb_edit_menu(course_key: str) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("📚 Kurs", callback_data="reg:edit:course"),
        InlineKeyboardButton("🗂 Bo'lim", callback_data="reg:edit:section")
    ]
    row2 = [
        InlineKeyboardButton("👤 Ism familiya", callback_data="reg:edit:name"),
        InlineKeyboardButton("🎂 Yosh", callback_data="reg:edit:age")
    ]
    row3 = [InlineKeyboardButton("📱 Telefon", callback_data="reg:edit:phone")]
    rows = [row1, row2, row3]
    if course_key in COURSES_WITH_LEVEL:
        rows.insert(1, [InlineKeyboardButton("📊 Daraja", callback_data="reg:edit:level")])
    rows.append([
        InlineKeyboardButton("⬅️ Ortga (Ko'rib chiqish)", callback_data="reg:back:review")
    ])
    return InlineKeyboardMarkup(rows)

# ----------------------- Helpers: Validation -----------------------
NAME_REGEX = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'`-]+(?:\s+[A-Za-zÀ-ÖØ-öø-ÿ'`-]+)+$")

def valid_full_name(s: str) -> bool:
    s = s.strip()
    return bool(NAME_REGEX.match(s)) and (2 <= len(s.split()) <= 5)

def valid_age(s: str) -> bool:
    if not s.isdigit():
        return False
    n = int(s)
    return 3 <= n <= 100

PHONE_REGEX = re.compile(r"^\+998\d{9}$")

def normalize_phone(text: str) -> Optional[str]:
    t = text.strip().replace(" ", "")
    if t.startswith("998") and len(t) == 12:
        t = "+" + t
    if PHONE_REGEX.match(t):
        return t
    return None

# ----------------------- Content builders -----------------------
def build_review_text(d: Dict[str, Any]) -> str:
    course_label = COURSES.get(d.get("course_key", ""), d.get("course_label", ""))
    level_label = d.get("level_label")
    section_label = d.get("section_label")
    full_name = d.get("full_name", "")
    age = d.get("age", "")
    phone = d.get("phone", "")

    lines = [
        "🧾 *Ma'lumotlarni ko'rib chiqing:*",
        f"• 📚 *Kurs:* {course_label}",
        f"• 🗂 *Bo'lim:* {section_label}",
        f"• 👤 *Ism familiya:* {full_name}",
        f"• 🎂 *Yosh:* {age}",
        f"• 📱 *Telefon:* {phone}",
    ]
    if d.get("course_key") in COURSES_WITH_LEVEL and level_label:
        lines.insert(2, f"• 📊 *Daraja:* {level_label}")

    return "\n".join(lines)

def build_admin_text(d: Dict[str, Any], u) -> str:
    course_label = COURSES.get(d.get("course_key", ""), d.get("course_label", ""))
    level_label = d.get("level_label")
    section_label = d.get("section_label")
    full_name = d.get("full_name", "")
    age = d.get("age", "")
    phone = d.get("phone", "")

    username = f"@{u.username}" if u.username else "@Yo'q"
    tnow = datetime.now(TASHKENT_TZ).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "🔔 *Yangi o'quvchi ro'yxatdan o'tdi*",
        f"👤 *Ism:* {full_name}",
        f"🎂 *Yosh:* {age}",
        f"📱 *Telefon:* {phone}",
        f"📚 *Kurs:* {course_label}",
        f"🗂 *Bo'lim:* {section_label}",
    ]
    if d.get("course_key") in COURSES_WITH_LEVEL and level_label:
        lines.insert(6, f"📊 *Daraja:* {level_label}")

    lines += [
        f"🆔 *Telegram ID:* {u.id}",
        f"👤 *Username:* {username}",
        f"📅 *Sana:* {tnow} (Asia/Tashkent)",
    ]
    return "\n".join(lines)

# ----------------------- Flow helpers -----------------------
async def goto_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ("📚 Qaysi *kurs*da o'qimoqchisiz?\n"
            "_Iltimos, quyidagilardan birini tanlang._")
    if getattr(update, "callback_query", None):
        await update.callback_query.edit_message_text(
            text, reply_markup=kb_courses(), parse_mode="Markdown")
    elif getattr(update, "message", None):
        await update.message.reply_text(text,
                                        reply_markup=kb_courses(),
                                        parse_mode="Markdown")
    context.user_data["step"] = "choose_course"

async def goto_levels(query, context):
    await query.edit_message_text(
        "📊 Iltimos, *darajangizni* tanlang:",
        reply_markup=kb_levels(),
        parse_mode="Markdown",
    )
    context.user_data["step"] = "choose_level"

async def goto_sections(query, context):
    course_key = context.user_data.get("course_key")
    await query.edit_message_text(
        "🗂 Iltimos, *bo'lim*ni tanlang:",
        reply_markup=kb_sections(course_key),
        parse_mode="Markdown",
    )
    context.user_data["step"] = "choose_section"

async def ask_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = ("✍️ *Iltimos, to'liq ism-familiyangizni kiriting.*\n"
           "_Masalan: Alamozon Alovuddinov_")
    if getattr(update, "effective_chat", None):
        await update.effective_chat.send_message(
            msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    context.user_data["step"] = "ask_name"

async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if getattr(update, "effective_chat", None):
        await update.effective_chat.send_message("🎂 *Yoshingizni kiriting:*",
                                                 parse_mode="Markdown")
    context.user_data["step"] = "ask_age"

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Raqamni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    if getattr(update, "effective_chat", None):
        await update.effective_chat.send_message(
            "📞 *Telefon raqamingizni kiriting* (format: `+998XXXXXXXXX`) yoki pastdagi tugma orqali yuboring.",
            parse_mode="Markdown",
            reply_markup=kb,
        )
    context.user_data["step"] = "ask_phone"

async def show_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = build_review_text(context.user_data)
    if getattr(update, "callback_query", None):
        await update.callback_query.edit_message_text(text,
                                                      reply_markup=kb_review(),
                                                      parse_mode="Markdown")
    elif getattr(update, "effective_chat", None):
        await update.effective_chat.send_message(text,
                                                 reply_markup=kb_review(),
                                                 parse_mode="Markdown")
    context.user_data["step"] = "review"

# ----------------------- Handlers -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "Assalomu alaykum!\n"
        "*ITeach Academy*ga xush kelibsiz! 🎓\n\n"
        "Bizning o'quv jamoamizga qo'shilish va ro'yxatdan o'tish uchun pastdagi tugmani bosing."
    )
    await update.message.reply_text(welcome,
                                    reply_markup=kb_register(),
                                    parse_mode="Markdown")
    context.user_data.clear()

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    await query.answer()
    logger.info("Callback data: %s", data)

    # Cancel from anywhere
    if data == "reg:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Ro'yxatdan o'tish bekor qilindi.")
        return

    # Start registration -> choose course
    if data == "reg:start":
        await goto_courses(update, context)
        return

    # Back navigations
    if data == "reg:back:courses":
        context.user_data.pop("level_key", None)
        context.user_data.pop("level_label", None)
        context.user_data.pop("section_key", None)
        context.user_data.pop("section_label", None)
        await goto_courses(update, context)
        return

    if data == "reg:back:levels":
        context.user_data.pop("section_key", None)
        context.user_data.pop("section_label", None)
        await goto_levels(query, context)
        return

    if data == "reg:back:review":
        await show_review(update, context)
        return

    # Choose course
    if data.startswith("reg:course:"):
        course_key = data.split(":")[2]
        if course_key not in COURSES:
            await query.edit_message_text(
                "Noto'g'ri kurs tanlandi. Qaytadan urinib ko'ring.")
            return
        context.user_data["course_key"] = course_key
        context.user_data["course_label"] = COURSES[course_key]
        context.user_data.pop("level_key", None)
        context.user_data.pop("level_label", None)
        context.user_data.pop("section_key", None)
        context.user_data.pop("section_label", None)

        if course_key in COURSES_WITH_LEVEL:
            await goto_levels(query, context)
        else:
            await goto_sections(query, context)
        return

    # Choose level (only EN/DE)
    if data.startswith("reg:level:"):
        level_key = data.split(":")[2]
        if level_key not in LEVELS:
            await query.edit_message_text(
                "Noto'g'ri daraja tanlandi. Qaytadan urinib ko'ring.")
            return
        context.user_data["level_key"] = level_key
        context.user_data["level_label"] = LEVELS[level_key]
        await goto_sections(query, context)
        return

    # Choose section
    if data.startswith("reg:section:"):
        section_key = data.split(":")[2]
        course_key = context.user_data.get("course_key")
        valid_keys = (
            SECTIONS_ENGLISH if course_key == "english" else
            SECTIONS_GERMAN if course_key == "german" else SECTIONS_OTHERS)
        if section_key not in valid_keys:
            await query.edit_message_text(
                "Noto'g'ri bo'lim tanlandi. Qaytadan urinib ko'ring.")
            return
        context.user_data["section_key"] = section_key
        context.user_data["section_label"] = valid_keys[section_key]
        await ask_full_name(update, context)
        return

    # Review actions
    if data == "reg:confirm":
        required = [
            "course_key", "course_label", "section_label", "full_name", "age", "phone"
        ]
        if context.user_data.get("course_key") in COURSES_WITH_LEVEL:
            required.append("level_label")
        missing = [k for k in required if not context.user_data.get(k)]
        if missing:
            await query.edit_message_text(
                "Ma'lumotlar yetarli emas. Iltimos, qaytadan boshlang: /start")
            context.user_data.clear()
            return

        u = update.effective_user
        d = context.user_data
        try:
            with SessionLocal() as session:
                reg = Registration(
                    tg_user_id=u.id,
                    username=u.username,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    full_name=d["full_name"],
                    age=int(d["age"]),
                    phone=d["phone"],
                    course=d["course_label"],
                    level=d.get("level_label"),
                    section=d["section_label"],
                )
                session.add(reg)
                session.commit()
        except Exception as e:
            logger.exception("DB error: %s", e)
            await query.edit_message_text(
                "Server xatosi yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."
            )
            return

        await query.edit_message_text(
            "🎉 *Tabriklaymiz!* Siz ro'yxatdan o'tdingiz.\n"
            "Tez orada siz bilan telefon raqamingiz orqali bog'lanamiz.",
            parse_mode="Markdown")

        try:
            admin_text = build_admin_text(context.user_data, update.effective_user)
            await context.bot.send_message(chat_id=ADMIN_ID, text
