# messages/texts.py
# Todos los textos del bot en español e inglés.
# Formato: cada clave devuelve un string bilingüe listo para enviar.

def t(es: str, en: str) -> str:
    return f"{es}\n\n{en}"


# ── BIENVENIDA AL GRUPO ───────────────────────────────────────────────────────

WELCOME_NEW_MEMBER = t(
    "👋 ¡Bienvenido/a a Underground FUT, {name}!\n"
    "Para participar debes leer y aceptar las reglas.\n"
    "Abre el bot en privado y pulsa START: @futelite_bot",

    "👋 Welcome to Underground FUT, {name}!\n"
    "To participate you must read and accept the rules.\n"
    "Open the bot in private and press START: @futelite_bot"
)

# ── INICIO EN PRIVADO ─────────────────────────────────────────────────────────

WELCOME_PRIVATE = t(
    "⚽ Bienvenido/a a *Underground FUT*.\n"
    "Lee las reglas completas a continuación y acepta para continuar.",

    "⚽ Welcome to *Underground FUT*.\n"
    "Read the full rules below and accept to continue."
)

RULES_ES = """📋 *REGLAMENTO — UNDERGROUND FUT*

*General*
La comunidad está reservada exclusivamente para mayores de 18 años. Ambos jugadores deben grabar todos los partidos. Sin grabación, pierdes el derecho a reclamar. Underground FUT se reserva el derecho de retransmitir los partidos en Twitch.

*Telegram*
Necesitas un usuario de Telegram en formato @usuario y tener activado @futelite\\_bot.

*Pagos*
El pago se realiza antes de solicitar el emparejamiento. El dinero queda retenido hasta validar el resultado. El premio se abona en un máximo de 12 horas tras la validación. Prohibido tener varias cuentas o pactar partidas.

*Reglas del partido*
• Modalidad: Partido Amistoso Online, configuración por defecto.
• Duración: 6 minutos por parte.
• El empate no es válido → se juega prórroga y penaltis.
• Solo equipos Ultimate Team.
• Prohibidos sliders y hándicaps.
• Estrictamente 1 vs 1.
• Prohibida la pérdida de tiempo intencional.

*Tiempos*
• 15 min para contactar al rival tras el emparejamiento.
• Máximo 1 hora para jugar.
• Máximo 2 horas para reportar el resultado.

*Desconexiones*
• Va perdiendo y se desconecta → gana el rival.
• Va ganando y se desconecta → se repite el partido.
• Empate con 11 vs 11 → se reinicia con mismo lineup.
• Empate con tarjeta roja → gana quien tiene más jugadores.
• Abandono voluntario → gana el rival, sin excepción.

*Fair Play*
Insultos o comportamiento tóxico = expulsión inmediata. Prohibido usar bugs. Prohibida la desconexión injustificada.

*Anti-Trampa*
Uso de programas externos, cuentas prestadas, resultados pactados o patrones sospechosos = expulsión inmediata y pérdida del saldo.

*Resultados*
• Ambos reportan el mismo resultado → validación automática.
• Resultados distintos → disputa. El admin revisa las grabaciones y decide en máx. 48 horas.
• Si ninguno reporta en 2 horas → ambos pierden el dinero."""

