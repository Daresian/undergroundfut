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

TOKEN = os.getenv("BOT_TOKEN")

GROUP_ID = -1003882941029
ADMIN_ID = 13493800
BOT_USERNAME = "Futelite_bot"

logging.basicConfig(level=logging.INFO)

queue = {5: [], 10: [], 20: [], 50: [], 100: []}
matches = {}
user_match = {}
users_started = set()
match_id_counter = 1

# ================== MENSAJES ==================

WELCOME_PRIVATE = """👋 Bienvenido a Underground Fut

⚽ Cómo jugar / How to play:

1. Escribe PLAY en el grupo
2. Elige cantidad
3. Espera rival
4. Contacta por privado
5. Juega
6. Reporta ganador

⏱ 15 min contacto / 1h juego

¡Ya puedes jugar!
"""

RULES = """📜 REGLAS / RULES

REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT Reglamento General La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch. Reglas de Emparejamiento en Telegram Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.

Reglas de Pago Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas.

Está prohibida la utilización de sliders y hándicaps...
"""

# ================== NUEVO USUARIO ==================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:

        await update.message.reply_text(
f"""👋 Bienvenido @{user.username}

⚠️ IMPORTANTE / IMPORTANT

Para poder jugar debes activar el bot:

👉 https://t.me/{BOT_USERNAME}
👉 Pulsa START

❗ Si no haces esto no podrás jugar

---

To play you MUST start the bot first.
"""
        )

# ================== START ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    users_started.add(user.id)

    keyboard = [[InlineKeyboardButton("✅ Aceptar reglas / Accept rules", callback_data="accept")]]

    await update.message.reply_text(
        RULES,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== ACCEPT ==================

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text(WELCOME_PRIVATE)

# ================== PLAY ==================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in users_started:
        await update.message.reply_text(
f"""⚠️ Debes activar el bot primero

👉 https://t.me/{BOT_USERNAME}

⚠️ You must start the bot first
"""
        )
        return

    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"), InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"), InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]

    await update.message.reply_text("Selecciona partido / Select match", reply_markup=InlineKeyboardMarkup(kb))

# ================== MATCH ==================

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global match_id_counter

    q = update.callback_query
    await q.answer()

    user = q.from_user
    amount = int(q.data.replace("p", ""))

    if user.id in user_match:
        await q.answer("Ya estás en partida / Already in match", show_alert=True)
        return

    queue[amount].append(user)

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        match_id = match_id_counter
        match_id_counter += 1

        matches[match_id] = {
            "p1": p1,
            "p2": p2,
            "amount": amount,
            "reports": {}
        }

        user_match[p1.id] = match_id
        user_match[p2.id] = match_id

        kb = [[
            InlineKeyboardButton(f"Gana @{p1.username}", callback_data=f"win_{match_id}_{p1.id}"),
            InlineKeyboardButton(f"Gana @{p2.username}", callback_data=f"win_{match_id}_{p2.id}")
        ]]

        await context.bot.send_message(
            GROUP_ID,
            f"""🔥 MATCH {amount}€

@{p1.username} vs @{p2.username}

📩 Contactad por privado / Contact each other privately
"""
            ,
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================== RESULTADO ==================

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Resultado enviado / Result submitted")

    user = q.from_user
    _, match_id, winner_id = q.data.split("_")

    match_id = int(match_id)
    winner_id = int(winner_id)

    match = matches.get(match_id)

    # anti trampas: solo jugadores del match
    if user.id not in [match["p1"].id, match["p2"].id]:
        return

    match["reports"][user.id] = winner_id

    if len(match["reports"]) == 2:
        votes = list(match["reports"].values())

        if votes[0] == votes[1]:
            winner = votes[0]

            username = match["p1"].username if match["p1"].id == winner else match["p2"].username

            await context.bot.send_message(
                GROUP_ID,
                f"""🏆 @{username} gana {match['amount']}€

💰 Pago en proceso / Payment processing"""
            )
        else:
            await context.bot.send_message(
                GROUP_ID,
                "⚠️ DISPUTA DETECTADA / DISPUTE DETECTED"
            )

            await context.bot.send_message(
                ADMIN_ID,
                f"""🚨 DISPUTA

Match {match_id}
@{match['p1'].username} vs @{match['p2'].username}
"""
            )

        # limpiar
        del user_match[match["p1"].id]
        del user_match[match["p2"].id]
        del matches[match_id]

# ================== MAIN ==================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))
    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(win, pattern="^win_"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))

    print("BOT PRO ACTIVO")
    app.run_polling()

if __name__ == "__main__":
    main()
