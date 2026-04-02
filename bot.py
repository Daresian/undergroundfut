import logging
import os
import sqlite3
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import *

TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = -1003882941029
ADMIN_ID = 13493800

MATCH_TIMEOUT = 900  # 15 min

logging.basicConfig(level=logging.INFO)

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    accepted_rules INTEGER DEFAULT 0,
    payment_pending INTEGER DEFAULT 0,
    payment_amount INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    p1 INTEGER,
    p2 INTEGER,
    amount INTEGER,
    r1 TEXT,
    r2 TEXT,
    status TEXT,
    created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    p1 INTEGER,
    p2 INTEGER,
    count INTEGER DEFAULT 1
)
""")

conn.commit()

# ================= MEMORIA =================
queue = {5: [], 10: [], 20: [], 50: [], 100: []}
user_cache = {}
user_match = {}
match_counter = 1

# ================= RULES =================
RULES = """📜 REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT

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

# ================= CACHE =================
async def cache_user(update):
    user = update.effective_user
    if user:
        user_cache[user.id] = user

def get_name(uid):
    u = user_cache.get(uid)
    return f"@{u.username}" if u and u.username else str(uid)

# ================= ANTI TRAMPA =================
def check_fraud(p1, p2):
    cursor.execute("""
        SELECT count FROM history 
        WHERE (p1=? AND p2=?) OR (p1=? AND p2=?)
    """, (p1, p2, p2, p1))

    row = cursor.fetchone()

    if row:
        if row[0] >= 3:
            return True
        else:
            cursor.execute("""
                UPDATE history SET count = count + 1
                WHERE (p1=? AND p2=?) OR (p1=? AND p2=?)
            """, (p1, p2, p2, p1))
    else:
        cursor.execute("INSERT INTO history(p1,p2,count) VALUES (?,?,1)", (p1, p2))

    conn.commit()
    return False

# ================= WELCOME =================
async def welcome(update, context):
    for user in update.message.new_chat_members:
        user_cache[user.id] = user

        cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user.id,))
        conn.commit()

        await context.bot.send_message(
            GROUP_ID,
            f"👋 Bienvenido {user.mention_html()}\n👉 Abre el bot:\nhttps://t.me/{context.bot.username}",
            parse_mode="HTML"
        )

        try:
            kb = [[InlineKeyboardButton("✅ Acepto / I Accept", callback_data="accept")]]
            await context.bot.send_message(user.id, RULES, reply_markup=InlineKeyboardMarkup(kb))
        except:
            pass

# ================= START =================
async def start(update, context):
    await cache_user(update)

    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (update.effective_user.id,))
    conn.commit()

    kb = [[InlineKeyboardButton("✅ Acepto / I Accept", callback_data="accept")]]
    await update.message.reply_text(RULES, reply_markup=InlineKeyboardMarkup(kb))

# ================= ACCEPT =================
async def accept(update, context):
    q = update.callback_query
    await q.answer()

    cursor.execute("UPDATE users SET accepted_rules=1 WHERE user_id=?", (q.from_user.id,))
    conn.commit()

    await q.message.edit_text("✅ Reglas aceptadas / Rules accepted")

# ================= PLAY =================
async def play(update, context):
    await cache_user(update)
    user = update.effective_user

    try:
        amount = int(update.message.text.split(" ")[1])
    except:
        return await update.message.reply_text("Uso: play 10")

    if amount not in queue:
        return await update.message.reply_text("❌ Cantidad no válida")

    cursor.execute("SELECT accepted_rules FROM users WHERE user_id=?", (user.id,))
    if cursor.fetchone()[0] != 1:
        return await update.message.reply_text("Acepta reglas primero")

    cursor.execute("UPDATE users SET payment_pending=1, payment_amount=? WHERE user_id=?", (amount, user.id))
    conn.commit()

    kb = [[InlineKeyboardButton("📩 He pagado", callback_data=f"paid_{user.id}_{amount}")]]
    await context.bot.send_message(user.id, f"💳 Envía {amount}€ y espera validación", reply_markup=InlineKeyboardMarkup(kb))

    kb_admin = [[InlineKeyboardButton("✅ Pago OK", callback_data=f"payok_{user.id}_{amount}")]]
    await context.bot.send_message(ADMIN_ID, f"💰 {get_name(user.id)} paga {amount}€", reply_markup=InlineKeyboardMarkup(kb_admin))

