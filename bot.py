import logging
import sqlite3
import os
import psutil


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)


# ================= ANTI DUPLICADOS =================
current_pid = os.getpid()
for proc in psutil.process_iter():
    try:
        if proc.pid != current_pid and "python" in proc.name().lower():
            proc.kill()
    except:
        pass


# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PAYPAL_LINK = "https://paypal.me/bucefalo74"


logging.basicConfig(level=logging.INFO)


# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    activated INTEGER DEFAULT 0,
    rules INTEGER DEFAULT 0,
    paid INTEGER DEFAULT 0
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS queue (
    user_id INTEGER,
    amount INTEGER
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    p1 INTEGER,
    p2 INTEGER,
    amount INTEGER,
    r1 TEXT,
    r2 TEXT,
    status TEXT
)
""")


conn.commit()


# ================= BIENVENIDA =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        try:
            await context.bot.send_message(
                user.id,
                f"👋 Hola {user.first_name}\n\n"
                "⚠️ Debes activar el bot o NO podrás jugar\n"
                "⚠️ You MUST activate the bot or you CANNOT play\n\n"
                "👉 Escribe /start"
            )
        except:
            pass


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user


    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)",
                   (user.id, user.username, 0, 0, 0))
    conn.commit()


    keyboard = [[InlineKeyboardButton("ACTIVAR", callback_data="activate")]]


    await update.message.reply_text(
        f"👋 Bienvenido {user.first_name}\n\nActiva el bot:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= ACTIVAR =================
async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()


    cursor.execute("UPDATE users SET activated=1 WHERE user_id=?", (q.from_user.id,))
    conn.commit()


    keyboard = [[InlineKeyboardButton("ACEPTAR REGLAS", callback_data="rules")]]


    await q.message.reply_text("📜 Acepta las reglas:", reply_markup=InlineKeyboardMarkup(keyboard))


# ================= REGLAS =================
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()


    cursor.execute("UPDATE users SET rules=1 WHERE user_id=?", (q.from_user.id,))
    conn.commit()


    await q.message.reply_text("✅ Reglas aceptadas\nEscribe PLAY")


# ================= PLAY =================
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user


    cursor.execute("SELECT activated, rules FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()


    if not data or data[0] == 0 or data[1] == 0:
        return


    keyboard = [
        [InlineKeyboardButton("4€", callback_data="4")],
        [InlineKeyboardButton("10€", callback_data="10")],
        [InlineKeyboardButton("20€", callback_data="20")],
        [InlineKeyboardButton("50€", callback_data="50")],
        [InlineKeyboardButton("100€", callback_data="100")]
    ]


    await update.message.reply_text("💰 Elige cantidad", reply_markup=InlineKeyboardMarkup(keyboard))


# ================= SELECCIÓN =================
async def select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()


    amount = int(q.data)
    context.user_data["amount"] = amount


    await q.message.reply_text(f"💳 Ingresa {amount}€:\n{PAYPAL_LINK}\n\nEscribe PAGADO")


# ================= PAGADO =================
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    amount = context.user_data.get("amount")


    if not amount:
        return


    await context.bot.send_message(ADMIN_ID, f"/confirm {user.id} {amount}")
    await update.message.reply_text("⏳ Esperando confirmación")


# ================= CONFIRM =================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return


    try:
        _, user_id, amount = update.message.text.split()
        user_id = int(user_id)
        amount = int(amount)
    except:
        return


    cursor.execute("UPDATE users SET paid=1 WHERE user_id=?", (user_id,))
    conn.commit()


    cursor.execute("SELECT user_id FROM queue WHERE amount=?", (amount,))
    rival = cursor.fetchone()


    if rival:
        rival_id = rival[0]


        cursor.execute("DELETE FROM queue WHERE user_id=?", (rival_id,))
        conn.commit()


        cursor.execute("INSERT INTO matches (p1,p2,amount,status) VALUES (?,?,?,?)",
                       (user_id, rival_id, amount, "playing"))
        conn.commit()


        await context.bot.send_message(user_id, "🎮 Rival encontrado")
        await context.bot.send_message(rival_id, "🎮 Rival encontrado")
    else:
        cursor.execute("INSERT INTO queue VALUES (?,?)", (user_id, amount))
        conn.commit()


        await context.bot.send_message(user_id, "⏳ Esperando rival")


# ================= RESULTADOS =================
async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text


    if "-" not in text:
        return


    cursor.execute("SELECT * FROM matches WHERE (p1=? OR p2=?) AND status='playing'",
                   (user.id, user.id))
    match = cursor.fetchone()


    if not match:
        return


    match_id = match[0]


    if match[1] == user.id:
        cursor.execute("UPDATE matches SET r1=? WHERE id=?", (text, match_id))
    else:
        cursor.execute("UPDATE matches SET r2=? WHERE id=?", (text, match_id))


    conn.commit()


    cursor.execute("SELECT r1,r2,amount,p1,p2 FROM matches WHERE id=?", (match_id,))
    r1, r2, amount, p1, p2 = cursor.fetchone()


    if r1 and r2:
        if r1 == r2:
            g1, g2 = map(int, r1.split("-"))
            winner = p1 if g1 > g2 else p2


            prize = amount * 2 * 0.7


            await context.bot.send_message(winner, f"🎉 GANADOR\nPremio: {prize}€")


            cursor.execute("UPDATE matches SET status='finished' WHERE id=?", (match_id,))
            conn.commit()
        else:
            await context.bot.send_message(ADMIN_ID, f"⚠️ DISPUTA match {match_id}")


# ================= RESET =================
async def reset_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return


    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM matches")
    cursor.execute("DELETE FROM queue")
    conn.commit()


    await update.message.reply_text("✅ BD reseteada")


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset_users", reset_users))
    app.add_handler(CommandHandler("confirm", confirm))


    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))


    app.add_handler(CallbackQueryHandler(activate, pattern="activate"))
    app.add_handler(CallbackQueryHandler(rules, pattern="rules"))
    app.add_handler(CallbackQueryHandler(select_amount, pattern="^[0-9]+$"))


    app.add_handler(MessageHandler(filters.Regex("(?i)^play$"), play))
    app.add_handler(MessageHandler(filters.Regex("(?i)^pagado$"), paid))


    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, result))


    print("✅ BOT FUNCIONANDO")
    app.run_polling()


if __name__ == "__main__":
    main()
