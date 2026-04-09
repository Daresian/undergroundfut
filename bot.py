import logging
import sqlite3
import os
import time


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler


TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PAYPAL_LINK = "https://paypal.me/bucefalo74"


logging.basicConfig(level=logging.INFO)


# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()


cursor.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
username TEXT,
rules INTEGER DEFAULT 0,
paid INTEGER DEFAULT 0,
last_match INTEGER DEFAULT 0
)""")


cursor.execute("""CREATE TABLE IF NOT EXISTS queue(
user_id INTEGER,
amount INTEGER,
time INTEGER
)""")


cursor.execute("""CREATE TABLE IF NOT EXISTS matches(
id INTEGER PRIMARY KEY AUTOINCREMENT,
p1 INTEGER,
p2 INTEGER,
amount INTEGER,
r1 TEXT,
r2 TEXT,
status TEXT,
created INTEGER
)""")


conn.commit()


# ================= REGLAS COMPLETAS (SIN TOCAR) =================


RULES = [


"""📜 REGLAMENTO DE LA COMUNIDAD UNDERGROUND FUT


🇪🇸 ESPAÑOL


Reglamento General
La Comunidad Underground Fut está reservada exclusivamente para personas mayores de 18 años. Es fundamental que ambos participantes graben todos los partidos, ya que la grabación será el único elemento válido en caso de discrepancia sobre el resultado del encuentro. Si un jugador no realiza la grabación, perderá el derecho a reclamar el dinero en caso de que surja algún desacuerdo. Además, Underground Fut se reserva el derecho de subir o retransmitir los partidos a través de su cuenta de Twitch.


Reglas de Emparejamiento en Telegram
Para participar en los emparejamientos, cada jugador debe disponer de un usuario en Telegram (en formato @usuario) y activar el bot correspondiente @Futelite_bot. Esto es imprescindible para acceder a los partidos y ser emparejado correctamente.""",


"""Reglas de Pago
Está terminantemente prohibido tener varias cuentas y pactar partidas entre ellas. El sistema monitoriza patrones de juego para detectar posibles fraudes. Cualquier intento de engaño supondrá la expulsión inmediata de la comunidad y la pérdida de todo el saldo ingresado. El pago debe realizarse antes de solicitar el emparejamiento, permitiendo a cada jugador añadir la cantidad que desee a su monedero.


El dinero jugado permanecerá retenido hasta la validación del resultado, y el premio será autorizado y abonado tras la validación, en un plazo máximo de 12 horas.""",


"""Reglas de Partido
Los partidos se disputarán en la modalidad Partido Amistoso online, utilizando siempre la configuración por defecto del juego. No está permitido modificar los ajustes, y la duración será de 6 minutos por parte. Todos los partidos deben finalizar con una victoria; el empate no es un resultado válido, por lo que se debe jugar prórroga y penaltis si es necesario. Solo se pueden utilizar equipos Ultimate Team.


Está prohibida la utilización de sliders y hándicaps. En caso de incumplimiento, el jugador será expulsado de la comunidad y perderá todo el dinero ingresado.""",


"""Los partidos son exclusivamente 1 contra 1, por lo que no se permite la participación de dos o más personas en un mismo equipo. Tampoco está permitida la pérdida manifiesta de tiempo mediante la posesión del balón; los administradores revisarán las grabaciones y sancionarán con la pérdida del partido a quien infrinja esta norma.


Tiempo para Jugar
Tras realizar el emparejamiento, los usuarios dispondrán de un máximo de 15 minutos para ponerse en contacto y acordar el inicio del partido. Una vez hecho el “match”, tendrán un máximo de 1 hora para jugar y comunicar el resultado.""",


"""Desconexiones
Es imprescindible que ambos jugadores graben los partidos para conservar el derecho a reclamar en caso de disputa.


Desconexión Aparentemente Involuntaria
1. Si se desconecta el jugador que va perdiendo, la victoria se otorgará al jugador que va ganando.
2. Si se desconecta el jugador que va ganando, el partido se repetirá.
3. En caso de empate con ambos equipos jugando 11 contra 11, el partido se reiniciará con la misma alineación y se jugará el tiempo restante.
4. En caso de empate y que uno de los equipos tenga una o más tarjetas rojas, la victoria será adjudicada al jugador que conserve los 11 jugadores o que tenga menos tarjetas rojas.


