import os
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

usuarios = {}

# ======================
# BIENVENIDA
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    usuarios[user.id] = {
        "username": user.username,
        "registro": datetime.now(),
        "partidos": 0
    }

    texto = f"""
🔥 Bienvenido a Underground FUT {user.first_name}

⚠️ IMPORTANTE:
Debes leer las reglas antes de jugar.

/reglas → Ver reglamento completo

🚨 El incumplimiento supone expulsión y pérdida de saldo.
"""
    await update.message.reply_text(texto)


# ======================
# REGLAS COMPLETAS
# ======================

async def reglas(update: Update, context: ContextTypes.DEFAULT_TYPE):

    texto = """📜 REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT

🔞 Reglamento General
Solo mayores de 18 años.
Es obligatorio grabar TODOS los partidos.
Sin grabación → NO hay derecho a reclamar.
Underground Fut puede retransmitir en Twitch.

🤖 Emparejamiento
Debes tener usuario en Telegram (@usuario) y usar el bot.

💰 Pagos
Prohibido multicuentas.
Sistema antifraude activo.
Fraude = expulsión + pérdida de saldo.
Pago ANTES del partido.
Premios en máximo 12h.

⚽ Reglas de Partido
Modo: Amistoso online
Duración: 6 min por parte
Sin modificar ajustes
SIN empate (prórroga y penaltis)
Solo Ultimate Team
Prohibido sliders/handicap
Solo 1 vs 1
Prohibido perder tiempo

⏱ Tiempo para jugar
15 min para contactar
1h para jugar

🔌 Desconexiones

Si pierde y se desconecta → pierde
Si gana y se desconecta → repetir
Empate → repetir
Con rojas → gana quien tenga más jugadores

❌ Fair Play
Prohibido insultar
Prohibido bugs
Prohibido perder tiempo
Prohibido desconectarse
"""
    await update.message.reply_text(texto)


# ======================
# SISTEMA BÁSICO ANTITRAMPAS
# ======================

async def registrar_partido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in usuarios:
        await update.message.reply_text("Usa /start primero")
        return

    usuarios[user.id]["partidos"] += 1

    # 🚨 Ejemplo detección básica (puedes mejorar luego)
    if usuarios[user.id]["partidos"] > 50:
        await update.message.reply_text("⚠️ Actividad sospechosa detectada")

    await update.message.reply_text("✅ Partido registrado")


# ======================
# INFO USUARIO
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
# LOOP ESTABLE (SIN ERROR)
# ======================

async def auto_loop():
    while True:
        print("Bot activo...")
        await asyncio.sleep(60)


# ======================
# MAIN CORRECTO
# ======================

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reglas", reglas))
    app.add_handler(CommandHandler("jugar", registrar_partido))
    app.add_handler(CommandHandler("perfil", perfil))

    # LOOP BIEN HECHO
    asyncio.create_task(auto_loop())

    print("Bot iniciado correctamente")
    await app.run_polling()


# ======================
# ARRANQUE
# ======================

if __name__ == "__main__":
    asyncio.run(main())
