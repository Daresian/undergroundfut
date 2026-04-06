import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

TOKEN = "TU_TOKEN"
ADMIN_ID = 123456789
PAYPAL_LINK = "https://paypal.me/bucefalo74"

logging.basicConfig(level=logging.INFO)

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    activated INTEGER DEFAULT 0,
    rules INTEGER DEFAULT 0,
    paid INTEGER DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS queue (
    user_id INTEGER,
    amount INTEGER
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    p1 INTEGER,
    p2 INTEGER,
    amount INTEGER,
    r1 TEXT,
    r2 TEXT,
    status TEXT
)""")

conn.commit()

# ================= REGLAS =================
RULES = """
REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT

🇪🇸 ESPAÑOL

Reglamento General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch.

Reglas de Emparejamiento en Telegram
Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente @Futelite_bot . Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.

Reglas de Pago
Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero. El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas.

Reglas de Partido
Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team.

Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado. Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón; los administradores revisarán las grabaciones y sancionarán con la pérdida del partido a quien infrinja esta norma.

Tiempo para Jugar
Tras realizar el emparejamiento, los usuarios dispondrán de un máximo de 15 minutos para ponerse en contacto y acordar el inicio del partido. Una vez hecho el “match”, tendrán un máximo de 1 hora para jugar y comunicar el resultado.

Desconexiones
Es imprescindible que ambos jugadores graben los partidos para conservar el derecho a reclamar en caso de disputa.

Desconexión Aparentemente Involuntaria
1. Si se desconecta el jugador que va perdiendo, la victoria se otorgará al jugador que va ganando.
2. Si se desconecta el jugador que va ganando, el partido se repetirá.
3. En caso de empate con ambos equipos jugando 11 contra 11, el partido se reiniciará con la misma alineación y se jugará el tiempo restante.
4. En caso de empate y que uno de los equipos tenga una o más tarjetas rojas, la victoria será adjudicada al jugador que conserve los 11 jugadores o que tenga menos tarjetas rojas.

Desconexión Voluntaria (Abandono de partida)
1. En caso de desconexión voluntaria, la victoria será concedida al jugador que mantiene la conexión, independientemente del resultado en el momento de la desconexión.

Fair Play
• Está prohibido insultar. Comportamiento tóxico. Expulsión Inmediata de la comunidad.
• No se permite el uso de bugs.
• La pérdida de tiempo intencional está sancionada.
• No está permitido desconectarse del partido de forma injustificada.

🇬🇧 ENGLISH

General Rules
The Underground Fut Community is strictly for users over 18 years old. Both participants must record all matches, as recordings are the only valid evidence in case of disputes. If a player does not record the match, they lose the right to claim any money in case of disagreement. Additionally, Underground Fut reserves the right to stream matches on its Twitch channel.

Telegram Matchmaking Rules
To participate in matchmaking, each player must have a Telegram username (in the format @username) and activate the bot @Futelite_bot. This is mandatory to access matches and be paired correctly.

Payment Rules
Having multiple accounts and arranging matches between them is strictly prohibited. The system monitors gameplay patterns to detect fraud. Any attempt to cheat will result in immediate expulsion from the community and loss of all deposited funds. Payment must be made before requesting matchmaking, allowing each player to add funds to their wallet. The money played will remain locked until result validation, and the prize will be authorized and paid within a maximum of 12 hours.

Match Rules
Matches must be played in Online Friendly mode using default settings. Settings cannot be modified, and each half must last 6 minutes. All matches must end with a winner; draws are not allowed, so extra time and penalties must be played if necessary. Only Ultimate Team squads are allowed.

The use of sliders and handicaps is strictly forbidden. Violations will result in expulsion and loss of funds. Matches are strictly 1 vs 1, and participation of multiple players on the same team is not allowed. Intentional time-wasting through ball possession is prohibited; administrators will review recordings and penalize offenders with a match loss.

Time to Play
After matchmaking, players have a maximum of 15 minutes to contact each other and agree on the match start. Once matched, they have a maximum of 1 hour to play and report the result.

Disconnections
Both players must record matches to maintain the right to claim in case of disputes.

Unintentional Disconnection
1. If the losing player disconnects, the win is awarded to the winning player.
2. If the winning player disconnects, the match must be replayed.
3. In case of a draw with both teams having 11 players, the match restarts with the same lineup and remaining time.
4. In case of a draw where one team has red cards, the win is awarded to the team with more players or fewer red cards.

Voluntary Disconnection (Quit)
1. If a player quits intentionally, the win is awarded to the player who remains connected, regardless of the current score.