RULES_EN = """📋 *REGULATIONS — UNDERGROUND FUT*

*General*
The community is strictly for players over 18 years old. Both players must record all matches. Without a recording, you lose the right to claim. Underground FUT reserves the right to stream matches on Twitch.

*Telegram*
You need a Telegram username in @username format and must activate @futelite\\_bot.

*Payments*
Payment is made before requesting matchmaking. Money is held until the result is validated. The prize is paid within a maximum of 12 hours after validation. Multiple accounts or arranged matches are strictly forbidden.

*Match Rules*
• Mode: Online Friendly Match, default settings only.
• Duration: 6 minutes per half.
• Draws are not valid → extra time and penalties must be played.
• Only Ultimate Team squads allowed.
• Sliders and handicaps are prohibited.
• Strictly 1 vs 1.
• Intentional time-wasting is forbidden.

*Time Limits*
• 15 min to contact your opponent after matchmaking.
• Maximum 1 hour to play.
• Maximum 2 hours to report the result.

*Disconnections*
• Losing player disconnects → opponent wins.
• Winning player disconnects → match is replayed.
• Draw with 11 vs 11 → restart with same lineup.
• Draw with red card → player with more players on field wins.
• Voluntary disconnection → opponent wins, no exceptions.

*Fair Play*
Insults or toxic behavior = immediate expulsion. Using bugs is forbidden. Unjustified disconnection is forbidden.

*Anti-Cheat*
External programs, borrowed accounts, arranged results or suspicious patterns = immediate expulsion and loss of all funds.

*Results*
• Both report the same result → automatic validation.
• Results don't match → dispute. Admin reviews recordings and decides within max. 48 hours.
• Neither reports within 2 hours → both lose their money."""

ACCEPT_BUTTON = "✅ Acepto / I Accept"

# ── POST-ACEPTACIÓN ───────────────────────────────────────────────────────────

RULES_ACCEPTED = t(
    "✅ Ya puedes jugar. Pulsa el botón PLAY para empezar.",
    "✅ You can now play. Press the PLAY button to start."
)

PLAY_BUTTON = "▶️ PLAY"

# ── SELECCIÓN DE STAKE ────────────────────────────────────────────────────────

SELECT_STAKE = t(
    "💶 Elige el importe que quieres apostar:",
    "💶 Choose the amount you want to bet:"
)

# ── INSTRUCCIONES DE PAGO ─────────────────────────────────────────────────────

PAYMENT_INSTRUCTIONS = t(
    "💳 Debes enviar *{amount}€* a través de PayPal a:\n"
    "{paypal}\n\n"
    "⏰ Tienes *15 minutos* para realizar el pago.\n"
    "Cuando lo hayas hecho, pulsa el botón de abajo.",

    "💳 You must send *{amount}€* via PayPal to:\n"
    "{paypal}\n\n"
    "⏰ You have *15 minutes* to complete the payment.\n"
    "Once done, press the button below."
)

PAID_BUTTON = "💸 He pagado / I have paid"

PAYMENT_PENDING_ADMIN = (
    "💰 *PAGO PENDIENTE DE VALIDAR*\n\n"
    "Jugador: @{username} (`{user_id}`)\n"
    "Importe: *{amount}€*\n"
    "ID Pago: `{payment_id}`"
)

VALIDATE_PAYMENT_BUTTON = "✅ Validar pago"
REJECT_PAYMENT_BUTTON = "❌ Rechazar"

PAYMENT_EXPIRED_PLAYER = t(
    "⏰ El tiempo para realizar el pago ha expirado (15 min).\n"
    "Pulsa PLAY si quieres intentarlo de nuevo.",

    "⏰ The payment time has expired (15 min).\n"
    "Press PLAY if you want to try again."
)

PAYMENT_REJECTED_PLAYER = t(
    "❌ El admin no pudo confirmar tu pago.\n"
    "Contacta con el admin si crees que es un error.\n"
    "Pulsa PLAY para intentarlo de nuevo.",

    "❌ The admin could not confirm your payment.\n"
    "Contact the admin if you think this is an error.\n"
    "Press PLAY to try again."
)

# ── COLA ──────────────────────────────────────────────────────────────────────

PAYMENT_VALIDATED_PLAYER = t(
    "✅ Pago de *{amount}€* confirmado. ¡Ya estás en cola buscando rival!\n"
    "Te avisaré en cuanto encuentre oponente.",

    "✅ Payment of *{amount}€* confirmed. You are now in the queue looking for an opponent!\n"
    "I will notify you as soon as a match is found."
)

# ── MENSAJES GRUPO (solo estos 3 tipos) ───────────────────────────────────────

GROUP_WAITING = "⏳ @{username} está esperando rival — *{amount}€*"

