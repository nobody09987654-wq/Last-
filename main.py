# filepath: main.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from models import Registration, SessionLocal
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Ro‘yxatdan o‘tish 📝", callback_data="register")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "O‘quv kursimizga xush kelibsiz.\n"
        "Ro‘yxatdan o‘tish uchun tugmani bosing 👇",
        reply_markup=reply_markup
    )


# Callback handler
async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "register":
        await query.edit_message_text("📝 Ismingizni kiriting:")
        context.user_data["step"] = "ask_name"


# Foydalanuvchi ma'lumotlarini yig‘ish
async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "ask_name":
        context.user_data["full_name"] = update.message.text
        context.user_data["step"] = "ask_age"
        await update.message.reply_text("📅 Yoshingizni kiriting:")

    elif step == "ask_age":
        if not update.message.text.isdigit():
            await update.message.reply_text("❌ Yoshingiz raqamda bo‘lishi kerak. Qaytadan kiriting:")
            return
        context.user_data["age"] = int(update.message.text)
        context.user_data["step"] = "ask_phone"
        await update.message.reply_text("📞 Telefon raqamingizni kiriting (masalan: +998901234567):")

    elif step == "ask_phone":
        context.user_data["phone"] = update.message.text

        # --- Ma'lumotlarni DB ga yozish ---
        session = SessionLocal()
        try:
            reg = Registration(
                tg_user_id=update.message.from_user.id,
                username=update.message.from_user.username,
                first_name=update.message.from_user.first_name,
                last_name=update.message.from_user.last_name,
                full_name=context.user_data["full_name"],
                age=context.user_data["age"],
                phone=context.user_data["phone"],
                course="Python",       # vaqtincha fixed
                level="Beginner",      # vaqtincha fixed
                section="Morning"      # vaqtincha fixed
            )
            session.add(reg)
            session.commit()

            await update.message.reply_text(
                "✅ Tabriklaymiz! Siz muvaffaqiyatli ro‘yxatdan o‘tdingiz."
            )

            # Adminni xabardor qilish
            if ADMIN_ID:
                try:
                    await context.bot.send_message(
                        chat_id=int(ADMIN_ID),
                        text=(
                            f"📥 Yangi ro‘yxatdan o‘tuvchi:\n\n"
                            f"👤 Ism: {reg.full_name}\n"
                            f"📅 Yosh: {reg.age}\n"
                            f"📞 Telefon: {reg.phone}\n"
                            f"🆔 UserID: {reg.tg_user_id}"
                        )
                    )
                except Exception as e:
                    print(f"Adminni xabardor qilishda xato: {e}")

        except Exception as e:
            session.rollback()
            await update.message.reply_text(f"❌ Xatolik yuz berdi: {e}")
        finally:
            session.close()

        context.user_data.clear()


# Botni ishga tushirish
def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN topilmadi. .env faylni tekshiring!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_data))

    print("🚀 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
