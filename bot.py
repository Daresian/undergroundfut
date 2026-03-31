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

# ================= REGLAS COMPLETAS =================

RULES_1 = """📜 REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT

🇪🇸
Reglamento General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch.

🇬🇧
General Rules
The Underground Fut Community is strictly for people over 18 years old. Both players must record all matches, as recordings are the only valid proof in case of disputes. If a player does not record, they lose the right to claim any money. Underground Fut reserves the right to stream matches on Twitch.
"""

RULES_2 = """📜 EMPAREJAMIENTO Y PAGOS

🇪🇸
Reglas de Emparejamiento en Telegram
Para participar, cada jugador debe tener usuario en Telegram (@usuario) y activar el bot @Futelite_bot.

Reglas de Pago
Prohibido tener varias cuentas o pactar partidos. El sistema detecta fraude. Cualquier intento supondrá expulsión inmediata y pérdida de saldo. El pago debe realizarse antes de jugar. El dinero queda retenido hasta validación y se paga en máximo 12h.

🇬🇧
Matchmaking & Payments
Players must have a Telegram username and activate the bot @Futelite_bot.

Multiple accounts and match fixing are forbidden. Fraud leads to immediate ban and loss of funds. Payment must be made before playing. Funds are held until validation (max 12h).
"""

RULES_3 = """📜 PARTIDOS, DESCONECIONES Y FAIR PLAY

🇪🇸
Reglas de Partido
Modo amistoso online, 6 min por parte, sin empate (prórroga y penaltis). Solo Ultimate Team. Prohibido sliders, hacks o manipulación. Solo 1vs1. Prohibido perder tiempo.

Tiempo:
15 min para contactar
1h para jugar

Desconexiones:
Si pierde → pierde
Si gana → repetir
Empate → repetir
Abandono voluntario → pierde

Fair Play:
Prohibido insultar, usar bugs o abandonar.

🇬🇧
Match Rules
Online friendly mode, 6 min halves, no draws (extra time + penalties). Ultimate Team only. No sliders/hacks. Strict 1v1. No time wasting.

Time:
15 min contact
1h to play

Disconnects:
Losing player disconnect → loss
Winning → replay
Draw → replay
Quit → loss

Fair Play:
No insults, exploits or quitting.
"""

# ================= NUEVO USUARIO =================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:

        kb = [[InlineKeyboardButton("👉 Activar Bot", url=BOT_LINK)]]

        await update.message.reply_text(
            f"👋 Bienvenido {get_name(user)}\n\nPulsa el botón y escribe /start",
            reply_markup=InlineKeyboardMarkup(kb)
        )

        try:
            await context.bot.send_message(
                user.id,
                f"👉 Activa el bot aquí:\n{BOT_LINK}\nEscribe /start"
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

    await q.message.reply_text("✅ Ya puedes jugar. Ve al grupo y escribe PLAY")

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
                    f"💳 Debes ingresar {amount}€ aquí:\n{PAYPAL_LINK}"
                )

                await q.message.reply_text("💳 Revisa tu privado para pagar")

            except:
                await q.message.reply_text(f"Abre el bot primero:\n{BOT_LINK}")

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
        f"✅ Autorizado Play {amount}"
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
                f"🏆 Ganador: {get_name(winner)} 🎉"
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