# ================= MATCH =================
async def try_match(amount, context):
    global match_counter

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        if check_fraud(p1, p2):
            await context.bot.send_message(ADMIN_ID, f"🚨 FRAUDE {get_name(p1)} vs {get_name(p2)}")
            return

        match_id = match_counter
        match_counter += 1

        now = datetime.utcnow().isoformat()

        cursor.execute("INSERT INTO matches VALUES (?,?,?,?,?,?,?,?)",
                       (match_id, p1, p2, amount, None, None, "playing", now))
        conn.commit()

        user_match[p1] = match_id
        user_match[p2] = match_id

        kb = [[
            InlineKeyboardButton("🏆 Gané", callback_data=f"win_{match_id}"),
            InlineKeyboardButton("❌ Perdí", callback_data=f"lose_{match_id}")
        ],[
            InlineKeyboardButton("⚠️ Disputa", callback_data=f"dispute_{match_id}")
        ]]

        msg = f"⚔️ MATCH {amount}€\n{get_name(p1)} vs {get_name(p2)}"

        await context.bot.send_message(GROUP_ID, msg)

        for p in [p1, p2]:
            await context.bot.send_message(p, msg, reply_markup=InlineKeyboardMarkup(kb))

# ================= RESULTADO =================
async def process_result(match_id, context):
    cursor.execute("SELECT p1,p2,amount,r1,r2 FROM matches WHERE match_id=?", (match_id,))
    row = cursor.fetchone()
    if not row:
        return

    p1,p2,amount,r1,r2 = row

    if r1 and r2:
        if r1 == "win" and r2 == "lose":
            winner = p1
        elif r2 == "win" and r1 == "lose":
            winner = p2
        else:
            cursor.execute("UPDATE matches SET status='dispute' WHERE match_id=?", (match_id,))
            conn.commit()
            await context.bot.send_message(ADMIN_ID, f"⚠️ Disputa {match_id}")
            return

        cursor.execute("UPDATE matches SET status='finished' WHERE match_id=?", (match_id,))
        conn.commit()

        loser = p2 if winner == p1 else p1
        win_amount = amount * 2

        msg = f"""
🏆 RESULTADO FINAL

⚔️ {get_name(p1)} vs {get_name(p2)}

🥇 GANADOR: {get_name(winner)}
💀 PERDEDOR: {get_name(loser)}

💰 PREMIO: {win_amount}€
"""
        await context.bot.send_message(GROUP_ID, msg)
        await context.bot.send_message(winner, f"🎉 Has ganado {win_amount}€")

# ================= BOTONES =================
async def button(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = q.from_user.id

    if data == "accept":
        return await accept(update, context)

    if data.startswith("payok"):
        if uid != ADMIN_ID:
            return

        _, u, amount = data.split("_")
        u = int(u); amount = int(amount)

        cursor.execute("UPDATE users SET payment_pending=0 WHERE user_id=?", (u,))
        conn.commit()

        queue[amount].append(u)
        await context.bot.send_message(u, f"✅ Pago confirmado {amount}€")
        await try_match(amount, context)

    if data.startswith("win") or data.startswith("lose"):
        match_id = int(data.split("_")[1])

        cursor.execute("SELECT p1,p2 FROM matches WHERE match_id=?", (match_id,))
        p1,p2 = cursor.fetchone()

        field = "r1" if uid == p1 else "r2"
        val = "win" if "win" in data else "lose"

        cursor.execute(f"UPDATE matches SET {field}=? WHERE match_id=?", (val, match_id))
        conn.commit()

        await process_result(match_id, context)

    if data.startswith("dispute"):
        match_id = int(data.split("_")[1])
        cursor.execute("UPDATE matches SET status='dispute' WHERE match_id=?", (match_id,))
        conn.commit()

        await context.bot.send_message(ADMIN_ID, f"⚠️ Disputa match {match_id}")

# ================= LOGS =================
async def logs(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM matches ORDER BY match_id DESC LIMIT 10")
    rows = cursor.fetchall()

    text = "📊 MATCHES\n\n"
    for r in rows:
        text += f"{r[0]} | {r[1]} vs {r[2]} | {r[6]}\n"

    await update.message.reply_text(text)

# ================= LOOP =================
async def loop(context):
    while True:
        await asyncio.sleep(60)

        now = datetime.utcnow()

        cursor.execute("SELECT match_id, created_at FROM matches WHERE status='playing'")
        for match_id, created_at in cursor.fetchall():
            created = datetime.fromisoformat(created_at)

            if (now - created).seconds > MATCH_TIMEOUT:
                cursor.execute("UPDATE matches SET status='cancelled' WHERE match_id=?", (match_id,))
                conn.commit()

                await context.bot.send_message(GROUP_ID, f"⏱️ Match {match_id} cancelado")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), play))
    app.add_handler(CallbackQueryHandler(button))

    async def post_init(app):
        asyncio.create_task(loop(app))

    app.post_init = post_init

    app.run_polling()

if __name__ == "__main__":
    main()
