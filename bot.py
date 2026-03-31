import logging
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

GROUP_ID = -1003882941029
ADMIN_ID = 13493800
BOT_LINK = "https://t.me/Futelite_bot"
PAYPAL_LINK = "https://paypal.me/bucefalo74"

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    authorized_amount INTEGER
)
""")
conn.commit()

# ================= MEMORIA =================

queue = {5: [], 10: [], 20: [], 50: [], 100: []}
matches = {}
user_match = {}
match_id_counter = 1

def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

def is_authorized(user_id, amount):
    cursor.execute("SELECT authorized_amount FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] == amount

def authorize_user(user_id, amount):
    cursor.execute("INSERT OR REPLACE INTO users (user_id, authorized_amount) VALUES (?,?)", (user_id, amount))
    conn.commit()

# ================= REGLAS =================

RULES_1 = """📜 REGLAMENTO UNDERGROUND FUT

🇪🇸
+18 obligatorio
Grabar partidos obligatorio
Sin grabación → pierdes derecho a reclamar
Posible retransmisión en Twitch

Emparejamiento:
Necesitas Telegram + activar bot

Pagos:
Prohibido fraude o multicuentas
Pago antes de jugar
Validación hasta 12h

---

🇬🇧
18+ only
Recording required
No recording → no claim
Matches may be streamed

Matchmaking:
Telegram + bot required

Payments:
No fraud
Pay before play
Validation up to 12h
"""

RULES_2 = """📜 REGLAS DE PARTIDO

🇪🇸
Amistoso online
6 min partes
Sin empate
Solo Ultimate Team
Sin hacks
1 vs 1 obligatorio

Tiempo:
15 min contacto
1h jugar

---

🇬🇧
Online friendly
6 min halves
No draws
Ultimate Team only
No hacks
1v1 only

Time:
15 min contact
1h play
"""

RULES_3 = """📜 FAIR PLAY

🇪🇸
Desconexión:
Pierde el que iba perdiendo
Si ganaba → repetir

Voluntaria → pierde

Prohibido:
Insultos
Bugs
Abandonar

---

🇬🇧
Disconnect:
Losing player loses
Winning → replay

Voluntary quit → loss

No:
Insults
Exploits
Quit
"""

# ================= NUEVO USUARIO =================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:

        kb = [[InlineKeyboardButton("👉 Activar Bot", url=BOT_LINK)]]

        await update.message.reply_text(
            f"👋 Bienvenido {get_name(user)}\n\n"
            "Pulsa el botón y escribe /start\n\n"
            "Click and press /start",
            reply_markup=InlineKeyboardMarkup(kb)
        )

        try:
            await context.bot.send_message(
                user.id,
                f"👉 Activa el bot:\n{BOT_LINK}\n/start"
            )
        except:
            pass

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("Aceptar / Accept", callback_data="accept")]]
    await update.message.reply_text(RULES_1, reply_markup=InlineKeyboardMarkup(kb))

# ================= ACEPTAR =================

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text(RULES_2)
    await q.message.reply_text(RULES_3)

    await q.message.reply_text(
        "✅ Ya puedes jugar\n\nVe al grupo y escribe PLAY\n\nYou can play now"
    )

# ================= PLAY =================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"), InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"), InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]

    await update.message.reply_text("Selecciona partido", reply_markup=InlineKeyboardMarkup(kb))

# ================= SELECT =================

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global match_id_counter

    q = update.callback_query
    await q.answer()

    user = q.from_user
    amount = int(q.data.replace("p", ""))

    if user.id != ADMIN_ID:

        if not is_authorized(user.id, amount):

            try:
                await context.bot.send_message(
                    user.id,
                    f"💳 Debes ingresar {amount}€:\n{PAYPAL_LINK}\n\n"
                    f"Send {amount}€ here"
                )

                await q.message.reply_text("💳 Revisa tu privado para pagar")

            except:
                await q.message.reply_text(f"Abre el bot primero:\n{BOT_LINK}")

            return

    if user.id in user_match:
        await q.message.reply_text("Ya estás en partida")
        return

    queue[amount].append(user)
    await q.message.reply_text("⏳ En cola")

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        match_id = match_id_counter
        match_id_counter += 1

        matches[match_id] = {"p1": p1, "p2": p2, "reports": {}}
        user_match[p1.id] = match_id
        user_match[p2.id] = match_id

        kb = [[
            InlineKeyboardButton(f"{get_name(p1)} gana", callback_data=f"win_{match_id}_{p1.id}"),
            InlineKeyboardButton(f"{get_name(p2)} gana", callback_data=f"win_{match_id}_{p2.id}")
        ],
        [InlineKeyboardButton("⚠️ Disputa", callback_data=f"draw_{match_id}")]
        ]

        await context.bot.send_message(
            GROUP_ID,
            f"🔥 MATCH {amount}€\n{get_name(p1)} vs {get_name(p2)}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= AUTORIZAR =================

async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Responde con /autorizar 10")
        return

    amount = int(context.args[0])
    user = update.message.reply_to_message.from_user

    authorize_user(user.id, amount)

    await context.bot.send_message(
        user.id,
        f"✅ Autorizado Play {amount}\n\nAuthorized Play {amount}"
    )

    await update.message.reply_text("OK autorizado")

# ================= RESULTADO =================

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user
    _, match_id, winner_id = q.data.split("_")

    match_id = int(match_id)
    winner_id = int(winner_id)

    match = matches.get(match_id)
    if not match:
        return

    match["reports"][user.id] = winner_id

    if len(match["reports"]) == 2:
        votes = list(match["reports"].values())

        if votes[0] == votes[1]:
            winner = match["p1"] if match["p1"].id == votes[0] else match["p2"]

            await context.bot.send_message(
                GROUP_ID,
                f"🏆 Ganador: {get_name(winner)}"
            )
        else:
            await context.bot.send_message(GROUP_ID, "⚠️ DISPUTA")

        del user_match[match["p1"].id]
        del user_match[match["p2"].id]
        del matches[match_id]

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("autorizar", autorizar))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))
    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))
    app.add_handler(CallbackQueryHandler(win, pattern="^win_"))

    app.run_polling()

if __name__ == "__main__":
    main()