GROUP_MATCH_FOUND = "⚔️ @{p1} vs @{p2} — *{amount}€* — `{match_id}`"

GROUP_WINNER = "🏆 ¡Felicidades @{username}! Has ganado *{amount}€* 🎉\n\nCongratulations @{username}! You won *{amount}€* 🎉"

GROUP_PENALTY = "⚠️ Un usuario ha sido bloqueado temporalmente por incumplir las normas.\n\nA user has been temporarily blocked for violating the rules."

# ── MATCHMAKING ───────────────────────────────────────────────────────────────

MATCH_FOUND = t(
    "⚽ *¡Rival encontrado!*\n\n"
    "Tu rival es: @{rival}\n"
    "Stake: *{amount}€*\n"
    "Partido: `{match_id}`\n\n"
    "📌 Tienes *15 minutos* para contactar con tu rival.\n"
    "⏰ Máximo *1 hora* para jugar el partido.\n"
    "📊 Máximo *2 horas* para reportar el resultado.\n\n"
    "Cuando termines, usa el botón de resultado que te llegará.",

    "⚽ *Opponent found!*\n\n"
    "Your opponent is: @{rival}\n"
    "Stake: *{amount}€*\n"
    "Match: `{match_id}`\n\n"
    "📌 You have *15 minutes* to contact your opponent.\n"
    "⏰ Maximum *1 hour* to play the match.\n"
    "📊 Maximum *2 hours* to report the result.\n\n"
    "When you finish, use the result button that will be sent to you."
)

REPORT_RESULT_MSG = t(
    "⚽ *Reporta el resultado* — `{match_id}`\n\n"
    "¿Cómo terminó el partido?",

    "⚽ *Report the result* — `{match_id}`\n\n"
    "How did the match end?"
)

WON_BUTTON = "🟢 Gané / I won"
LOST_BUTTON = "🔴 Perdí / I lost"

# ── RESULTADO VÁLIDO ──────────────────────────────────────────────────────────

RESULT_WINNER_PRIVATE = t(
    "🏆 *¡Ganaste!*\n\n"
    "Partido: `{match_id}`\n"
    "Premio: *{prize}€*\n\n"
    "Recibirás el pago en un máximo de 12 horas.",

    "🏆 *You won!*\n\n"
    "Match: `{match_id}`\n"
    "Prize: *{prize}€*\n\n"
    "You will receive payment within a maximum of 12 hours."
)

RESULT_LOSER_PRIVATE = t(
    "😔 Has perdido el partido `{match_id}`.\n\n"
    "Podrás jugar de nuevo en 10 minutos.",

    "😔 You lost the match `{match_id}`.\n\n"
    "You will be able to play again in 10 minutes."
)

ADMIN_PAY_WINNER = (
    "💸 *ACCIÓN REQUERIDA — PAGAR AL GANADOR*\n\n"
    "Partido: `{match_id}`\n"
    "Bote total: {bote}€ (stake × 2)\n"
    "Tu comisión (15%): -{comision}€\n"
    "─────────────────\n"
    "💰 Debes pagar: *{neto}€* a @{username}"
)

# ── DISPUTAS ──────────────────────────────────────────────────────────────────

DISPUTE_OPENED_PLAYER = t(
    "⚠️ *Disputa abierta* — `{match_id}`\n\n"
    "Los resultados reportados no coinciden.\n"
    "Por favor, envía tu explicación y la grabación del partido al admin.\n\n"
    "El admin dará un veredicto en un máximo de *48 horas*.",

    "⚠️ *Dispute opened* — `{match_id}`\n\n"
    "The reported results do not match.\n"
    "Please send your explanation and the match recording to the admin.\n\n"
    "The admin will give a verdict within a maximum of *48 hours*."
)

DISPUTE_ADMIN_NOTIFY = (
    "⚠️ *NUEVA DISPUTA*\n\n"
    "Partido: `{match_id}`\n"
    "@{p1} vs @{p2}\n"
    "Stake: *{amount}€*\n\n"
    "Cada jugador reportó un resultado diferente.\n"
    "Usa /disputas para ver la lista completa."
)

