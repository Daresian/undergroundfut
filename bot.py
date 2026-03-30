import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ======================
# CONFIG
# ======================

TOKEN = os.getenv("BOT_TOKEN")

usuarios = {}

# ======================
# REGLAS EXACTAS (TUS TEXTOS)
# ======================

RULES_1 = """REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT Reglamento General La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch. Reglas de Emparejamiento en Telegram Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente."""

RULES_2 = """Reglas de Pago Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas. Reglas de Partido Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team."""

RULES_3 = """Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón; los administradores revisarán las grabaciones y sancionarán con la pérdida del partido a quien infrinja esta norma. Tiempo para Jugar Tras realizar el emparejamiento, los usuarios dispondrán de un máximo de 15 minutos para ponerse en contacto y acordar el inicio del partido. Una vez hecho el “match”, tendrán un máximo de 1 hora para jugar y comunicar el resultado. Desconexiones Es imprescindible que ambos jugadores graben los partidos para conservar el derecho a reclamar en caso de disputa. Desconexión Aparentemente Involuntaria 1. Si se desconecta el jugador que va perdiendo, la victoria se otorgará al jugador que va ganando. 2. Si se desconecta el jugador que va ganando, el partido se repetirá. 3. En caso de empate con ambos equipos jugando 11 contra 11, el partido se reiniciará con la misma alineación y se jugará el tiempo restante. 4. En caso de empate y que uno de los equipos tenga una o más tarjetas rojas, la victoria será adjudicada al jugador que conserve los 11 jugadores o que tenga menos tarjetas rojas. Desconexión Voluntaria (Abandono de partida) 1. En caso de desconexión voluntaria, la victoria será concedida al jugador que mantiene la conexión, independientemente del resultado en el momento de la desconexión. Fair Play • Está prohibido insultar. Comportamiento tóxico. Expulsión Inmediata de la comunidad. • No se permite el uso de bugs. • La pérdida de tiempo intencional está sancionada. • No está permitido desconectarse del partido de forma injustificada."""

# ======================
# /start → BIENVENIDA
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in usuarios:
        usuarios[user.id] = {
            "username": user.username if user.username else "sin_username",
            "registro": datetime.now(),
            "partidos": 0
        }

    texto = f"""
🔥 Bienvenido a Underground FUT {user.first_name}

📜 Usa /reglas para ver el reglamento completo
👤 Usa /perfil para ver tu perfil
🎮 Usa /jugar para registrar partido

⚠️ Es obligatorio grabar todos los partidos
"""
    await update.message.reply_text(texto)

# ======================
# /reglas
# ======================

async def reglas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_1)
    await update.message.reply_text(RULES_2)
    await update.message.reply_text(RULES_3)

# ======================
# /jugar
# ======================

async def jugar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in usuarios:
        await update.message.reply_text("⚠️ Usa /start primero")
        return

    usuarios[user.id]["partidos"] += 1

    if usuarios[user.id]["partidos"] > 100:
        await update.message.reply_text("🚨 Actividad sospechosa detectada")

    await update.message.reply_text("✅ Partido registrado")

# ======================
# /perfil
# ======================

async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in usuarios:
        await update.message.reply_text("No registrado")
        return

    data = usuarios[user.id]

    texto = f"""
👤 Usuario: @{data['username']}
🎮 Partidos: {data['partidos']}
📅 Registro: {data['registro'].strftime("%d/%m/%Y")}
"""
    await update.message.reply_text(texto)

# ======================
# MAIN
# ======================

def main():
    if not TOKEN:
        print("ERROR: Falta BOT_TOKEN")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reglas", reglas))
    app.add_handler(CommandHandler("jugar", jugar))
    app.add_handler(CommandHandler("perfil", perfil))

    print("Bot iniciado correctamente")

    app.run_polling()

# ======================
# ARRANQUE
# ======================

if __name__ == "__main__":
    main()
