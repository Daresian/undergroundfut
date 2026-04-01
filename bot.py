import logging
import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    p1 INTEGER,
    p2 INTEGER,
    amount INTEGER,
    status TEXT,
    r1 TEXT,
    r2 TEXT
)
""")
conn.commit()

# ================= MEMORIA =================

queue = {5: [], 10: [], 20: [], 50: [], 100: []}
user_cache = {}
user_in_queue = set()
user_match = {}
match_id_counter = 1

# ================= REGLAS COMPLETAS =================

RULES_1 = """📜 REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT

🇪🇸
Reglamento General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch.

🇬🇧
General Rules
The Underground Fut Community is strictly for people over 18 years old. Both players must record all matches, as recordings are the only valid proof in case of disputes. If a player does not record, they lose the right to claim money. Underground Fut reserves the right to upload or stream matches on Twitch.
"""

RULES_2 = """📜 EMPAREJAMIENTO Y PAGOS

🇪🇸
Reglas de Emparejamiento en Telegram
Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente @Futelite_bot. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.

Reglas de Pago
Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas.

🇬🇧
Matchmaking Rules
To participate, each player must have a Telegram username (@username) and activate the bot @Futelite_bot. This is mandatory to be matched correctly.

Payment Rules
Multiple accounts and match fixing are strictly prohibited. The system monitors behavior to detect fraud. Any attempt will result in immediate ban and loss of all funds. Payment must be completed before matchmaking. Funds remain locked until the result is validated, and the prize will be released within a maximum of 12 hours.
"""

RULES_3 = """📜 PARTIDOS, DESCONECTES Y FAIR PLAY

🇪🇸
Reglas de Partido
Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team.

Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1. Tampoco está permitida la pérdida de tiempo mediante la posesión del balón.

Tiempo para Jugar
15 minutos para contactar
1 hora para jugar

Desconexiones
Es obligatorio grabar.

Desconexión Involuntaria
- Si pierde → pierde
- Si gana → repetir
- Empate → repetir

Desconexión Voluntaria
- Abandono → pierde

Fair Play
Prohibido insultar, usar bugs o abandonar injustificadamente.

🇬🇧
Match Rules
Matches must be played as online friendlies using default settings. Each half is 6 minutes. No draws allowed (extra time/penalties required). Only Ultimate Team is allowed.

Sliders and handicaps are strictly forbidden. Violations result in expulsion and loss of funds. Matches are strictly 1v1. Time wasting is not allowed.

Time
15 minutes to contact
1 hour to play

Disconnections
Recording is mandatory.

Unintentional Disconnect:
- Losing player → loses
- Winning player → replay
- Draw → replay

Intentional Disconnect:
- Quit → loss

Fair Play
No insults, no bugs, no unjustified quitting.
"""

# ================= UTILS =================

def get_name(uid):
    u = user_cache.get(uid)
    if u:
        return f"@{u.username}" if u.username else u.first_name
    return str(uid)

def is_authorized(uid, amount):
    cursor.execute("SELECT authorized_amount FROM users WHERE user_id=?", (uid,))
    row = cursor.fetchone()
    return row and row[0] == amount

def authorize(uid, amount):
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (uid, amount))
    conn.commit()

# ================= WELCOME =================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for u in update.message.new_chat_members:
        user_cache[u.id] = u
        kb = [[InlineKeyboardButton("👉 Activar Bot", url=BOT_LINK)]]
        await update.message.reply_text(
            f"👋 Bienvenido {get_name(u.id)}\n\nPulsa y escribe /start",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_cache[update.effective_user.id] = update.effective_user
    kb = [[InlineKeyboardButton("Aceptar / Accept", callback_data="ok")]]
    await update.message.reply_text(RULES_1, reply_markup=InlineKeyboardMarkup(kb))

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(RULES_2)
    await q.message.reply_text(RULES_3)
    await q.message.reply_text("✅ Ya puedes jugar → escribe PLAY en el grupo")

# ================= RESTO SISTEMA (IGUAL QUE PRO) =================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"),
         InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"),
         InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]
    await update.message.reply_text("Selecciona apuesta", reply_markup=InlineKeyboardMarkup(kb))

async def try_match(amount, context):
    global match_id_counter

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        match_id = match_id_counter
        match_id_counter += 1

        cursor.execute(
            "INSERT INTO matches VALUES (?,?,?,?,?,?,?)",
            (match_id, p1, p2, amount, "playing", None, None)
        )
        conn.commit()

        user_match[p1] = match_id
        user_match[p2] = match_id
        user_in_queue.discard(p1)
        user_in_queue.discard(p2)

        await context.bot.send_message(
            GROUP_ID,
            f"⚔️ MATCH {amount}€\n{get_name(p1)} vs {get_name(p2)}"
        )

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    user_cache[user.id] = user
    amount = int(q.data.replace("p", ""))

    if not is_authorized(user.id, amount):
        await q.message.reply_text("❗ Ve al BOT a pagar")

        await context.bot.send_message(
            user.id,
            f"💳 Paga {amount}€ en:\n{PAYPAL_LINK}\n@{user.username}"
        )

        kb = [[InlineKeyboardButton("Autorizar", callback_data=f"a_{user.id}_{amount}")]]
        await context.bot.send_message(
            GROUP_ID,
            f"{get_name(user.id)} quiere jugar {amount}€",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if user.id in user_in_queue:
        return

    queue[amount].append(user.id)
    user_in_queue.add(user.id)

    await q.message.reply_text("⏳ Buscando rival...")
    await try_match(amount, context)

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in user_match:
        await update.message.reply_text("❌ No tienes partido")
        return

    match_id = user_match[user.id]

    cursor.execute("SELECT * FROM matches WHERE match_id=?", (match_id,))
    m = cursor.fetchone()

    if not context.args:
        return

    result = context.args[0]

    if user.id == m[1]:
        cursor.execute("UPDATE matches SET r1=? WHERE match_id=?", (result, match_id))
    else:
        cursor.execute("UPDATE matches SET r2=? WHERE match_id=?", (result, match_id))

    conn.commit()

    cursor.execute("SELECT r1,r2 FROM matches WHERE match_id=?", (match_id,))
    r1, r2 = cursor.fetchone()

    if r1 and r2:
        if r1 == r2:
            cursor.execute("UPDATE matches SET status='finished' WHERE match_id=?", (match_id,))
            await context.bot.send_message(GROUP_ID, "🏆 Resultado confirmado")
        else:
            cursor.execute("UPDATE matches SET status='disputed' WHERE match_id=?", (match_id,))
            await context.bot.send_message(GROUP_ID, "⚠️ PARTIDO EN DISPUTA")

    conn.commit()

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM matches WHERE status='disputed'")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No hay disputas")
        return

    msg = "⚠️ DISPUTAS:\n"
    for r in rows:
        msg += f"Match {r[0]} → {get_name(r[1])} vs {get_name(r[2])}\n"

    await update.message.reply_text(msg)

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    _, uid, amount = q.data.split("_")
    authorize(int(uid), int(amount))

    await context.bot.send_message(int(uid), "✅ Autorizado")
    await q.message.edit_text("Pago OK")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))

    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(accept, pattern="ok"))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^a_"))

    app.run_polling()

if __name__ == "__main__":
    main()
