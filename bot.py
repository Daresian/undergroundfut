import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# ================== CONFIG ==================
TOKEN = os.getenv("BOT_TOKEN")

GROUP_ID = -1003882941029
ADMIN_ID = 13493800

# ================== LOGS ==================
logging.basicConfig(level=logging.INFO)

# ================== ESTADOS ==================
queue = {5: [], 10: [], 20: [], 50: [], 100: []}
active_matches = {}  # match_id -> data
user_in_match = {}   # user_id -> match_id
match_counter = 1

# ================== REGLAS ==================
RULES_1 = """REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT Reglamento General La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch. Reglas de Emparejamiento en Telegram Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente."""
RULES_2 = """Reglas de Pago Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas. Reglas de Partido Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team."""
RULES_3 = """Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón; los administradores revisarán las grabaciones y sancionarán con la pérdida del partido a quien infrinja esta norma. Tiempo para Jugar Tras realizar el emparejamiento, los usuarios dispondrán de un máximo de 15 minutos para ponerse en contacto y acordar el inicio del partido. Una vez hecho el “match”, tendrán un máximo de 1 hora para jugar y comunicar el resultado. Desconexiones Es imprescindible que ambos jugadores graben los partidos para conservar el derecho a reclamar en caso de disputa. Desconexión Aparentemente Involuntaria 1. Si se desconecta el jugador que va perdiendo, la victoria se otorgará al jugador que va ganando. 2. Si se desconecta el jugador que va ganando, el partido se repetirá. 3. En caso de empate con ambos equipos jugando 11 contra 11, el partido se reiniciará con la misma alineación y se jugará el tiempo restante. 4. En caso de empate y que uno de los equipos tenga una o más tarjetas rojas, la victoria será adjudicada al jugador que conserve los 11 jugadores o que tenga menos tarjetas rojas. Desconexión Voluntaria (Abandono de partida) 1. En caso de desconexión voluntaria, la victoria será concedida al jugador que mantiene la conexión, independientemente del resultado en el momento de la desconexión. Fair Play • Está prohibido insultar. Comportamiento tóxico. Expulsión Inmediata de la comunidad. • No se permite el uso de bugs. • La pérdida de tiempo intencional está sancionada. • No está permitido desconectarse del partido de forma injustificada."""

WELCOME = """👋 Bienvenido a Underground Fut

1. Escribe PLAY
2. Elige partido
3. Espera rival
4. Contacta por privado
5. Juega
6. Reporta ganador

⏱ 15 min contacto / 1h juego"""

# ================== NUEVO USUARIO ==================
async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        try:
            keyboard = [[InlineKeyboardButton("✅ Aceptar", callback_data="accept")]]
            await context.bot.send_message(
                chat_id=user.id,
                text=WELCOME,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except:
            pass

# ================== ACEPTAR ==================
async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(RULES_1)
    await q.message.reply_text(RULES_2)
    await q.message.reply_text(RULES_3)
    await q.message.reply_text("✅ Ya puedes jugar. Escribe PLAY en el grupo.")

# ================== PLAY ==================
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"), InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"), InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]
    await update.message.reply_text("Selecciona partido:", reply_markup=InlineKeyboardMarkup(kb))

# ================== COLA + MATCH ==================
async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global match_counter
    q = update.callback_query
    await q.answer()

    user = q.from_user
    amount = int(q.data.replace("p", ""))

    if user.id in user_in_match:
        await q.message.reply_text("⚠️ Ya estás en un partido")
        return

    if user in queue[amount]:
        await q.message.reply_text("⚠️ Ya estás en cola")
        return

    queue[amount].append(user)
    await q.message.reply_text(f"✅ @{user.username} en cola {amount}€")

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        match_id = match_counter
        match_counter += 1

        active_matches[match_id] = {
            "p1": p1,
            "p2": p2,
            "amount": amount,
            "status": "playing",
            "reported": []
        }

        user_in_match[p1.id] = match_id
        user_in_match[p2.id] = match_id

        kb = [[
            InlineKeyboardButton(f"Gana @{p1.username}", callback_data=f"win_{match_id}_{p1.id}"),
            InlineKeyboardButton(f"Gana @{p2.username}", callback_data=f"win_{match_id}_{p2.id}")
        ]]

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🔥 MATCH 🔥\n@{p1.username} vs @{p2.username}\n💰 {amount}€\nContactad por privado",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================== GANADOR ==================
async def report_win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    _, match_id, winner_id = q.data.split("_")
    match_id = int(match_id)
    winner_id = int(winner_id)

    if match_id not in active_matches:
        return

    match = active_matches[match_id]

    if user.id not in [match["p1"].id, match["p2"].id]:
        return

    if user.id in match["reported"]:
        await q.answer("Ya has votado", show_alert=True)
        return

    match["reported"].append(user.id)

    if len(match["reported"]) == 2:
        winner = match["p1"] if match["p1"].id == winner_id else match["p2"]

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"🏆 @{winner.username} gana el partido de {match['amount']}€"
        )

        # limpiar
        del user_in_match[match["p1"].id]
        del user_in_match[match["p2"].id]
        del active_matches[match_id]

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play$"), play))
    app.add_handler(CallbackQueryHandler(select, pattern="p"))
    app.add_handler(CallbackQueryHandler(report_win, pattern="win_"))

    print("BOT FUNCIONANDO PERFECTO")
    app.run_polling()

if __name__ == "__main__":
    main()
