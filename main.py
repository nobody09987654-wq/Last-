# filepath: main.py
import os
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
from datetime import datetime

# Bot token va admin ID Render env’dan olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ----------------------- Keyboards -----------------------
def kb_register():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Ro'yxatdan o'tish", callback_data="reg:start")
    ]])

def kb_review():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data="reg:confirm"),
            InlineKeyboardButton("✏️ O'zgartirish", callback_data="reg:edit"),
        ],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="reg:cancel")]
    ])

def kb_back_cancel(back_data="reg:back"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Ortga", callback_data=back_data),
            InlineKeyboardButton("❌ Bekor qilish", callback_data="reg:cancel")
        ]
    ])

# ----------------------- Handlers -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "Assalomu alaykum!\n"
        "*ITeach Academy*ga xush kelibsiz! 🎓\n\n"
        "Bizning o'quv jamoamizga qo'shilish va ro'yxatdan o'tish uchun pastdagi tugmani bosing."
    )
    await update.message.reply_text(
        welcome,
        reply_markup=kb_register(),
        parse_mode="Markdown"
    )
    context.user_data.clear()

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Bekor qilish
    if data == "reg:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Ro'yxatdan o'tish bekor qilindi.")
        return

    # Orqaga
    if data == "reg:back":
        step = context.user_data.get("prev_step")
        if step == "ask_name":
            await query.edit_message_text("✍️ Iltimos, to'liq ism-familiyangizni kiriting:", reply_markup=kb_back_cancel())
            context.user_data["step"] = "ask_name"
        elif step == "ask_age":
            await query.edit_message_text("🎂 Yoshingizni kiriting:", reply_markup=kb_back_cancel())
            context.user_data["step"] = "ask_age"
        elif step == "ask_phone":
            kb = ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Raqamni ulashish", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await query.edit_message_text(
                "📞 Telefon raqamingizni kiriting yoki pastdagi tugma orqali yuboring:",
                reply_markup=kb
            )
            context.user_data["step"] = "ask_phone"
        return

    # Ro'yxatdan boshlash
    if data == "reg:start":
        await query.edit_message_text("✍️ Iltimos, to'liq ism-familiyangizni kiriting:", reply_markup=kb_back_cancel())
        context.user_data["step"] = "ask_name"
        return

    # Tasdiqlash
    if data == "reg:confirm":
        user_data = context.user_data
        admin_text = (
            f"🔔 Yangi o'quvchi ro'yxatdan o'tdi\n"
            f"👤 Ism: {user_data.get('full_name')}\n"
            f"🎂 Yosh: {user_data.get('age')}\n"
            f"📱 Telefon: {user_data.get('phone')}\n"
            f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
        await query.edit_message_text("🎉 Ro'yxatdan o'tish muvaffaqiyatli!\nTez orada siz bilan bog'lanamiz.")
        context.user_data.clear()
        return

    # Qayta tahrirlash
    if data == "reg:edit":
        await query.edit_message_text("✏️ Ma’lumotlarni qayta kiriting. Ism-familiya bilan boshlang:", reply_markup=kb_back_cancel())
        context.user_data["step"] = "ask_name"
        return

# ----------------------- Collect user input -----------------------
async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "ask_name":
        context.user_data["full_name"] = update.message.text
        context.user_data["prev_step"] = "ask_name"
        context.user_data["step"] = "ask_age"
        await update.message.reply_text("🎂 Yoshingizni kiriting:", reply_markup=kb_back_cancel())

    elif step == "ask_age":
        context.user_data["age"] = update.message.text
        context.user_data["prev_step"] = "ask_age"
        context.user_data["step"] = "ask_phone"
        kb = ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Raqamni ulashish", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await update.message.reply_text(
            "📞 Telefon raqamingizni kiriting yoki pastdagi tugma orqali yuboring:",
            reply_markup=kb
        )

    elif step == "ask_phone":
        phone = update.message.contact.phone_number if update.message.contact else update.message.text
        context.user_data["phone"] = phone
        context.user_data["prev_step"] = "ask_phone"
        context.user_data["step"] = "review"

        text = (
            f"🧾 Ma'lumotlaringiz:\n"
            f"• 👤 Ism-familiya: {context.user_data.get('full_name')}\n"
            f"• 🎂 Yosh: {context.user_data.get('age')}\n"
            f"• 📱 Telefon: {context.user_data.get('phone')}"
        )
        await update.message.reply_text(text, reply_markup=kb_review(), parse_mode="Markdown", reply_markup=kb_review())

# ----------------------- Main -----------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data))
    app.add_handler(MessageHandler(filters.CONTACT, collect_data))

    app.run_polling()

if __name__ == "__main__":
    main()
