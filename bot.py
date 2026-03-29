import os
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 13493800
GROUP_ID = -1001234567890
BOT_USERNAME = "@futelite_bot"
PAYPAL_LINK = "https://paypal.me/bucefalo74"

COMMISSION = 0.30
CONFIRM_TIME = 900

# ================= DATA =================
queues = {5: [], 10: [], 20: [], 50: [], 100: []}
balances = {}
rules_step = {}
matches = {}
pending_results = {}
last_opponent = {}

# ================= HELPERS =================
def get_name(user):
    return f"@{user.username}" if user.username else user.first_name

def btn_continue():
    return InlineKeyboardMarkup([[InlineKeyboardButton("CONTINUAR ▶️", callback_data="cont")]])

def btn_next():
    return InlineKeyboardMarkup([[InlineKeyboardButton("SIGUIENTE ▶️", callback_data="next")]])

def btn_accept():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ ACEPTO", callback_data="accept")]])

def result_buttons(match_id, p1_name, p2_name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🏆 Gana {p1_name}", callback_data=f"win_{match_id}_1")],
        [InlineKeyboardButton(f"🏆 Gana {p2_name}", callback_data=f"win_{match_id}_2")]
    ])

def init_user(uid):
    if uid not in balances:
        balances[uid] = 0
        rules_step[uid] = 0

# ================= COMANDOS PRO =================
async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    chat = update.message.chat
    uid = user.id

    # /id
    if text == "/id":
        await update.message.reply_text(f"🆔 Tu ID: {uid}")
        return

    # /grupo
    if text == "/grupo":
        await update.message.reply_text(f"📢 ID grupo: {chat.id}")
        return

    # /info
    if text == "/info":
        await update.message.reply_text(f"""
👤 Usuario: {get_name(user)}
🆔 ID Usuario: {uid}
💬 Chat ID: {chat.id}
📌 Tipo: {chat.type}
""")
        return

    # /saldo
    if text == "/saldo":
        init_user(uid)
        await update.message.reply_text(f"💰 Saldo: {balances[uid]}€")
        return

# ================= BOTONES =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    if query.data.startswith("win_"):
        _, match_id, player = query.data.split("_")

        if match_id not in matches:
            return

        if match_id in pending_results:
            await query.answer("Resultado ya enviado", show_alert=True)
            return

        p1, p2, amount, names = matches[match_id]
        winner = p1 if player == "1" else p2

        pending_results[match_id] = {
            "winner": winner,
            "time": time.time()
        }

        await query.edit_message_text("⏳ Resultado enviado. Esperando confirmación automática...")

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id
    name = get_name(user)

    init_user(uid)

    # ===== COMANDOS PRO =====
    await comandos(update, context)

    # ===== ADMIN =====
    if uid == ADMIN_ID:

        if text == "ADMIN":
            activos = "\n".join(matches.keys()) or "Ninguno"
            pendientes = "\n".join(pending_results.keys()) or "Ninguno"

            await update.message.reply_text(f"""
🛠 ADMIN

🎮 Activos:
{activos}

⏳ Pendientes resultado:
{pendientes}

💰 Saldos:
{balances}
""")

        if text.startswith("OK"):
            _, user_id, amount = text.split()
            balances[int(user_id)] += int(amount)

    # ===== PAY =====
    if text == "PAY":
        await context.bot.send_message(ADMIN_ID, f"💰 Pago de {name} ({uid})")

    # ===== PLAY =====
    if text.startswith("PLAY"):
        amount = int(text.split()[1])

        if balances[uid] < amount:
            await update.message.reply_text("❌ Saldo insuficiente")
            return

        queues[amount].append((uid, name))

        if len(queues[amount]) >= 2:
            (p1, n1) = queues[amount].pop(0)
            (p2, n2) = queues[amount].pop(0)

            balances[p1] -= amount
            balances[p2] -= amount

            match_id = str(time.time())
            matches[match_id] = (p1, p2, amount, (n1, n2))

            await context.bot.send_message(
                GROUP_ID,
                f"⚔️ MATCH\n\n{n1} vs {n2}\n\nSelecciona ganador:",
                reply_markup=result_buttons(match_id, n1, n2)
            )

# ================= AUTO =================
async def auto_confirm(app):
    while True:
        now = time.time()

        for match_id in list(pending_results.keys()):
            data = pending_results[match_id]

            if now - data["time"] > CONFIRM_TIME:
                winner = data["winner"]
                p1, p2, amount, names = matches[match_id]

                prize = int(amount * 2 * (1 - COMMISSION))
                balances[winner] += prize

                winner_name = names[0] if winner == p1 else names[1]

                await app.bot.send_message(
                    GROUP_ID,
                    f"🎉 {winner_name} gana {prize}€ 💰"
                )

                del matches[match_id]
                del pending_results[match_id]

        await asyncio.sleep(30)

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.job_queue.run_once(lambda ctx: asyncio.create_task(auto_confirm(app)), 1)

    app.run_polling()

if __name__ == "__main__":
    main()
