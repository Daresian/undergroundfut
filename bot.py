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

# ================= UTIL =================

def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= REGLAS (DIVIDIDAS) =================

RULES_1 = """📜 REGLAMENTO UNDERGROUND FUT

🇪🇸 ESPAÑOL

General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de desacuerdo. Underground Fut puede retransmitir los partidos en Twitch.

Reglas de Emparejamiento
Cada jugador debe tener usuario en Telegram (@usuario) y activar el bot @Futelite_bot.

Reglas de Pago
Prohibido tener múltiples cuentas o pactar partidos. Fraude = expulsión + pérdida total del saldo.
El pago debe hacerse antes del emparejamiento. El dinero queda retenido hasta validación (máx 12h).

---

🇬🇧 ENGLISH

General
The Underground Fut Community is strictly for users over 18 years old. Matches must be recorded. Recording is the only valid proof in disputes. If not recorded, the player loses claim rights. Matches may be streamed on Twitch.

Matchmaking Rules
Users must have a Telegram username (@user) and activate the bot @Futelite_bot.

Payment Rules
Multiple accounts or arranged matches are strictly forbidden. Fraud = ban + loss of funds.
Payments must be done before matchmaking. Funds are held until validation (max 12h).
"""

RULES_2 = """📜 REGLAS DE PARTIDO / MATCH RULES

🇪🇸 ESPAÑOL

Los partidos se juegan en amistoso online con configuración por defecto.
Duración: 6 minutos por parte.
No se permiten empates (prórroga + penaltis).
Solo equipos Ultimate Team.

Prohibido:
- Sliders o hándicaps
- Jugar en equipo (solo 1vs1)
- Perder tiempo intencionadamente

⏱ Tiempo:
15 min para contactar
1 hora para jugar

---

🇬🇧 ENGLISH

Matches are played as online friendlies with default settings.
6 minutes per half.
No draws allowed (extra time + penalties).
Only Ultimate Team squads allowed.

Forbidden:
- Sliders or handicaps
- Playing with multiple players
- Time wasting

⏱ Time:
15 min to contact
1 hour to play
"""

RULES_3 = """📜 DESCONEXIONES Y FAIR PLAY

🇪🇸 ESPAÑOL

Desconexión involuntaria:
- Pierde quien iba perdiendo
- Si iba ganando, se repite
- Empate → reinicio
- Con rojas → gana quien tenga más jugadores

Desconexión voluntaria:
- Victoria para el rival

Fair Play:
- Prohibido insultar
- Prohibido bugs
- Prohibido perder tiempo
- Prohibido abandonar

---

🇬🇧 ENGLISH

Disconnections:

Unintentional:
- Losing player loses
- If winning → replay
- Draw → restart
- Red cards → player with more players wins

Voluntary:
- Opponent wins

Fair Play:
- No insults
- No exploits
- No time wasting
- No rage quit
"""

WELCOME_PRIVATE = """👋 Bienvenido / Welcome

✅ Ya estás listo para jugar

👉 Ahora debes:
1. Ir al grupo
2. Escribir: PLAY
3. Elegir cantidad
4. Esperar rival
5. Hablar por privado

---

👉 Now:
1. Go to group
2. Type PLAY
3. Choose amount
4. Wait opponent
5. Contact privately
"""

# ================= NUEVO USUARIO =================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        name = get_name(user)

        await update.message.reply_text(
f"""👋 Bienvenido {name}

⚠️ IMPORTANTE

👉 https://t.me/{BOT_USERNAME}
👉 Pulsa START

❗ Sin esto no puedes jugar
"""
        )

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users_started.add(user.id)

    keyboard = [[InlineKeyboardButton("✅ Aceptar reglas", callback_data="accept")]]

    await update.message.reply_text(RULES_1, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= ACCEPT =================

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text(RULES_2)
    await q.message.reply_text(RULES_3)
    await q.message.reply_text(WELCOME_PRIVATE)

# ================= PLAY =================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in users_started:
        await update.message.reply_text(f"⚠️ Activa el bot: https://t.me/{BOT_USERNAME}")
        return

    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"), InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"), InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]

    await update.message.reply_text("Selecciona partido", reply_markup=InlineKeyboardMarkup(kb))

# ================= MATCH =================

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global match_id_counter

    q = update.callback_query
    await q.answer()

    user = q.from_user
    amount = int(q.data.replace("p", ""))

    if user.id in user_match:
        await q.answer("Ya estás en partida", show_alert=True)
        return

    if user in queue[amount]:
        await q.answer("Ya en cola", show_alert=True)
        return

    queue[amount].append(user)

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        if p1.id == p2.id:
            queue[amount].append(p1)
            return

        match_id = match_id_counter
        match_id_counter += 1

        matches[match_id] = {"p1": p1, "p2": p2, "amount": amount, "reports": {}, "state": "playing"}

        user_match[p1.id] = match_id
        user_match[p2.id] = match_id

        name1 = get_name(p1)
        name2 = get_name(p2)

        kb = [[
            InlineKeyboardButton(f"Gana {name1}", callback_data=f"win_{match_id}_{p1.id}"),
            InlineKeyboardButton(f"Gana {name2}", callback_data=f"win_{match_id}_{p2.id}")
        ],
        [InlineKeyboardButton("⚠️ Disputa", callback_data=f"draw_{match_id}")]
        ]

        await context.bot.send_message(
            GROUP_ID,
            f"🔥 MATCH {amount}€\n{name1} vs {name2}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= RESULTADO =================

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    _, match_id, winner_id = q.data.split("_")

    match_id = int(match_id)
    winner_id = int(winner_id)

    match = matches.get(match_id)
    if not match:
        return

    if user.id in match["reports"]:
        await q.answer("Ya reportado", show_alert=True)
        return

    match["reports"][user.id] = winner_id

    if len(match["reports"]) == 2:
        votes = list(match["reports"].values())

        if votes[0] == votes[1]:
            winner = votes[0]
            winner_user = match["p1"] if match["p1"].id == winner else match["p2"]

            await context.bot.send_message(
                GROUP_ID,
                f"🏆 {get_name(winner_user)} gana {match['amount']}€"
            )
        else:
            await context.bot.send_message(GROUP_ID, "⚠️ DISPUTA")
            await context.bot.send_message(ADMIN_ID, f"Disputa match {match_id}")

        del user_match[match["p1"].id]
        del user_match[match["p2"].id]
        del matches[match_id]

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))
    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(win, pattern="^win_"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))

    print("BOT FINAL FUNCIONANDO")
    app.run_polling()

if __name__ == "__main__":
    main()
