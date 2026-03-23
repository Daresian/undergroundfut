import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# Colas de jugadores
queue_5 = []
queue_10 = []

# Bienvenida automática
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await update.message.reply_text(
            "Bienvenido 👋 / Welcome 👋\n"
            "PLAY para jugar / Type PLAY to play"
        )

# Manejo de mensajes
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    user = update.message.from_user
    username = user.username if user.username else user.first_name

    if text == "PLAY":
        await update.message.reply_text(
            "Elige: PLAY 5 o PLAY 10\nChoose: PLAY 5 or PLAY 10"
        )

    elif text == "PLAY 5":
        queue_5.append(username)
        await update.message.reply_text(f"{username} añadido a cola 5€")

        if len(queue_5) >= 2:
            p1 = queue_5.pop(0)
            p2 = queue_5.pop(0)

            await update.message.reply_text(
                f"⚔️ Match listo / Match ready\n"
                f"{p1} vs {p2}\n"
                f"Entrada: 5€ → Ganador: 8€"
            )

    elif text == "PLAY 10":
        queue_10.append(username)
        await update.message.reply_text(f"{username} añadido a cola 10€")

        if len(queue_10) >= 2:
            p1 = queue_10.pop(0)
            p2 = queue_10.pop(0)

            await update.message.reply_text(
                f"⚔️ Match listo / Match ready\n"
                f"{p1} vs {p2}\n"
                f"Entrada: 10€ → Ganador: 16€"
            )

# Main
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
