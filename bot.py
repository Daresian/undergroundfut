import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

usuarios = {}
cola = {5: [], 10: [], 20: [], 50: [], 100: []}
partidas = {}

# ======================
# REGLAS EXACTAS (NO TOCADAS)
# ======================

RULES_1 = """REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT Reglamento General La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch. Reglas de Emparejamiento en Telegram Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente."""

RULES_2 = """Reglas de Pago Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas. Reglas de Partido Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team."""

RULES_3 = """Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón; los administradores revisarán las grabaciones y sancionarán con la pérdida del partido a quien infrinja esta norma. Tiempo para Jugar Tras realizar el emparejamiento, los usuarios dispondrán de un máximo de 15 minutos para ponerse en contacto y acordar el inicio del partido. Una vez hecho el “match”, tendrán un máximo de 1 hora para jugar y comunicar el resultado. Desconexiones Es imprescindible que ambos jugadores graben los partidos para conservar el derecho a reclamar en caso de disputa. Desconexión Aparentemente Involuntaria 1. Si se desconecta el jugador que va perdiendo, la victoria se otorgará al jugador que va ganando. 2. Si se desconecta el jugador que va ganando, el partido se repetirá. 3. En caso de empate con ambos equipos jugando 11 contra 11, el partido se reiniciará con la misma alineación y se jugará el tiempo restante. 4. En caso de empate y que uno de los equipos tenga una o más tarjetas rojas, la victoria será adjudicada al jugador que conserve los 11 jugadores o que tenga menos tarjetas rojas. Desconexión Voluntaria (Abandono de partida) 1. En caso de desconexión voluntaria, la victoria será concedida al jugador que mantiene la conexión, independientemente del resultado en el momento de la desconexión. Fair Play • Está prohibido insultar. Comportamiento tóxico. Expulsión Inmediata de la comunidad. • No se permite el uso de bugs. • La pérdida de tiempo intencional está sancionada. • No está permitido desconectarse del partido de forma injustificada."""

# ======================
# START + ACEPTAR REGLAS
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Aceptar reglas", callback_data="accept")]]
    await update.message.reply_text(
        RULES_1 + "\n\n" + RULES_2 + "\n\n" + RULES_3,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def aceptar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    usuarios[user.id] = {
        "username": user.username,
        "jugando": False,
    }

    keyboard = [
        [
            InlineKeyboardButton("PLAY 5", callback_data="play_5"),
            InlineKeyboardButton("PLAY 10", callback_data="play_10"),
        ],
        [
            InlineKeyboardButton("PLAY 20", callback_data="play_20"),
            InlineKeyboardButton("PLAY 50", callback_data="play_50"),
            InlineKeyboardButton("PLAY 100", callback_data="play_100"),
        ],
    ]

    await query.message.reply_text(
        f"Bienvenido @{user.username}", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ======================
# COLAS + MATCH
# ======================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    amount = int(query.data.split("_")[1])

    if usuarios[user.id]["jugando"]:
        await query.answer("Ya estás en partida o cola")
        return

    cola[amount].append(user.id)
    usuarios[user.id]["jugando"] = True

    if len(cola[amount]) >= 2:
        u1 = cola[amount].pop(0)
        u2 = cola[amount].pop(0)

        partida_id = f"{u1}_{u2}"
        partidas[partida_id] = {
            "players": [u1, u2],
            "estado": "playing",
            "reportes": [],
        }

        keyboard = [
            [InlineKeyboardButton("Soy ganador", callback_data=f"win_{partida_id}")]
        ]

        for uid in [u1, u2]:
            await context.bot.send_message(
                uid,
                f"Match encontrado contra @{usuarios[u2 if uid==u1 else u1]['username']}",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
    else:
        await query.answer(f"En cola {amount}€...")

# ======================
# RESULTADO
# ======================

async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    partida_id = query.data.split("_", 1)[1]

    partida = partidas.get(partida_id)

    if user.id in partida["reportes"]:
        await query.answer("Ya reportaste")
        return

    partida["reportes"].append(user.id)

    if len(partida["reportes"]) == 2:
        partida["estado"] = "finished"

        for uid in partida["players"]:
            usuarios[uid]["jugando"] = False

        if ADMIN_ID:
            await context.bot.send_message(
                ADMIN_ID, f"Partida finalizada: {partida_id}"
            )

        await query.message.reply_text("Resultado confirmado")

    else:
        await query.answer("Esperando rival...")

# ======================
# MAIN
# ======================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(aceptar, pattern="accept"))
    app.add_handler(CallbackQueryHandler(play, pattern="play_"))
    app.add_handler(CallbackQueryHandler(resultado, pattern="win_"))

    print("Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()
