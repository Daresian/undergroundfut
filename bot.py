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
user_data_cache = {}
matches = {}
user_match = {}
user_in_queue = set()
match_id_counter = 1

def get_name(user_id):
    user = user_data_cache.get(user_id)
    if user:
        return f"@{user.username}" if user.username else user.first_name
    return f"user_{user_id}"

def is_authorized(user_id, amount):
    cursor.execute("SELECT authorized_amount FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] == amount

def authorize_user(user_id, amount):
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (user_id, amount))
    conn.commit()

# ================= REGLAS EXACTAS =================

RULES_1 = """📜 REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT

🇪🇸
Reglamento General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch.

🇬🇧
General Rules
The Underground Fut Community is strictly for people over 18 years old. It is mandatory that both players record all matches, as recordings are the only valid proof in case of disputes. If a player does not record, they lose the right to claim money. Underground Fut reserves the right to stream matches on Twitch.
"""

RULES_2 = """📜 REGLAS DE EMPAREJAMIENTO Y PAGOS

🇪🇸
Reglas de Emparejamiento en Telegram
Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente @Futelite_bot . Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.

Reglas de Pago
Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas.

🇬🇧
Matchmaking Rules
Each player must have a Telegram username (@username) and activate the bot @Futelite_bot.

Payment Rules
Multiple accounts and match fixing are strictly prohibited. The system monitors behavior to detect fraud. Any attempt will result in a permanent ban and loss of funds. Payment must be completed before matchmaking. Funds remain locked until validation (max 12h).
"""

RULES_3 = """📜 PARTIDOS, DESCONECTES Y FAIR PLAY

🇪🇸
Reglas de Partido
Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team.

Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón.

Tiempo para Jugar
15 minutos para contactar
1 hora para jugar

Desconexiones
Si pierde → pierde
Si gana → repetir
Empate → repetir
Abandono → pierde

Fair Play
Prohibido insultar, usar bugs o abandonar.

🇬🇧
Match Rules
Online friendly match, default settings, 6 minutes per half. No draws allowed. Only Ultimate Team.

No sliders or manipulation. Matches are strictly 1v1.

Time
15 minutes to contact
1 hour to play

Disconnections
Lose → lose
Win → replay
Draw → replay
Quit → lose

Fair Play
No insults, bugs or quitting.
"""

# ================= MATCH =================

async def try_match(amount, context):
    global match_id_counter

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        user_in_queue.discard(p1)
        user_in_queue.discard(p2)

        match_id = match_id_counter
        match_id_counter += 1

        matches[match_id] = {
            "p1": p1,
            "p2": p2,
            "amount": amount,
            "status": "playing",
            "r1": None,
            "r2": None
        }

        user_match[p1] = match_id
        user_match[p2] = match_id

        await context.bot.send_message(
            GROUP_ID,
            f"⚔️ MATCH {amount}€\n{get_name(p1)} vs {get_name(p2)}\n\nTenéis 1h para jugar"
        )

# ================= BOT =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data_cache[user.id] = user

    kb = [[InlineKeyboardButton("Aceptar / Accept", callback_data="accept")]]
    await update.message.reply_text(RULES_1, reply_markup=InlineKeyboardMarkup(kb))

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text(RULES_2)
    await q.message.reply_text(RULES_3)
    await q.message.reply_text("✅ Ya puedes jugar. Ve al grupo y escribe PLAY")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data_cache[user.id] = user

    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"), InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"), InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]
    await update.message.reply_text("Selecciona partido", reply_markup=InlineKeyboardMarkup(kb))

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    user_data_cache[user.id] = user

    amount = int(q.data.replace("p", ""))

    if not is_authorized(user.id, amount):

        await q.message.reply_text("❗ Ve al BOT para pagar")

        try:
            await context.bot.send_message(
                user.id,
                f"💳 Debes pagar {amount}€ en:\n{PAYPAL_LINK}\n\nIndica tu usuario:\n@{user.username}"
            )
        except:
            pass

        kb = [[InlineKeyboardButton("Autorizar", callback_data=f"admin_ok_{user.id}_{amount}")]]

        await context.bot.send_message(
            GROUP_ID,
            f"{get_name(user.id)} quiere jugar {amount}€",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if user.id in user_in_queue:
        await q.message.reply_text("⚠️ Ya estás en cola")
        return

    queue[amount].append(user.id)
    user_in_queue.add(user.id)

    await q.message.reply_text("⏳ Buscando rival...")
    await try_match(amount, context)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id not in user_match:
        await update.message.reply_text("❌ No tienes partido activo")
        return

    match_id = user_match[user.id]
    match = matches[match_id]

    if len(context.args) == 0:
        await update.message.reply_text("Usa: /report win o /report lose")
        return

    result = context.args[0]

    if match["p1"] == user.id:
        if match["r1"]:
            await update.message.reply_text("⚠️ Ya reportaste")
            return
        match["r1"] = result
    else:
        if match["r2"]:
            await update.message.reply_text("⚠️ Ya reportaste")
            return
        match["r2"] = result

    if match["r1"] and match["r2"]:
        if match["r1"] == match["r2"]:
            await context.bot.send_message(GROUP_ID, "🏆 Resultado confirmado")
        else:
            await context.bot.send_message(GROUP_ID, "⚠️ Conflicto en resultado")

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    data = q.data.split("_")
    user_id = int(data[2])
    amount = int(data[3])

    authorize_user(user_id, amount)

    await context.bot.send_message(user_id, f"✅ Autorizado {amount}€")
    await q.message.edit_text("Pago validado")

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))

    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^admin_"))

    app.run_polling()

if __name__ == "__main__":
    main()
