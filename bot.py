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

# ================= NUEVO USUARIO =================

async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:

        name = get_name(user)

        await update.message.reply_text(
f"""👋 Bienvenido {name}

⚠️ IMPORTANTE / IMPORTANT

Para poder jugar debes activar el bot:

👉 https://t.me/{BOT_USERNAME}
👉 Pulsa START

❗ Si no haces esto no podrás jugar

---

To play you MUST start the bot first.
"""
        )

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users_started.add(user.id)

    keyboard = [[InlineKeyboardButton("✅ Aceptar reglas / Accept rules", callback_data="accept")]]

    await update.message.reply_text(
        RULES,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= ACCEPT =================

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text(WELCOME_PRIVATE)

# ================= PLAY =================

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

        name1 = get_name(p1)
        name2 = get_name(p2)

        kb = [[
            InlineKeyboardButton(f"Gana {name1}", callback_data=f"win_{match_id}_{p1.id}"),
            InlineKeyboardButton(f"Gana {name2}", callback_data=f"win_{match_id}_{p2.id}")
        ]]

        await context.bot.send_message(
            GROUP_ID,
            f"""🔥 MATCH {amount}€

{name1} vs {name2}

📩 Hablad por privado / Contact privately
""",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= RESULTADO =================

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Resultado enviado")

    user = q.from_user
    _, match_id, winner_id = q.data.split("_")

    match_id = int(match_id)
    winner_id = int(winner_id)

    match = matches.get(match_id)

    if not match:
        return

    if user.id not in [match["p1"].id, match["p2"].id]:
        return

    match["reports"][user.id] = winner_id

    if len(match["reports"]) == 2:
        votes = list(match["reports"].values())

        if votes[0] == votes[1]:
            winner = votes[0]

            winner_user = match["p1"] if match["p1"].id == winner else match["p2"]
            name = get_name(winner_user)

            await context.bot.send_message(
                GROUP_ID,
                f"""🏆 {name} gana {match['amount']}€

💰 Pago en proceso"""
            )
        else:
            await context.bot.send_message(GROUP_ID, "⚠️ DISPUTA DETECTADA")

            await context.bot.send_message(
                ADMIN_ID,
                f"""🚨 DISPUTA

Match {match_id}
"""
            )

        del user_match[match["p1"].id]
        del user_match[match["p2"].id]
        del matches[match_id]

# ================= TEXTOS =================

WELCOME_PRIVATE = """👋 Bienvenido

Ya puedes usar PLAY en el grupo
"""

RULES = """📜 REGLAS (exactas aquí)
"""

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))
    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(win, pattern="^win_"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))

    print("BOT LIMPIO ACTIVO")
    app.run_polling()

if __name__ == "__main__":
    main()
