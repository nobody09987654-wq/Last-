# filepath: main.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from models import Registration, SessionLocal  # models.py bilan bog‘lanadi

# Token Render environmentdan olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN")


# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Ro‘yxatdan o‘tish", callback_data="register")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Assalomu alaykum! Botga xush kelibsiz 👋\n\n"
        "Quyidagi tugmani bosib ro‘yxatdan o‘ting:",
        reply_markup=reply_markup
    )


# Callback handler
async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "register":
        await query.edit_message_text("Ismingizni kiriting:")
        context.user_data["step"] = "ask_name"


# Foydalanuvchi ma'lumotlarini yig‘ish
async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") == "ask_name":
        context.user_data["full_name"] = update.message.text
        context.user_data["step"] = "ask_age"
        await update.message.reply_text("Yoshingizni kiriting:")

    elif context.user_data.get("step") == "ask_age":
        context.user_data["age"] = update.message.text
        context.user_data["step"] = "ask_phone"
        await update.message.reply_text("Telefon raqamingizni kiriting:")

    elif context.user_data.get("step") == "ask_phone":
        context.user_data["phone"] = update.message.text

        # Ma'lumotlarni DB ga yozamiz
        session = SessionLocal()
        reg = Registration(
            tg_user_id=update.message.from_user.id,
            username=update.message.from_user.username,
            first_name=update.message.from_user.first_name,
            last_name=update.message.from_user.last_name,
            full_name=context.user_data["full_name"],
            age=int(context.user_data["age"]),
            phone=context.user_data["phone"],
            course="Python",       # vaqtincha fix qilingan
            level="Beginner",      # vaqtincha fix qilingan
            section="Morning"      # vaqtincha fix qilingan
        )
        session.add(reg)
        session.commit()
        session.close()

        await update.message.reply_text("✅ Ro‘yxatdan o‘tish muvaffaqiyatli tugadi!")
        context.user_data.clear()


# Botni ishga tushirish
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data))

    app.run_polling()


if __name__ == "__main__":
    main()