Fair Play
• Insults and toxic behavior are strictly prohibited and will result in immediate expulsion.
• Exploiting bugs is not allowed.
• Intentional time-wasting is punishable.
• Unjustified disconnections are not allowed.
"""

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)",
                   (user.id, user.username, 0, 0, 0))
    conn.commit()

    keyboard = [[InlineKeyboardButton("ACTIVAR / ACTIVATE", callback_data="activate")]]

    await update.message.reply_text(
        f"👋 Bienvenido {user.first_name}\n\n"
        "⚠️ Debes activar el bot para jugar\n"
        "⚠️ You must activate the bot to play",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= ACTIVAR =================
async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    cursor.execute("UPDATE users SET activated=1 WHERE user_id=?", (q.from_user.id,))
    conn.commit()

    keyboard = [[InlineKeyboardButton("ACEPTAR REGLAS", callback_data="rules")]]

    await q.message.reply_text(RULES, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= REGLAS =================
async def accept_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    cursor.execute("UPDATE users SET rules=1 WHERE user_id=?", (q.from_user.id,))
    conn.commit()

    await q.message.reply_text("✅ Reglas aceptadas\nEscribe PLAY")

# ================= PLAY =================
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    cursor.execute("SELECT activated, rules FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()

    if not data or data[0] == 0 or data[1] == 0:
        return

    keyboard = [
        [InlineKeyboardButton("4€", callback_data="4")],
        [InlineKeyboardButton("10€", callback_data="10")],
        [InlineKeyboardButton("20€", callback_data="20")],
        [InlineKeyboardButton("50€", callback_data="50")],
        [InlineKeyboardButton("100€", callback_data="100")]
    ]

    await update.message.reply_text("💰 Elige cantidad", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= PAGO =================
async def select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    amount = int(q.data)
    context.user_data["amount"] = amount

    await q.message.reply_text(
        f"💳 Debes pagar {amount}€ antes de jugar\n{PAYPAL_LINK}\n\nEscribe PAGADO"
    )

# ================= PAGADO =================
async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != "pagado":
        return

    user = update.effective_user
    amount = context.user_data.get("amount")

    await context.bot.send_message(
        ADMIN_ID,
        f"/confirm_{user.id}_{amount}"
    )

    await update.message.reply_text("⏳ Esperando confirmación admin")

# ================= CONFIRMAR =================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    parts = update.message.text.split("_")
    user_id = int(parts[1])
    amount = int(parts[2])

    cursor.execute("UPDATE users SET paid=1 WHERE user_id=?", (user_id,))
    conn.commit()

    # MATCH
    cursor.execute("SELECT user_id FROM queue WHERE amount=?", (amount,))
    rival = cursor.fetchone()

    if rival:
        rival_id = rival[0]

        cursor.execute("DELETE FROM queue WHERE user_id=?", (rival_id,))
        conn.commit()

        cursor.execute("INSERT INTO matches (p1,p2,amount,status) VALUES (?,?,?,?)",
                       (user_id, rival_id, amount, "playing"))
        conn.commit()

        await context.bot.send_message(user_id, f"🎮 Rival encontrado: {rival_id}")
        await context.bot.send_message(rival_id, f"🎮 Rival encontrado: {user_id}")

    else:
        cursor.execute("INSERT INTO queue VALUES (?,?)", (user_id, amount))
        conn.commit()

        await context.bot.send_message(user_id, "⏳ Esperando rival")

# ================= RESULTADOS =================
async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if "-" not in text:
        return

    cursor.execute("SELECT * FROM matches WHERE (p1=? OR p2=?) AND status='playing'",
                   (user.id, user.id))
    match = cursor.fetchone()

    if not match:
        return

    match_id = match[0]

    if match[1] == user.id:
        cursor.execute("UPDATE matches SET r1=? WHERE id=?", (text, match_id))
    else:
        cursor.execute("UPDATE matches SET r2=? WHERE id=?", (text, match_id))

    conn.commit()

    cursor.execute("SELECT r1,r2,amount,p1,p2 FROM matches WHERE id=?", (match_id,))
    r1,r2,amount,p1,p2 = cursor.fetchone()

    if r1 and r2:
        if r1 == r2:
            g1,g2 = map(int, r1.split("-"))
            winner = p1 if g1 > g2 else p2

            prize = amount * 2 * 0.7

            await context.bot.send_message(winner,
                f"🏆 GANADOR\n🎉 Has ganado {prize}€")

            cursor.execute("UPDATE matches SET status='finished' WHERE id=?", (match_id,))
            conn.commit()

        else:
            await context.bot.send_message(ADMIN_ID, f"⚠️ DISPUTA match {match_id}")

# ================= ANTI TRAMPA =================
def anti_cheat(user):
    cursor.execute("SELECT COUNT(*) FROM users WHERE username=?", (user.username,))
    return cursor.fetchone()[0] > 1

# ================= RESET =================
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM matches")
        cursor.execute("DELETE FROM queue")
        conn.commit()
        await update.message.reply_text("BD reseteada")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        app.bot.delete_webhook(drop_pending_updates=True)
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(CallbackQueryHandler(activate, pattern="activate"))
    app.add_handler(CallbackQueryHandler(accept_rules, pattern="rules"))
    app.add_handler(CallbackQueryHandler(select_amount, pattern="^[0-9]+$"))

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^play$"), play))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^pagado$"), paid))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/confirm_"), confirm))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, result))

    print("BOT FUNCIONANDO")

    app.run_polling()

if __name__ == "__main__":
    main()