DISPUTE_VERDICT_WINNER = t(
    "✅ *Veredicto del admin* — `{match_id}`\n\n"
    "El admin ha resuelto la disputa a tu favor.\n"
    "Premio: *{prize}€* — se abonará en un máximo de 12 horas.",

    "✅ *Admin verdict* — `{match_id}`\n\n"
    "The admin has resolved the dispute in your favor.\n"
    "Prize: *{prize}€* — will be paid within a maximum of 12 hours."
)

DISPUTE_VERDICT_LOSER = t(
    "❌ *Veredicto del admin* — `{match_id}`\n\n"
    "El admin ha resuelto la disputa. No has ganado esta partida.",

    "❌ *Admin verdict* — `{match_id}`\n\n"
    "The admin has resolved the dispute. You did not win this match."
)

DISPUTE_CANCELLED_PLAYER = t(
    "🔄 El admin ha anulado el partido `{match_id}`.\n"
    "Recibirás tu stake ({amount}€) en un máximo de 12 horas.",

    "🔄 The admin has cancelled the match `{match_id}`.\n"
    "You will receive your stake ({amount}€) within a maximum of 12 hours."
)

# ── ANTITRAMPA — mensajes al jugador ─────────────────────────────────────────

BLOCKED_PLAYER = t(
    "🚫 Tu cuenta ha sido bloqueada temporalmente.\n\n"
    "El sistema ha detectado un comportamiento irregular en tu cuenta.\n"
    "Este proceso es automático y no es personal.\n\n"
    "Podrás volver a jugar en *{hours} horas*.\n"
    "Por favor, respeta las normas de la comunidad.",

    "🚫 Your account has been temporarily blocked.\n\n"
    "The system has detected irregular behavior on your account.\n"
    "This process is automatic and not personal.\n\n"
    "You will be able to play again in *{hours} hours*.\n"
    "Please respect the community rules."
)

BANNED_PLAYER = t(
    "⛔ Tu cuenta ha sido suspendida permanentemente de Underground FUT.\n\n"
    "Si crees que esto es un error, contacta con el admin.",

    "⛔ Your account has been permanently suspended from Underground FUT.\n\n"
    "If you believe this is an error, please contact the admin."
)

COOLDOWN_ACTIVE = t(
    "⏸️ Debes esperar *{minutes} minutos* antes de jugar otro partido.",
    "⏸️ You must wait *{minutes} minutes* before playing another match."
)

ALREADY_IN_FLOW = t(
    "Ya tienes una acción en curso. Usa /estado para ver tu situación.",
    "You already have an ongoing action. Use /estado to check your status."
)

NOT_REGISTERED = t(
    "Primero debes aceptar las reglas. Abre el bot con /start",
    "You must accept the rules first. Open the bot with /start"
)

# ── ESTADO ────────────────────────────────────────────────────────────────────

STATUS_MESSAGES = {
    "IDLE":                t("😴 Sin actividad. Pulsa PLAY para buscar rival.", "😴 No activity. Press PLAY to find an opponent."),
    "WAITING_PAYMENT":     t("💳 Esperando validación de tu pago.", "💳 Waiting for your payment to be validated."),
    "IN_QUEUE":            t("⏳ En cola buscando rival.", "⏳ In queue looking for an opponent."),
    "IN_MATCH":            t("⚽ Partido en curso.", "⚽ Match in progress."),
    "IN_DISPUTE":          t("⚠️ Disputa abierta. El admin está revisando.", "⚠️ Dispute open. The admin is reviewing."),
    "COOLDOWN":            t("⏸️ En cooldown. Espera unos minutos.", "⏸️ On cooldown. Wait a few minutes."),
    "BLOCKED":             t("🚫 Cuenta bloqueada temporalmente.", "🚫 Account temporarily blocked."),
    "BANNED":              t("⛔ Cuenta suspendida permanentemente.", "⛔ Account permanently suspended."),
}
