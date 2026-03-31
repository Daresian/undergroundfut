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
BOT_LINK = "https://t.me/Futelite_bot"
PAYPAL_LINK = "https://paypal.me/bucefalo74"

logging.basicConfig(level=logging.INFO)

queue = {5: [], 10: [], 20: [], 50: [], 100: []}
matches = {}
user_match = {}
users_started = set()
authorized_users = {}
match_id_counter = 1

def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= REGLAS =================

RULES_1 = """📜 REGLAMENTO UNDERGROUND FUT

🇪🇸
La comunidad es solo para mayores de 18 años.
Es obligatorio grabar los partidos.
Si no grabas → pierdes derecho a reclamar.
Underground Fut puede retransmitir los partidos.

Emparejamiento:
Necesitas usuario Telegram (@usuario) y activar el bot.

Pagos:
Prohibido multicuentas o fraude → expulsión + pérdida de saldo.
Debes pagar antes de jugar.
Validación en máximo 12h.

---

🇬🇧
Community for +18 only.
Matches must be recorded.
No recording → no claim rights.
Matches may be streamed.

Matchmaking:
Telegram username required and bot activated.

Payments:
No multi-accounts or fraud.
Pay before playing.
Validation within 12h.
"""

RULES_2 = """📜 REGLAS DE PARTIDO

🇪🇸
Modo amistoso online
6 min por parte
Sin empate (prórroga + penaltis)
Solo Ultimate Team
Sin sliders ni hacks
1 vs 1 obligatorio
Prohibido perder tiempo

Tiempo:
15 min contacto
1h jugar

---

🇬🇧
Online friendly mode
6 min halves
No draws (extra time + penalties)
Ultimate Team only
No sliders/hacks
Strict 1v1
No time wasting

Time:
15 min contact
1h play
"""

RULES_3 = """📜 DESCONEXIONES Y FAIR PLAY

🇪🇸
Desconexión:
Pierde quien iba perdiendo
Si ganaba → repetir
Empate → repetir

Voluntaria → pierde

Fair Play:
Prohibido insultar
Prohibido bugs
Prohibido abandonar

---

🇬🇧
Disconnection:
Losing player loses
Winning → replay
Draw → replay

Voluntary quit → loss

Fair Play:
No insults
No exploits
No quitting
"""

# ================= NUEVO USUARIO =================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:

        kb = [[InlineKeyboardButton("👉 Activar Bot / Start Bot", url=BOT_LINK)]]

        await update.message.reply_text(
            f"👋 Bienvenido {get_name(user)}\n\n"
            f"🇪🇸 Pulsa el botón y escribe /start\n"
            f"🇬🇧 Click and press /start",
            reply_markup=InlineKeyboardMarkup(kb)
        )

        # intento de mensaje privado (solo funciona si ya abrió el bot antes)
        try:
            await context.bot.send_message(
                user.id,
                f"👋 Bienvenido\n\n"
                f"👉 Activa el bot aquí:\n{BOT_LINK}\n"
                f"Escribe /start"
            )
        except:
            pass

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_started.add(update.effective_user.id)

    kb = [[InlineKeyboardButton("✅ Aceptar reglas / Accept", callback_data="accept")]]

    await update.message.reply_text(RULES_1, reply_markup=InlineKeyboardMarkup(kb))

# ================= ACEPTAR =================

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text(RULES_2)
    await q.message.reply_text(RULES_3)

    await q.message.reply_text(
        "✅ Ya puedes jugar\n\n"
        "1. Ve al grupo\n"
        "2. Escribe PLAY\n\n"
        "🇬🇧 You can now play"
    )

# ================= PLAY =================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in users_started:
        await update.message.reply_text("⚠️ Haz /start en privado primero")
        return

    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"), InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"), InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]

    await update.message.reply_text("Selecciona / Select", reply_markup=InlineKeyboardMarkup(kb))

# ================= SELECT =================

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global match_id_counter

    q = update.callback_query
    await q.answer()

    user = q.from_user
    amount = int(q.data.replace("p", ""))

    # ADMIN bypass (modo test)
    if user.id != ADMIN_ID:

        if authorized_users.get(user.id) != amount:
            try:
                await context.bot.send_message(
                    user.id,
                    f"💳 Debes ingresar {amount}€ aquí:\n{PAYPAL_LINK}\n\n"
                    f"🇬🇧 Send {amount}€ here:\n{PAYPAL_LINK}"
                )
            except:
                await q.answer("Abre el bot primero", show_alert=True)
                return

            await q.answer("Debes pagar primero", show_alert=True)
            return

    if user.id in user_match:
        return

    if any(user in ql for ql in queue.values()):
        return

    queue[amount].append(user)

    await q.message.reply_text("⏳ En cola")

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        match_id = match_id_counter
        match_id_counter += 1

        matches[match_id] = {"p1": p1, "p2": p2, "amount": amount, "reports": {}}
        user_match[p1.id] = match_id
        user_match[p2.id] = match_id

        kb = [[
            InlineKeyboardButton(f"🏆 {get_name(p1)}", callback_data=f"win_{match_id}_{p1.id}"),
            InlineKeyboardButton(f"🏆 {get_name(p2)}", callback_data=f"win_{match_id}_{p2.id}")
        ],
        [InlineKeyboardButton("⚠️ Disputa", callback_data=f"draw_{match_id}")]
        ]

        await context.bot.send_message(
            GROUP_ID,
            f"🔥 MATCH {amount}€\n{get_name(p1)} vs {get_name(p2)}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= AUTORIZAR =================

async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Responde al usuario con /autorizar 10")
        return

    try:
        amount = int(context.args[0])
    except:
        await update.message.reply_text("Uso: /autorizar 10")
        return

    user = update.message.reply_to_message.from_user
    authorized_users[user.id] = amount

    await context.bot.send_message(
        user.id,
        f"✅ Autorizado Play {amount}\n\n🇬🇧 Authorized Play {amount}"
    )

    await update.message.reply_text("OK autorizado")

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

    match["reports"][user.id] = winner_id

    if len(match["reports"]) == 2:
        votes = list(match["reports"].values())

        if votes[0] == votes[1]:
            winner_user = match["p1"] if match["p1"].id == votes[0] else match["p2"]

            await context.bot.send_message(
                GROUP_ID,
                f"🏆 Ganador: {get_name(winner_user)}"
            )
        else:
            await context.bot.send_message(GROUP_ID, "⚠️ DISPUTA")

        del user_match[match["p1"].id]
        del user_match[match["p2"].id]
        del matches[match_id]

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("autorizar", autorizar))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))
    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))
    app.add_handler(CallbackQueryHandler(win, pattern="^win_"))

    app.run_polling()

if __name__ == "__main__":
    main()
