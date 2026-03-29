import os
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 13493800
GROUP_ID = -1001234567890
BOT_USERNAME = "@futelite_bot"
PAYPAL_LINK = "https://paypal.me/bucefalo74"

COMMISSION = 0.30
CONFIRM_TIME = 900

# ================= DATA =================
queues = {5: [], 10: [], 20: [], 50: [], 100: []}
balances = {}
rules_step = {}
matches = {}
pending_results = {}
last_opponent = {}

# ================= REGLAS COMPLETAS =================
RULES_1 = """REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT
Reglamento General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch.

Reglas de Emparejamiento en Telegram
Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.
"""

RULES_2 = """Reglas de Pago
Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas.

Reglas de Partido
Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team.
"""

RULES_3 = """Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón.

Tiempo para Jugar
Tras el match: 15 min para contactar + 1h para jugar.

Desconexiones y Fair Play aplican estrictamente.

Pulsa el botón para aceptar."""
# ================= HELPERS =================
def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

def btn_continue():
    return InlineKeyboardMarkup([[InlineKeyboardButton("CONTINUAR ▶️", callback_data="cont")]])

def btn_next():
    return InlineKeyboardMarkup([[InlineKeyboardButton("SIGUIENTE ▶️", callback_data="next")]])

def btn_accept():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ ACEPTO LAS REGLAS", callback_data="accept")]])

def result_buttons(match_id, p1_name, p2_name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🏆 Gana {p1_name}", callback_data=f"win_{match_id}_1")],
        [InlineKeyboardButton(f"🏆 Gana {p2_name}", callback_data=f"win_{match_id}_2")]
    ])

def init_user(uid):
    if uid not in balances:
        balances[uid] = 0
        rules_step[uid] = 0

# ================= BIENVENIDA =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await context.bot.send_message(
            user.id,
            f"""👋 Bienvenido a UNDERGROUND FUT

1. Busca {BOT_USERNAME}
2. Pulsa START
3. Vuelve al grupo

👇 Pulsa continuar""",
            reply_markup=btn_continue()
        )

# ================= COMANDOS PRO =================
async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    chat = update.message.chat
    uid = user.id

    if text == "/id":
        await update.message.reply_text(f"🆔 Tu ID: {uid}")
        return True

    if text == "/grupo":
        await update.message.reply_text(f"📢 ID grupo: {chat.id}")
        return True

    if text == "/info":
        await update.message.reply_text(f"""
👤 {get_name(user)}
🆔 {uid}
💬 Chat: {chat.id}
📌 Tipo: {chat.type}
""")
        return True

    if text == "/saldo":
        init_user(uid)
        await update.message.reply_text(f"💰 Saldo: {balances[uid]}€")
        return True

    return False

# ================= BOTONES =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == "cont":
        await query.message.edit_text(RULES_1, reply_markup=btn_next())
        rules_step[uid] = 1

    elif query.data == "next" and rules_step[uid] == 1:
        await query.message.edit_text(RULES_2, reply_markup=btn_next())
        rules_step[uid] = 2

    elif query.data == "next" and rules_step[uid] == 2:
        await query.message.edit_text(RULES_3, reply_markup=btn_accept())
        rules_step[uid] = 3

    elif query.data == "accept":
        rules_step[uid] = 4
        await query.message.edit_text(f"""
✅ Reglas aceptadas

💰 Paga aquí:
{PAYPAL_LINK}

Escribe PAY

🎮 PLAY 5 / 10 / 20 / 50 / 100
""")

    elif query.data.startswith("win_"):
        _, match_id, player = query.data.split("_")

        if match_id in pending_results:
            return

        p1, p2, amount, names = matches[match_id]
        winner = p1 if player == "1" else p2

        pending_results[match_id] = {
            "winner": winner,
            "time": time.time()
        }

        await query.edit_message_text("⏳ Resultado enviado. Esperando validación...")

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id
    name = get_name(user)

    init_user(uid)

    if await comandos(update, context):
        return

    if uid == ADMIN_ID:
        if text == "ADMIN":
            await update.message.reply_text(f"""
PARTIDOS ACTIVOS:
{matches}

PENDIENTES:
{pending_results}

SALDOS:
{balances}
""")

        if text.startswith("OK"):
            _, user_id, amount = text.split()
            balances[int(user_id)] += int(amount)

    if text == "PAY":
        await context.bot.send_message(ADMIN_ID, f"💰 Pago de {name} ({uid})")

    if text.startswith("PLAY"):
        amount = int(text.split()[1])

        if balances[uid] < amount:
            await update.message.reply_text("❌ Saldo insuficiente")
            return

        queues[amount].append((uid, name))

        if len(queues[amount]) >= 2:
            (p1, n1) = queues[amount].pop(0)
            (p2, n2) = queues[amount].pop(0)

            balances[p1] -= amount
            balances[p2] -= amount

            match_id = str(time.time())
            matches[match_id] = (p1, p2, amount, (n1, n2))

            await context.bot.send_message(
                GROUP_ID,
                f"⚔️ MATCH\n\n{n1} vs {n2}",
                reply_markup=result_buttons(match_id, n1, n2)
            )

# ================= AUTO =================
async def auto_confirm(app):
    while True:
        now = time.time()

        for match_id in list(pending_results.keys()):
            if now - pending_results[match_id]["time"] > CONFIRM_TIME:
                winner = pending_results[match_id]["winner"]
                p1, p2, amount, names = matches[match_id]

                prize = int(amount * 2 * (1 - COMMISSION))
                balances[winner] += prize

                winner_name = names[0] if winner == p1 else names[1]

                await app.bot.send_message(
                    GROUP_ID,
                    f"🎉 {winner_name} gana {prize}€ 💰"
                )

                del matches[match_id]
                del pending_results[match_id]

        await asyncio.sleep(30)

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.job_queue.run_once(lambda ctx: asyncio.create_task(auto_confirm(app)), 1)

    app.run_polling()

if __name__ == "__main__":
    main()
