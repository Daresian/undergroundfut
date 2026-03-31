import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ================== CONFIG ==================
TOKEN = os.getenv("BOT_TOKEN")

# ================== LOGS ==================
logging.basicConfig(level=logging.INFO)

# ================== COMANDO /id ==================
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        f"🆔 CHAT ID DEL GRUPO:\n\n{chat_id}"
    )

# ================== MENSAJE DEBUG ==================
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    await update.message.reply_text(
        f"DEBUG INFO:\nUsuario: @{user.username}\nChat ID: {chat_id}"
    )

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Comando para obtener ID
    app.add_handler(CommandHandler("id", get_chat_id))

    # Mensaje cualquiera (debug opcional)
    app.add_handler(MessageHandler(filters.TEXT, echo))

    print("Bot temporal activo para obtener ID...")
    app.run_polling()

if __name__ == "__main__":
    main()
