import logging
import os
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# CONFIG
ADMIN_ID = 123456789  # <-- CAMBIA ESTO
PAYPAL_LINK = "https://paypal.me/bucefalo74"
COMMISSION = 0.30
CONFIRM_TIME = 900  # 15 minutos

# DATA
queues = {5: [], 10: [], 20: [], 50: [], 100: []}
balances = {}
approved = {}
matches = {}
pending_results = {}
user_devices = {}

# HELPERS
def get_username(user):
    return user.username if user.username else user.first_name

def ensure_user(user_id):
    if user_id not in balances:
        balances[user_id] = 0
        approved[user_id] = False

# BIENVENIDA
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"""
👋 Bienvenido

📜 Reglas:
- Debes pagar antes de jugar
- Tienes 15 min para confirmar resultado
- Trampas = baneo

💰 Recarga saldo:
{PAYPAL_LINK}

Cuando pagues escribe:
PAY

Luego espera aprobación
"""
        )

# MENSAJES
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    user = update.message.from_user
    user_id = user.id
    username = get_username(user)

    ensure_user(user_id)

    # ANTI MULTICUENTA (básico)
    device = str(user_id)[:5]
    if device in user_devices and user_devices[device] != user_id:
        await update.message.reply_text("🚫 Posible multicuenta detectada")
        return
    user_devices[device] = user_id

    # VER SALDO
    if text == "SALDO":
        await context.bot.send_message(
            chat_id=user_id,
            text=f"💰 Tu saldo: {balances[user_id]}€"
        )

    # SOLICITAR PAGO
    elif text == "PAY":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"💰 {username} quiere recargar saldo"
        )
        await update.message.reply_text("⏳ Esperando aprobación admin")

    # ADMIN APRUEBA
    elif text.startswith("OK") and user_id == ADMIN_ID:
        try:
            parts = text.split()
            target_username = parts[1]
            amount = int(parts[2])

            for uid in balances:
                # búsqueda simple
                if True:
                    balances[uid] += amount
                    approved[uid] = True
                    await context.bot.send_message(
                        chat_id=uid,
                        text=f"✅ Pago aprobado\n💰 Saldo: {balances[uid]}€"
                    )
                    break

        except:
            await update.message.reply_text("Formato: OK usuario cantidad")

    # PLAY
    elif text.startswith("PLAY"):
        try:
            amount = int(text.split()[1])

            if amount not in queues:
                return

            if balances[user_id] < amount:
                await update.message.reply_text("❌ Saldo insuficiente")
                return

            queues[amount].append(user_id)
            await update.message.reply_text(f"✅ Entraste en cola {amount}€")

            if len(queues[amount]) >= 2:
                p1 = queues[amount].pop(0)
                p2 = queues[amount].pop(0)

                # descontar saldo
                balances[p1] -= amount
                balances[p2] -= amount

                match_id = f"{p1}_{p2}_{time.time()}"
                matches[match_id] = (p1, p2, amount)

                await context.bot.send_message(p1, f"""
⚔️ MATCH ENCONTRADO

Rival: {p2}
Apuesta: {amount}€
Premio: {int(amount*2*(1-COMMISSION))}€

Contacta por privado y juega.
""")

                await context.bot.send_message(p2, f"""
⚔️ MATCH ENCONTRADO

Rival: {p1}
Apuesta: {amount}€
Premio: {int(amount*2*(1-COMMISSION))}€

Contacta por privado y juega.
""")

        except:
            pass

    # REPORTAR RESULTADO
    elif text.startswith("WIN"):
        try:
            match_id = list(matches.keys())[0]
            p1, p2, amount = matches[match_id]

            if user_id not in [p1, p2]:
                return

            pending_results[match_id] = {
                "winner": user_id,
                "time": time.time(),
                "confirmed": False
            }

            loser = p2 if user_id == p1 else p1

            await context.bot.send_message(
                chat_id=loser,
                text="⚠️ Rival dice que ha ganado\nResponde WIN o NO"
            )

        except:
            pass

    # CONFIRMAR
    elif text == "WIN":
        for match_id in pending_results:
            data = pending_results[match_id]
            p1, p2, amount = matches[match_id]

            if user_id in [p1, p2]:
                winner = data["winner"]

                prize = int(amount * 2 * (1 - COMMISSION))
                balances[winner] += prize

                await context.bot.send_message(
                    chat_id=winner,
                    text=f"🏆 Ganaste {prize}€\n💰 Saldo: {balances[winner]}"
                )

                del matches[match_id]
                del pending_results[match_id]
                break

    # DISPUTA
    elif text == "NO":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="🚨 DISPUTA DETECTADA"
        )

# TIMEOUT
async def check_timeouts(app):
    while True:
        now = time.time()
        for match_id in list(pending_results.keys()):
            data = pending_results[match_id]

            if now - data["time"] > CONFIRM_TIME:
                winner = data["winner"]
                p1, p2, amount = matches[match_id]

                prize = int(amount * 2 * (1 - COMMISSION))
                balances[winner] += prize

                del matches[match_id]
                del pending_results[match_id]

        await asyncio.sleep(30)

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
