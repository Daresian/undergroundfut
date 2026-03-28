import os
import time
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 13493800   # ← CAMBIAR
GROUP_ID = -1001234567890  # ← CAMBIAR
BOT_USERNAME = "Futelite_bot"  # ← SIN @
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

# ================= REGLAS (TAL CUAL) =================
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

RULES_3 = """Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón; los administradores revisarán las grabaciones y sancionarán con la pérdida del partido a quien infrinja esta norma.

Tiempo para Jugar
Tras realizar el emparejamiento, los usuarios dispondrán de un máximo de 15 minutos para ponerse en contacto y acordar el inicio del partido. Una vez hecho el “match”, tendrán un máximo de 1 hora para jugar y comunicar el resultado.

Desconexiones
Es imprescindible que ambos jugadores graben los partidos para conservar el derecho a reclamar en caso de disputa.

Desconexión Aparentemente Involuntaria
1. Si se desconecta el jugador que va perdiendo, la victoria se otorgará al jugador que va ganando.
2. Si se desconecta el jugador que va ganando, el partido se repetirá.
3. En caso de empate con ambos equipos jugando 11 contra 11, el partido se reiniciará con la misma alineación y se jugará el tiempo restante.
4. En caso de empate y que uno de los equipos tenga una o más tarjetas rojas, la victoria será adjudicada al jugador que conserve los 11 jugadores o que tenga menos tarjetas rojas.

Desconexión Voluntaria (Abandono de partida)
1. En caso de desconexión voluntaria, la victoria será concedida al jugador que mantiene la conexión, independientemente del resultado en el momento de la desconexión.

Fair Play
• Está prohibido insultar. Comportamiento tóxico. Expulsión Inmediata de la comunidad.
• No se permite el uso de bugs.
• La pérdida de tiempo intencional está sancionada.
• No está permitido desconectarse del partido de forma injustificada.

Responde con ✅ para aceptar
"""

# ================= INIT =================
def init_user(uid):
    if uid not in balances:
        balances[uid] = 0
        rules_step[uid] = 0

# ================= BIENVENIDA =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await context.bot.send_message(user.id, RULES_1)
        rules_step[user.id] = 1

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id

    init_user(uid)

    # ===== REGLAS =====
    if rules_step[uid] == 1:
        await context.bot.send_message(uid, RULES_2)
        rules_step[uid] = 2
        return

    if rules_step[uid] == 2:
        await context.bot.send_message(uid, RULES_3)
        rules_step[uid] = 3
        return

    if rules_step[uid] == 3:
        if text == "✅":
            rules_step[uid] = 4
            await context.bot.send_message(uid, f"""
✅ Reglas aceptadas

💰 Paga aquí:
{PAYPAL_LINK}

Cuando pagues escribe: PAY

🎮 PLAY 5 / 10 / 20 / 50 / 100
""")
        else:
            await context.bot.send_message(uid, "Debes aceptar con ✅")
        return

    if rules_step[uid] != 4:
        return

    # ===== PLAY =====
    if text.upper().startswith("PLAY"):
        amount = int(text.split()[1])

        if balances[uid] < amount:
            return

        queues[amount].append(uid)

        if len(queues[amount]) >= 2:
            p1 = queues[amount].pop(0)
            p2 = queues[amount].pop(0)

            # ANTI TRAMPAS
            if last_opponent.get(p1) == p2:
                return

            last_opponent[p1] = p2
            last_opponent[p2] = p1

            balances[p1] -= amount
            balances[p2] -= amount

            match_id = f"{p1}_{p2}_{time.time()}"
            matches[match_id] = (p1, p2, amount)

            await context.bot.send_message(
                GROUP_ID,
                f"""⚔️ MATCH

Jugador {p1} vs Jugador {p2}

Responder a ESTE mensaje con:

Usuario ganador ✅"""
            )

    # ===== RESULTADO =====
    elif "✅" in text:
        for match_id, (p1, p2, amount) in matches.items():

            if str(p1) in text:
                winner = p1
            elif str(p2) in text:
                winner = p2
            else:
                continue

            pending_results[match_id] = {
                "winner": winner,
                "time": time.time()
            }

# ===== AUTO =====
async def auto_confirm(app):
    while True:
        now = time.time()

        for match_id in list(pending_results.keys()):
            data = pending_results[match_id]

            if now - data["time"] > CONFIRM_TIME:
                winner = data["winner"]
                p1, p2, amount = matches[match_id]

                prize = int(amount * 2 * (1 - COMMISSION))
                balances[winner] += prize

                await app.bot.send_message(
                    GROUP_ID,
                    f"🎉🎊 Felicidades 🎉🎊 Jugador {winner} ha ganado {prize} € 💰💰"
                )

                del matches[match_id]
                del pending_results[match_id]

        await asyncio.sleep(30)

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.job_queue.run_once(lambda ctx: asyncio.create_task(auto_confirm(app)), 1)

    app.run_polling()

if __name__ == "__main__":
    main()
