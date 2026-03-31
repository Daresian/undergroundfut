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
The Underground Fut Community is strictly for people over 18 years old. Both participants must record all matches, as recordings are the only valid proof in case of disputes. If a player does not record, they lose the right to claim money. Underground Fut reserves the right to stream matches via Twitch.
"""

RULES_2 = """📜 EMPAREJAMIENTO Y PAGOS

🇪🇸
Reglas de Emparejamiento en Telegram
Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente @Futelite_bot. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.

Reglas de Pago
Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será abonado en un plazo máximo de 12 horas.

🇬🇧
Matchmaking & Payments
Each player must have a Telegram username (@username) and activate the bot @Futelite_bot.

Multiple accounts and match fixing are strictly prohibited. Any fraud attempt results in immediate ban and loss of funds. Payment must be completed before matchmaking. Funds are held until result validation (max 12h).
"""

RULES_3 = """📜 PARTIDOS, DESCONECTES Y FAIR PLAY

🇪🇸
Reglas de Partido
Los partidos se disputarán en modo amistoso online, con configuración por defecto y duración de 6 minutos por parte. No se permiten empates (prórroga y penaltis obligatorios). Solo se permite Ultimate Team.

Está prohibido el uso de sliders, hacks o cualquier manipulación. Los partidos son 1 vs 1. No se permite perder tiempo.

Tiempo para jugar
15 minutos para contactar
1 hora para jugar

Desconexiones
Si pierde → pierde
Si gana → repetir
Empate → repetir
Abandono voluntario → pierde

Fair Play
Prohibido insultar, usar bugs o abandonar partidos injustificadamente.

🇬🇧
Match Rules
Online friendly mode, default settings, 6 minutes per half. No draws (extra time + penalties required). Only Ultimate Team allowed.

No sliders, hacks or manipulation. Matches are strictly 1v1. Time wasting is forbidden.

Time Limits
15 minutes to contact
1 hour to play

Disconnections
Losing player disconnects → loss
Winning player disconnects → replay
Draw → replay
Voluntary quit → loss

Fair Play
No insults, exploits or unjustified disconnections.
"""

# ================= NUEVO USUARIO =================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:

        kb = [[InlineKeyboardButton("👉 Activar Bot", url=BOT_LINK)]]

        await update.message.reply_text(
            f"👋 Bienvenido {get_name(user)}\n\nPulsa el botón y escribe /start",
            reply_markup=InlineKeyboardMarkup(kb)
        )

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
    q = update.callback_query
    await q.answer()

    user = q.from_user
    amount = int(q.data.replace("p", ""))

    if not is_authorized(user.id, amount):

        try:
            await context.bot.send_message(
                user.id,
                f"💳 Debes ingresar {amount}€ en:\n{PAYPAL_LINK}\n\n"
                f"IMPORTANTE: Indica tu usuario:\n{get_name(user)}"
            )
        except:
            pass

        kb = [[
            InlineKeyboardButton(f"✅ Autorizar {amount}€", callback_data=f"admin_ok_{user.id}_{amount}"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"admin_no_{user.id}")
        ]]

        await context.bot.send_message(
            GROUP_ID,
            f"💳 {get_name(user)} quiere jugar {amount}€",
            reply_markup=InlineKeyboardMarkup(kb)
        )

        return

    queue[amount].append(user)
    await q.message.reply_text("⏳ En cola")

# ================= PANEL ADMIN =================

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    data = q.data.split("_")

    if data[1] == "ok":
        user_id = int(data[2])
        amount = int(data[3])

        authorize_user(user_id, amount)

        await context.bot.send_message(user_id, f"✅ Autorizado Play {amount}")
        await q.message.edit_text("✅ Pago validado")

    elif data[1] == "no":
        await q.message.edit_text("❌ Cancelado")

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))

    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^admin_"))

    app.run_polling()

if __name__ == "__main__":
    main()
