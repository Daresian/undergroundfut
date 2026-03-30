import os
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 13493800
GROUP_ID = -1001234567890
BOT_USERNAME = "@futelite_bot"
PAYPAL_LINK = "https://paypal.me/bucefalo74"

COMMISSION = 0.30
CONFIRM_TIME = 900

queues = {5: [], 10: [], 20: [], 50: [], 100: []}
balances = {}
users_state = {}
matches = {}
pending_results = {}

RULES_1 = """REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT Reglamento General La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch. Reglas de Emparejamiento en Telegram Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente."""

RULES_2 = """Reglas de Pago Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas. Reglas de Partido Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team."""

RULES_3 = """Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón; los administradores revisarán las grabaciones y sancionarán con la pérdida del partido a quien infrinja esta norma. Tiempo para Jugar Tras realizar el emparejamiento, los usuarios dispondrán de un máximo de 15 minutos para ponerse en contacto y acordar el inicio del partido. Una vez hecho el “match”, tendrán un máximo de 1 hora para jugar y comunicar el resultado. Desconexiones Es imprescindible que ambos jugadores graben los partidos para conservar el derecho a reclamar en caso de disputa. Desconexión Aparentemente Involuntaria 1. Si se desconecta el jugador que va perdiendo, la victoria se otorgará al jugador que va ganando. 2. Si se desconecta el jugador que va ganando, el partido se repetirá. 3. En caso de empate con ambos equipos jugando 11 contra 11, el partido se reiniciará con la misma alineación y se jugará el tiempo restante. 4. En caso de empate y que uno de los equipos tenga una o más tarjetas rojas, la victoria será adjudicada al jugador que conserve los 11 jugadores o que tenga menos tarjetas rojas. Desconexión Voluntaria (Abandono de partida) 1. En caso de desconexión voluntaria, la victoria será concedida al jugador que mantiene la conexión, independientemente del resultado en el momento de la desconexión. Fair Play • Está prohibido insultar. Comportamiento tóxico. Expulsión Inmediata de la comunidad. • No se permite el uso de bugs. • La pérdida de tiempo intencional está sancionada. • No está permitido desconectarse del partido de forma injustificada."""

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
            f"👋 Bienvenido a UNDERGROUND FUT\n\n1. Busca {BOT_USERNAME}\n2. Pulsa START\n3. Vuelve al grupo\n\n👇 Pulsa continuar",
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
        await query.message.edit_text(RULES_3, reply_markup=btn("✅ ACEPTO LAS REGLAS", "ok"))

    elif query.data == "ok":
        users_state[uid]["accepted"] = True
        await query.message.edit_text(f"✅ Reglas aceptadas\n\n💰 Paga aquí:\n{PAYPAL_LINK}\n\nEscribe PAY\n\n🎮 PLAY 5 / 10 / 20 / 50 / 100")

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

        await query.edit_message_text("⏳ Resultado enviado. Esperando validación...")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id
    name = get_name(user)

    init_user(uid)

    if text == "PAY":
        await context.bot.send_message(ADMIN_ID, f"💰 Pago de {name} ({uid})")

    if text.startswith("PLAY"):
        if not users_state[uid]["accepted"]:
            await update.message.reply_text("❌ Debes aceptar las reglas primero")
            return

        if users_state[uid]["playing"]:
            await update.message.reply_text("❌ Ya estás en un partido")
            return

        amount = int(text.split()[1])

        if amount not in queues:
            await update.message.reply_text("❌ Cantidad no válida")
            return

        if balances[uid] < amount:
            await update.message.reply_text("❌ Saldo insuficiente")
            return

        queues[amount].append((uid, name))
        await update.message.reply_text(f"⏳ Buscando rival para {amount}€...")

        if len(queues[amount]) >= 2:
            (p1, n1) = queues[amount].pop(0)
            (p2, n2) = queues[amount].pop(0)

            balances[p1] -= amount
            balances[p2] -= amount

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
                f"⚔️ MATCH\n\n{n1} vs {n2}\n💰 {amount}€",
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
                balances[winner] += prize

                n1, n2 = match["names"]
                winner_name = n1 if winner == match["p1"] else n2

                await app.bot.send_message(
                    GROUP_ID,
                    f"🎉🎊 Felicidades 🎉🎊 {winner_name} ha ganado {prize} € 💰💰"
                )

                users_state[match["p1"]]["playing"] = False
                users_state[match["p2"]]["playing"] = False

                del matches[match_id]
                del pending_results[match_id]

        await asyncio.sleep(30)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    asyncio.create_task(auto_loop(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
