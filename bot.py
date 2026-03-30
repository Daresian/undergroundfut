import os
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 13493800
GROUP_ID = -1001234567890
BOT_USERNAME = "@futelite_bot"
PAYPAL_LINK = "https://paypal.me/bucefalo74"

COMMISSION = 0.30
CONFIRM_TIME = 900

queues = {5: [], 10: [], 20: [], 50: [], 100: []}
balances = {}
users_state = {}
matches = {}
pending_results = {}

def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

def btn(text, data):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)]])

def result_buttons(match_id, p1, p2):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🏆 {p1}", callback_data=f"win_{match_id}_1")],
        [InlineKeyboardButton(f"🏆 {p2}", callback_data=f"win_{match_id}_2")]
    ])

def init_user(uid):
    if uid not in balances:
        balances[uid] = 0
        users_state[uid] = {"accepted": False, "playing": False}

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await context.bot.send_message(
            user.id,
            f"👋 Bienvenido a UNDERGROUND FUT\n\n1. Busca {BOT_USERNAME}\n2. Pulsa START\n3. Vuelve al grupo",
            reply_markup=btn("CONTINUAR ▶️", "r1")
        )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data == "r1":
        await query.message.edit_text("📜 Reglas 1", reply_markup=btn("SIGUIENTE ▶️", "r2"))

    elif query.data == "r2":
        await query.message.edit_text("📜 Reglas 2", reply_markup=btn("SIGUIENTE ▶️", "r3"))

    elif query.data == "r3":
        await query.message.edit_text("📜 Reglas 3", reply_markup=btn("ACEPTAR", "ok"))

    elif query.data == "ok":
        users_state[uid]["accepted"] = True
        await query.message.edit_text(f"✅ Reglas aceptadas\n💰 {PAYPAL_LINK}\nEscribe PAY o PLAY")

    elif query.data.startswith("win_"):
        _, match_id, player = query.data.split("_")

        if match_id in pending_results:
            return

        match = matches.get(match_id)
        if not match or match["status"] != "playing":
            return

        winner = match["p1"] if player == "1" else match["p2"]

        pending_results[match_id] = {"winner": winner, "time": time.time()}
        match["status"] = "pending"

        await query.edit_message_text("⏳ Esperando confirmación...")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id
    name = get_name(user)

    init_user(uid)

    if text == "PAY":
        await context.bot.send_message(ADMIN_ID, f"💰 Pago de {name}")

    if text.startswith("PLAY"):
        parts = text.split()

        if len(parts) < 2 or not parts[1].isdigit():
            await update.message.reply_text("❌ Usa: PLAY 5 / 10 / 20 / 50 / 100")
            return

        amount = int(parts[1])

        if not users_state[uid]["accepted"]:
            await update.message.reply_text("❌ Acepta reglas primero")
            return

        if users_state[uid]["playing"]:
            await update.message.reply_text("❌ Ya estás jugando")
            return

        if amount not in queues:
            await update.message.reply_text("❌ Cantidad inválida")
            return

        if balances[uid] < amount:
            await update.message.reply_text("❌ Sin saldo")
            return

        queues[amount].append((uid, name))
        await update.message.reply_text(f"⏳ Buscando rival {amount}€")

        if len(queues[amount]) >= 2:
            (p1, n1) = queues[amount].pop(0)
            (p2, n2) = queues[amount].pop(0)

            balances[p1] -= amount
            balances[p2] -= amount

            match_id = str(time.time())

            matches[match_id] = {
                "p1": p1,
                "p2": p2,
                "names": (n1, n2),
                "amount": amount,
                "status": "playing"
            }

            users_state[p1]["playing"] = True
            users_state[p2]["playing"] = True

            await context.bot.send_message(
                GROUP_ID,
                f"⚔️ {n1} vs {n2}\n💰 {amount}€",
                reply_markup=result_buttons(match_id, n1, n2)
            )

async def auto_loop(context):
    while True:
        now = time.time()

        for match_id in list(pending_results.keys()):
            if now - pending_results[match_id]["time"] > CONFIRM_TIME:

                match = matches[match_id]
                winner = pending_results[match_id]["winner"]

                prize = int(match["amount"] * 2 * (1 - COMMISSION))
                balances[winner] += prize

                n1, n2 = match["names"]
                winner_name = n1 if winner == match["p1"] else n2

                await context.bot.send_message(
                    GROUP_ID,
                    f"🏆 {winner_name} gana {prize}€"
                )

                users_state[match["p1"]]["playing"] = False
                users_state[match["p2"]]["playing"] = False

                del matches[match_id]
                del pending_results[match_id]

        await asyncio.sleep(30)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.create_task(auto_loop(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
