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
PAYPAL_LINK = "https://paypal.me/bucefalo74"

logging.basicConfig(level=logging.INFO)

queue = {5: [], 10: [], 20: [], 50: [], 100: []}
matches = {}
user_match = {}
users_started = set()
authorized_users = {}  # user_id: amount autorizado
match_id_counter = 1

def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users_started.add(update.effective_user.id)

    kb = [[InlineKeyboardButton("✅ Aceptar reglas / Accept rules", callback_data="accept")]]
    await update.message.reply_text("📜 Reglas enviadas arriba", reply_markup=InlineKeyboardMarkup(kb))

# ================= PLAY =================

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in users_started:
        await update.message.reply_text("⚠️ Haz /start primero en privado")
        return

    kb = [
        [InlineKeyboardButton("5€", callback_data="p5"), InlineKeyboardButton("10€", callback_data="p10")],
        [InlineKeyboardButton("20€", callback_data="p20"), InlineKeyboardButton("50€", callback_data="p50")],
        [InlineKeyboardButton("100€", callback_data="p100")]
    ]

    await update.message.reply_text("Selecciona / Select", reply_markup=InlineKeyboardMarkup(kb))

# ================= SELECCIÓN =================

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global match_id_counter

    q = update.callback_query
    await q.answer()

    user = q.from_user
    amount = int(q.data.replace("p", ""))

    # ADMIN puede saltarse pago (modo test)
    if user.id != ADMIN_ID:

        # NO autorizado → enviar a pagar
        if authorized_users.get(user.id) != amount:
            try:
                await context.bot.send_message(
                    user.id,
                    f"💳 Debes ingresar {amount}€ aquí:\n{PAYPAL_LINK}\n\n"
                    f"🇬🇧 You must send {amount}€ here:\n{PAYPAL_LINK}"
                )
            except:
                await q.answer("Abre privado con el bot", show_alert=True)
                return

            await q.answer("Debes pagar primero", show_alert=True)
            return

    # YA AUTORIZADO → entra en cola
    if user.id in user_match:
        return

    if any(user in ql for ql in queue.values()):
        return

    queue[amount].append(user)

    await q.message.reply_text("⏳ En cola / In queue")

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

# ================= AUTORIZAR (ADMIN) =================

async def autorizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        amount = int(context.args[0])
        username = context.args[1].replace("@", "")
    except:
        await update.message.reply_text("Uso: /autorizar 10 @usuario")
        return

    # buscar usuario en chat
    for u in users_started:
        # no tenemos mapping username→id directo, así que simplificamos
        pass

    # solución práctica: responder a mensaje del usuario
    if update.message.reply_to_message:
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
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))
    app.add_handler(CallbackQueryHandler(select, pattern="^p"))
    app.add_handler(CallbackQueryHandler(win, pattern="^win_"))

    app.run_polling()

if __name__ == "__main__":
    main()