Desconexión Voluntaria (Abandono de partida)
1. En caso de desconexión voluntaria, la victoria será concedida al jugador que mantiene la conexión, independientemente del resultado en el momento de la desconexión.""",


"""Fair Play
• Está prohibido insultar. Comportamiento tóxico. Expulsión Inmediata de la comunidad.
• No se permite el uso de bugs.
• La pérdida de tiempo intencional está sancionada.
• No está permitido desconectarse del partido de forma injustificada.


🇬🇧 ENGLISH


General Rules
The Underground Fut Community is strictly for users over 18 years old. Both participants must record all matches, as recordings are the only valid evidence in case of disputes. If a player does not record the match, they lose the right to claim any money in case of disagreement. Additionally, Underground Fut reserves the right to stream matches on its Twitch channel.""",


"""Telegram Matchmaking Rules
To participate in matchmaking, each player must have a Telegram username (in the format @username) and activate the bot @Futelite_bot. This is mandatory to access matches and be paired correctly.


Payment Rules
Having multiple accounts and arranging matches between them is strictly prohibited. The system monitors gameplay patterns to detect fraud. Any attempt to cheat will result in immediate expulsion from the community and loss of all deposited funds. Payment must be made before requesting matchmaking, allowing each player to add funds to their wallet. The money played will remain locked until result validation, and the prize will be authorized and paid within a maximum of 12 hours.""",


"""Match Rules
Matches must be played in Online Friendly mode using default settings. Settings cannot be modified, and each half must last 6 minutes. All matches must end with a winner; draws are not allowed, so extra time and penalties must be played if necessary. Only Ultimate Team squads are allowed.


The use of sliders and handicaps is strictly forbidden. Violations will result in expulsion and loss of funds.


Time to Play
After matchmaking, players have a maximum of 15 minutes to contact each other and agree on the match start. Once matched, they have a maximum of 1 hour to play and report the result.""",


"""Disconnections
Both players must record matches to maintain the right to claim in case of disputes.


Unintentional Disconnection
1. If the losing player disconnects, the win is awarded to the winning player.
2. If the winning player disconnects, the match must be replayed.


Voluntary Disconnection (Quit)
1. If a player quits intentionally, the win is awarded to the player who remains connected, regardless of the current score.


