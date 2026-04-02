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
PAYPAL_LINK = "https://paypal.me/bucefalo74"

logging.basicConfig(level=logging.INFO)

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    accepted_rules INTEGER DEFAULT 0,
    authorized_amount INTEGER DEFAULT 0
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

conn.commit()

# ================= MEMORIA =================
queue = {5: [], 10: [], 20: [], 50: [], 100: []}
user_cache = {}
user_match = {}
match_id_counter = 1

# ================= REGLAS (NO TOCADAS) =================
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
# 👆 DEJA EXACTAMENTE TU TEXTO ORIGINAL AQUÍ

# ================= BIENVENIDA =================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"""👋 Bienvenido / Welcome {user.mention_html()}
👉 Te he enviado las reglas por privado
👉 Check your private messages

⚠️ Si no las ves, inicia el bot:
⚠️ If you don't see it, start the bot:
https://t.me/Futelite_bot""",
            parse_mode="HTML"
        )

        try:
            kb = [[InlineKeyboardButton("✅ Acepto / I Accept", callback_data="accept")]]
            await context.bot.send_message(
                chat_id=user.id,
                text=RULES,
                reply_markup=InlineKeyboardMarkup(kb)
            )
        except:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"⚠️ {user.mention_html()} NO ha iniciado el bot privado",
                parse_mode="HTML"
            )

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("✅ Acepto / I Accept", callback_data="accept")]]
    await update.message.reply_text(RULES, reply_markup=InlineKeyboardMarkup(kb))

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (uid,))
    cursor.execute("UPDATE users SET accepted_rules=1 WHERE user_id=?", (uid,))
    conn.commit()

    await q.message.edit_text("✅ Reglas aceptadas / Rules accepted")

# ================= UTILS =================
def get_name(uid):
    u = user_cache.get(uid)
    return f"@{u.username}" if u and u.username else str(uid)

def accepted(uid):
    cursor.execute("SELECT accepted_rules FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    return r and r[0] == 1

# ================= MATCH =================
async def try_match(amount, context):
    global match_id_counter

    if len(queue[amount]) >= 2:
        p1 = queue[amount].pop(0)
        p2 = queue[amount].pop(0)

        match_id = match_id_counter
        match_id_counter += 1

        now = datetime.utcnow()

        cursor.execute(
            "INSERT INTO matches VALUES (?,?,?,?,?,?,?,?)",
            (match_id, p1, p2, amount, None, None, "playing", now.isoformat())
        )
        conn.commit()

        user_match[p1] = match_id
        user_match[p2] = match_id

        msg = f"""⚔️ MATCH {amount}€
{get_name(p1)} vs {get_name(p2)}

📩 Contacta por privado / Contact via DM
⏱ 15 min para coordinar
⏱ 1h para jugar

👉 Reporta:
 /report win
 /report lose
"""

        await context.bot.send_message(GROUP_ID, msg)

        for p in [p1, p2]:
            try:
                await context.bot.send_message(p, msg)
            except:
                await context.bot.send_message(
                    GROUP_ID,
                    f"⚠️ {get_name(p)} NO ha iniciado el bot"
                )

# ================= REPORT =================
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in user_match:
        return

    if len(context.args) == 0:
        return

    result = context.args[0]
    match_id = user_match[user.id]

    cursor.execute("SELECT * FROM matches WHERE match_id=?", (match_id,))
    m = cursor.fetchone()

    if m[6] != "playing":
        return

    if user.id == m[1]:
        if m[4]: return
        cursor.execute("UPDATE matches SET r1=? WHERE match_id=?", (result, match_id))
    else:
        if m[5]: return
        cursor.execute("UPDATE matches SET r2=? WHERE match_id=?", (result, match_id))

    conn.commit()

    cursor.execute("SELECT r1,r2 FROM matches WHERE match_id=?", (match_id,))
    r1, r2 = cursor.fetchone()

    if r1 and r2:

        if r1 == r2:
            winner = m[1] if r1 == "win" else m[2]

            cursor.execute("UPDATE matches SET status='finished' WHERE match_id=?", (match_id,))
            conn.commit()

            user_match.pop(m[1], None)
            user_match.pop(m[2], None)

            await context.bot.send_message(
                GROUP_ID,
                f"🏆 GANADOR / WINNER: {get_name(winner)}\n🎉 Felicidades!"
            )

        else:
            cursor.execute("UPDATE matches SET status='dispute' WHERE match_id=?", (match_id,))
            conn.commit()

            await context.bot.send_message(
                GROUP_ID,
                "⚠️ DISPUTA / DISPUTE — Admin revisará"
            )

# ================= AUTO CONTROL =================
async def check_matches_loop(app):
    while True:
        now = datetime.utcnow()

        cursor.execute("SELECT match_id, created_at, status FROM matches")
        matches = cursor.fetchall()

        for m in matches:
            match_id, created_at, status = m
            created_at = datetime.fromisoformat(created_at)

            if status == "playing":
                if now - created_at > timedelta(hours=1):
                    cursor.execute("UPDATE matches SET status='expired' WHERE match_id=?", (match_id,))
                    conn.commit()

                    await app.bot.send_message(
                        GROUP_ID,
                        f"⌛ MATCH {match_id} EXPIRADO / EXPIRED"
                    )

        await asyncio.sleep(60)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report))

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^play"), lambda u,c: None))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))

    # ================= FIX CRASH LOOP =================
    async def safe_check(context):
        await check_matches_loop(context.application)

    if app.job_queue:
        app.job_queue.run_repeating(safe_check, interval=60, first=10)
    else:
        async def fallback_loop(app):
            while True:
                await check_matches_loop(app)
                await asyncio.sleep(60)

        async def start_fallback(app):
            asyncio.create_task(fallback_loop(app))

        app.post_init = start_fallback
    # =================================================

    app.run_polling()
