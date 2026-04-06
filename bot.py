# ================= IMPORTS =================
import logging
import os
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1003882941029
ADMIN_ID = 13493800
PAYPAL_LINK = "https://paypal.me/TU_LINK_AQUI"

logging.basicConfig(level=logging.INFO)

# ================= DB =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    accepted_rules INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    p1 INTEGER,
    p2 INTEGER,
    amount INTEGER,
    r1 TEXT,
    r2 TEXT,
    status TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    p1 INTEGER,
    p2 INTEGER,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (p1,p2)
)
""")

conn.commit()

# ================= UTILS =================

def create_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (uid,))
    conn.commit()

def has_accepted(uid):
    cursor.execute("SELECT accepted_rules FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r and r[0] == 1

async def get_name(context, uid):
    try:
        user = await context.bot.get_chat(uid)
        return f"@{user.username}" if user.username else str(uid)
    except:
        return str(uid)

def check_fraud(p1, p2):
    cursor.execute("SELECT count FROM history WHERE p1=? AND p2=?", (p1,p2))
    row = cursor.fetchone()

    if row:
        if row[0] >= 3:
            return True
        cursor.execute("UPDATE history SET count=count+1 WHERE p1=? AND p2=?", (p1,p2))
    else:
        cursor.execute("INSERT INTO history(p1,p2,count) VALUES (?,?,1)", (p1,p2))

    conn.commit()
    return False

# ================= WELCOME =================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        create_user(user.id)

        await update.message.reply_html(
            f"""👋 Bienvenido {user.first_name}

👉 Activa el bot:
https://t.me/{context.bot.username}"""
        )

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    create_user(uid)

    kb = [[InlineKeyboardButton("✅ Acepto", callback_data="accept")]]
    await update.message.reply_text("Acepta reglas", reply_markup=InlineKeyboardMarkup(kb))

# ================= ACCEPT =================

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    cursor.execute("UPDATE users SET accepted_rules=1 WHERE user_id=?", (uid,))
    conn.commit()

    await q.message.edit_text("Escribe PLAY para jugar")

# ================= PLAY =================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if not has_accepted(uid):
        return await update.message.reply_text("Debes aceptar reglas")

    kb = [
        [InlineKeyboardButton("5€", callback_data="play_5"),
         InlineKeyboardButton("10€", callback_data="play_10")],
        [InlineKeyboardButton("20€", callback_data="play_20"),
         InlineKeyboardButton("50€", callback_data="play_50")],
        [InlineKeyboardButton("100€", callback_data="play_100")]
    ]

    await update.message.reply_text("Elige cantidad", reply_markup=InlineKeyboardMarkup(kb))

# ================= MATCH =================

queue = {5:[],10:[],20:[],50:[],100:[]}

async def try_match(amount, context):
    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        if check_fraud(p1,p2):
            await context.bot.send_message(ADMIN_ID, f"🚨 Posible trampa {p1}-{p2}")
            return

        cursor.execute("""
        INSERT INTO matches (p1,p2,amount,status,created_at)
        VALUES (?,?,?,?,?)
        """,(p1,p2,amount,"playing",datetime.utcnow().isoformat()))
        conn.commit()

        match_id = cursor.lastrowid

        kb = [[
            InlineKeyboardButton("🏆 Gané", callback_data=f"win_{match_id}"),
            InlineKeyboardButton("❌ Perdí", callback_data=f"lose_{match_id}")
        ]]

        for p in [p1,p2]:
            await context.bot.send_message(p, f"Match {amount}€", reply_markup=InlineKeyboardMarkup(kb))

# ================= RESULT =================

async def process_result(match_id, context):
    cursor.execute("SELECT p1,p2,amount,r1,r2 FROM matches WHERE match_id=?", (match_id,))
    p1,p2,amount,r1,r2 = cursor.fetchone()

    if not r1 or not r2:
        return

    if r1 == r2:
        cursor.execute("UPDATE matches SET status='dispute' WHERE match_id=?", (match_id,))
        conn.commit()

        await context.bot.send_message(ADMIN_ID, f"⚠️ DISPUTA match {match_id}")
        return

    winner = p1 if r1 == "win" else p2
    name = await get_name(context, winner)

    total = amount * 2
    win = int(total * 0.7)  # 30% comisión

    cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (win,winner))
    conn.commit()

    await context.bot.send_message(
        GROUP_ID,
        f"🎉 {name} gana {win}€"
    )

# ================= BUTTON =================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if data == "accept":
        return await accept(update, context)

    if data.startswith("play_"):
        amount = int(data.split("_")[1])

        await context.bot.send_message(uid, f"Envía {amount}€:\n{PAYPAL_LINK}")

        kb = [[InlineKeyboardButton("Confirmar", callback_data=f"payok_{uid}_{amount}")]]
        await context.bot.send_message(ADMIN_ID, f"Pago {uid}", reply_markup=InlineKeyboardMarkup(kb))

    if data.startswith("payok"):
        if uid != ADMIN_ID:
            return

        _, u, amount = data.split("_")
        u = int(u)
        amount = int(amount)

        queue[amount].append(u)
        await context.bot.send_message(u, "Buscando rival...")
        await try_match(amount, context)

    if data.startswith("win") or data.startswith("lose"):
        match_id = int(data.split("_")[1])

        cursor.execute("SELECT p1,p2 FROM matches WHERE match_id=?", (match_id,))
        p1,p2 = cursor.fetchone()

        field = "r1" if uid == p1 else "r2"
        val = "win" if "win" in data else "lose"

        cursor.execute(f"UPDATE matches SET {field}=? WHERE match_id=?", (val,match_id))
        conn.commit()

        await process_result(match_id, context)

# ================= ADMIN =================

async def reset_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("UPDATE users SET accepted_rules=0")
    conn.commit()

    await update.message.reply_text("Usuarios reseteados")

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset_users", reset_users))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.Regex("(?i)^play$"), play))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()
