import os
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 13493800
GROUP_ID = -1001234567890
BOT_USERNAME = "futelite_bot"
PAYPAL_LINK = "https://paypal.me/bucefalo74"

COMMISSION = 0.30
CONFIRM_TIME = 900

queues = {5: [], 10: [], 20: [], 50: [], 100: []}
balances = {}
users_state = {}
matches = {}
pending_results = {}

RULES_1 = """REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT

Reglamento General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años.
Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro.
Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo.
Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch.

Reglas de Emparejamiento en Telegram
Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente.
Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.
"""

RULES_2 = """Reglas de Pago
Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas.
El sistema monitoriza patrones de juego para detectar posibles fraudes.
Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado.

El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero.
El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas.

Reglas de Partido
Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego.
No está permitido modificar los ajustes, y la duración será de 6 minutos por parte.
Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario.
Solo se pueden utilizar equipos Ultimate Team.
"""

RULES_3 = """Está prohibida la utilización de sliders y hándicaps.
En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado.

Los partidos son exclusivamente 1 contra 1.
No se permite la participación de dos o más personas en un mismo equipo.

No está permitida la pérdida de tiempo mediante la posesión del balón.

Tiempo para jugar:
15 minutos para contactar
1 hora para jugar

Desconexiones:

Si se desconecta el jugador que va perdiendo → pierde
Si se desconecta el jugador que va ganando → se repite
Empate → repetir
Abandono → pierde quien abandona

Fair Play:
Prohibido insultar
Prohibido bugs
Prohibido perder tiempo
Prohibido desconectarse injustificadamente
"""

def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

def btn(text, data):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)]])

def result_buttons(match_id, p1, p2):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🏆 {p1}", callback_data=f"win_{match_id}_1")],
        [InlineKeyboardButton(f"🏆 {p2}", callback_data=f"win_{match_id}_2")]
    ])

def init_user(uid):
    if uid not in balances:
        balances[uid] = 0
        users_state[uid] = {"accepted": False, "playing": False}

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await context.bot.send_message(
            user.id,
            f"👋 Bienvenido a UNDERGROUND FUT\n\n1. Busca {BOT_USERNAME}\n2. Pulsa START\n3. Vuelve al grupo",
            reply_markup=btn("CONTINUAR ▶️", "r1")
        )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == "r1":
        await query.message.edit_text(RULES_1, reply_markup=btn("SIGUIENTE ▶️", "r2"))

    elif query.data == "r2":
        await query.message.edit_text(RULES_2, reply_markup=btn("SIGUIENTE ▶️", "r3"))

    elif query.data == "r3":
        await query.message.edit_text(RULES_3, reply_markup=btn("ACEPTAR", "ok"))

    elif query.data == "ok":
        users_state[uid]["accepted"] = True
        await query.message.edit_text(f"✅ Reglas aceptadas\n💰 {PAYPAL_LINK}\nEscribe PAY o PLAY")

    elif query.data.startswith("win_"):
        _, match_id, player = query.data.split("_")

        if match_id in pending_results:
            return

        match = matches.get(match_id)
        if not match or match["status"] != "playing":
            return

        winner = match["p1"] if player == "1" else match["p2"]

        pending_results[match_id] = {"winner": winner, "time": time.time()}
        match["status"] = "pending"

        await query.edit_message_text("⏳ Resultado enviado")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id
    name = get_name(user)

    init_user(uid)

    if text == "PAY":
        await context.bot.send_message(ADMIN_ID, f"💰 Pago de {name}")

    if text.startswith("PLAY"):
        parts = text.split()

        if len(parts) < 2 or not parts[1].isdigit():
            await update.message.reply_text("Usa: PLAY 5 / 10 / 20 / 50 / 100")
            return

        amount = int(parts[1])

        if not users_state[uid]["accepted"]:
            await update.message.reply_text("Acepta reglas primero")
            return

        if users_state[uid]["playing"]:
            await update.message.reply_text("Ya estás jugando")
            return

        if amount not in queues:
            await update.message.reply_text("Cantidad inválida")
            return

        queues[amount].append((uid, name))
        await update.message.reply_text(f"Buscando rival {amount}€")

        if len(queues[amount]) >= 2:
            (p1, n1) = queues[amount].pop(0)
            (p2, n2) = queues[amount].pop(0)

            match_id = str(time.time())

            matches[match_id] = {
                "p1": p1,
                "p2": p2,
                "names": (n1, n2),
                "amount": amount,
                "status": "playing"
            }

            users_state[p1]["playing"] = True
            users_state[p2]["playing"] = True

            await context.bot.send_message(
                GROUP_ID,
                f"⚔️ {n1} vs {n2} | {amount}€",
                reply_markup=result_buttons(match_id, n1, n2)
            )

async def auto_loop(app):
    while True:
        now = time.time()

        for match_id in list(pending_results.keys()):
            if now - pending_results[match_id]["time"] > CONFIRM_TIME:

                match = matches[match_id]
                winner = pending_results[match_id]["winner"]

                prize = int(match["amount"] * 2 * (1 - COMMISSION))

                n1, n2 = match["names"]
                winner_name = n1 if winner == match["p1"] else n2

                await app.bot.send_message(
                    GROUP_ID,
                    f"🏆 {winner_name} gana {prize}€"
                )

                users_state[match["p1"]]["playing"] = False
                users_state[match["p2"]]["playing"] = False

                del matches[match_id]
                del pending_results[match_id]

        await asyncio.sleep(30)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.create_task(auto_loop(app))

    app.run_polling()

if __name__ == "__main__":
    main()
