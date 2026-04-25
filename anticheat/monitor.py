# anticheat/monitor.py

import time
import logging
from aiogram import Bot

import utils.database as db
from config import ADMIN_ID, GROUP_ID, BLOQUEO_HORAS
from messages.texts import BLOCKED_PLAYER, GROUP_PENALTY

logger = logging.getLogger(__name__)

# Códigos de antitrampa
CODES = {
    "AC01": "Intentó jugar sin aceptar reglas",
    "AC02": "Intentó jugar sin pago validado",
    "AC03": "Intentó reportar resultado sin partido activo",
    "AC04": "Intentó reportar resultado fuera de tiempo",
    "AC05": "Intentó saltarse pasos del flujo",
    "AC06": "Intentó usar botones o callbacks que no le corresponden",
    "AC07": "Intentó repetir 'He pagado' sin pago pendiente",
    "AC08": "Intentó jugar antes de que termine el cooldown",
    "AC09": "Reportó haber ganado cuando el rival también reportó ganar",
    "AC10": "Patrón de multicuenta detectado",
    "AC11": "Intentó manipular el stake",
    "AC12": "Intentó manipular el callback data",
    "AC13": "Intentó manipular el ID del partido",
    "AC14": "Intentó cancelar partido sin motivo válido",
    "AC15": "Ratio de victorias anómalo",
}


async def trigger(bot: Bot, user_id: int, code: str, detail: str = ""):
    """Aplica bloqueo, notifica al jugador, al admin y al grupo."""
    user = db.get_user(user_id)
    username = user["username"] if user else str(user_id)
    description = CODES.get(code, code)

    # Registrar evento
    db.log_anticheat(user_id, code, detail or description)

    # Bloquear usuario
    db.set_blocked(user_id, BLOQUEO_HORAS)

    # Mensaje privado al jugador — bilingüe, respetuoso
    try:
        await bot.send_message(
            user_id,
            BLOCKED_PLAYER.format(hours=BLOQUEO_HORAS),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"No se pudo notificar bloqueo al jugador {user_id}: {e}")

    # Mensaje privado al admin — con detalle técnico
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🚨 *ANTITRAMPA — BLOQUEO AUTOMÁTICO*\n\n"
            f"Jugador: @{username} (`{user_id}`)\n"
            f"Código: `{code}`\n"
            f"Motivo: {description}\n"
            f"Detalle: {detail or '—'}\n"
            f"Duración: *{BLOQUEO_HORAS} horas*\n\n"
            f"Acción recomendada: revisar historial del jugador.\n"
            f"Puedes desbloquear manualmente con /desbloquear @{username}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"No se pudo notificar al admin sobre bloqueo de {user_id}: {e}")

    # Mensaje neutro al grupo — sin nombres, sin acusaciones
    try:
        await bot.send_message(GROUP_ID, GROUP_PENALTY)
    except Exception as e:
        logger.error(f"No se pudo enviar mensaje de penalización al grupo: {e}")

    logger.info(f"Antitrampa {code} aplicado a {user_id} ({username})")


def check_user_can_play(user_id: int) -> tuple[bool, str]:
    """
    Devuelve (puede_jugar, motivo_si_no).
    Verifica estado, bloqueo, ban y cooldown.
    """
    user = db.get_user(user_id)
    if not user:
        return False, "not_registered"

    if user["state"] == "BANNED":
        return False, "banned"

    now = int(time.time())

    if user["state"] == "BLOCKED" and user["blocked_until"] > now:
        minutes = int((user["blocked_until"] - now) / 60)
        return False, f"blocked:{minutes}"

    # Si el bloqueo ya expiró, limpiar estado
    if user["state"] == "BLOCKED" and user["blocked_until"] <= now:
        db.set_state(user_id, "IDLE")

    if user["cooldown_until"] > now:
        minutes = int((user["cooldown_until"] - now) / 60)
        return False, f"cooldown:{minutes}"

    if user["state"] in ("WAITING_PAYMENT", "IN_QUEUE", "IN_MATCH", "IN_DISPUTE"):
        return False, "busy"

    return True, ""