Fair Play
• Insults and toxic behavior are strictly prohibited and will result in immediate expulsion.
• Exploiting bugs is not allowed.
• Intentional time-wasting is punishable.
• Unjustified disconnections are not allowed."""
]


# ================= ANTI TRAMPAS =================
def anti_cheat(uid):
    cursor.execute("SELECT last_match FROM users WHERE user_id=?", (uid,))
    data = cursor.fetchone()
    if not data:
        return False
    return int(time.time()) - data[0] < 30


# ================= BOT =================


async def start(update, context):
    u = update.effective_user
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (u.id, u.username,0,0,0))
    conn.commit()


    kb = [[InlineKeyboardButton("ACTIVAR", callback_data="rules_0")]]
    await update.message.reply_text(f"👋 Bienvenido {u.first_name}", reply_markup=InlineKeyboardMarkup(kb))


async def bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)", (user.id, user.username,0,0,0))
        conn.commit()


        kb = [[InlineKeyboardButton("ACTIVAR", url=f"https://t.me/{context.bot.username}?start=true")]]
        await update.message.reply_text(f"👋 Bienvenido {user.first_name}\nPulsa ACTIVAR", reply_markup=InlineKeyboardMarkup(kb))


async def rules(update, context):
    q = update.callback_query
    await q.answer()
    step = int(q.data.split("_")[1])


    if step < len(RULES):
        if step < len(RULES)-1:
            kb = [[InlineKeyboardButton("➡️", callback_data=f"rules_{step+1}")]]
        else:
            kb = [[InlineKeyboardButton("ACEPTO", callback_data="accept")]]
        await q.message.reply_text(RULES[step], reply_markup=InlineKeyboardMarkup(kb))


async def accept(update, context):
    q = update.callback_query
    await q.answer()
    cursor.execute("UPDATE users SET rules=1 WHERE user_id=?", (q.from_user.id,))
    conn.commit()
    await q.message.reply_text("✅ Reglas aceptadas. Escribe PLAY")


async def play(update, context):
    uid = update.effective_user.id


    cursor.execute("SELECT rules FROM users WHERE user_id=?", (uid,))
    res = cursor.fetchone()
    if not res or res[0] == 0:
        await update.message.reply_text("❌ Debes aceptar las reglas")
        return


    if anti_cheat(uid):
        await update.message.reply_text("⚠️ Espera antes de jugar otro partido")
        return


    kb = [[InlineKeyboardButton(str(x), callback_data=str(x))] for x in [4,10,20,50,100]]
    await update.message.reply_text("💰 Elige cantidad", reply_markup=InlineKeyboardMarkup(kb))


async def amount(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["amount"] = int(q.data)
    await q.message.reply_text(f"Paga aquí:\n{PAYPAL_LINK}\n\nEscribe PAGADO")


async def paid(update, context):
    uid = update.effective_user.id
    amt = context.user_data.get("amount")


    if not amt:
        await update.message.reply_text("❌ Primero PLAY")
        return


    await context.bot.send_message(ADMIN_ID, f"/confirm {uid} {amt}")
    await update.message.reply_text("⏳ Esperando confirmación")


async def confirm(update, context):
    if update.effective_user.id != ADMIN_ID:
        return


    _, uid, amt = update.message.text.split()
    uid, amt = int(uid), int(amt)


    cursor.execute("UPDATE users SET paid=1,last_match=? WHERE user_id=?", (int(time.time()),uid))
    conn.commit()


    cursor.execute("SELECT user_id FROM queue WHERE amount=?", (amt,))
    rival = cursor.fetchone()


    if rival:
        rid = rival[0]


        if uid == rid:
            await update.message.reply_text("⚠️ MULTICUENTA DETECTADA")
            return


        cursor.execute("DELETE FROM queue WHERE user_id=?", (rid,))
        cursor.execute("INSERT INTO matches (p1,p2,amount,status,created) VALUES (?,?,?,?,?)", (uid,rid,amt,"playing",int(time.time())))
        conn.commit()


        await context.bot.send_message(uid,"🎮 Rival encontrado")
        await context.bot.send_message(rid,"🎮 Rival encontrado")
    else:
        cursor.execute("INSERT INTO queue VALUES (?,?,?)", (uid,amt,int(time.time())))
        conn.commit()
        await context.bot.send_message(uid,"⏳ Esperando rival")


async def result(update, context):
    txt = update.message.text
    uid = update.effective_user.id


    if "-" not in txt:
        return


    cursor.execute("SELECT * FROM matches WHERE (p1=? OR p2=?) AND status='playing'", (uid,uid))
    m = cursor.fetchone()
    if not m:
        return


    mid = m[0]


    if m[1] == uid:
        cursor.execute("UPDATE matches SET r1=? WHERE id=?", (txt,mid))
    else:
        cursor.execute("UPDATE matches SET r2=? WHERE id=?", (txt,mid))
    conn.commit()


    cursor.execute("SELECT r1,r2,amount,p1,p2 FROM matches WHERE id=?", (mid,))
    r1,r2,amt,p1,p2 = cursor.fetchone()


    if r1 and r2:
        if r1 == r2:
            g1,g2 = map(int,r1.split("-"))
            winner = p1 if g1>g2 else p2
            prize = round(amt*2*0.7,2)


            await context.bot.send_message(winner,f"🏆 GANADOR\n💰 {prize}€")
        else:
            await context.bot.send_message(ADMIN_ID,f"⚠️ DISPUTA MATCH {mid}")


async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return


    cursor.execute("SELECT COUNT(*) FROM users")
    u = cursor.fetchone()[0]


    cursor.execute("SELECT COUNT(*) FROM matches")
    m = cursor.fetchone()[0]


    await update.message.reply_text(f"👑 ADMIN\nUsuarios: {u}\nMatches: {m}")


async def reset_users(update, context):
    if update.effective_user.id != ADMIN_ID:
        return


    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM queue")
    cursor.execute("DELETE FROM matches")
    conn.commit()


    await update.message.reply_text("♻️ RESET COMPLETO")


def main():
    app = ApplicationBuilder().token(TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("reset_users", reset_users))
    app.add_handler(CommandHandler("admin", admin))


    app.add_handler(CallbackQueryHandler(rules, pattern="rules_"))
    app.add_handler(CallbackQueryHandler(accept, pattern="accept"))
    app.add_handler(CallbackQueryHandler(amount, pattern="^[0-9]+$"))


    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))


    app.add_handler(MessageHandler(filters.Regex("(?i)^play$"), play))
    app.add_handler(MessageHandler(filters.Regex("(?i)^pagado$"), paid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, result))


    print("🔥 BOT 100% FUNCIONANDO")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
