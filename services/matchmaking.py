# services/matchmaking.py

import time
import random
import string
import logging
from datetime import datetime
from aiogram import Bot

import utils.database as db
from config import (ADMIN_ID, GROUP_ID,
                    TIMEOUT_REPORTAR_MINUTOS)
from keyboards.buttons import kb_report_result
from messages.texts import MATCH_FOUND, GROUP_MATCH_FOUND, REPORT_RESULT_MSG

logger = logging.getLogger(__name__)


def generate_match_id() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"UF-{today}-{suffix}"


async def try_match(bot: Bot, new_player_id: int, amount: int):
    """
    Busca rival en la cola para new_player_id con el mismo stake.
    Si encuentra rival, crea el partido, notifica y limpia la cola.
    """
    rival = db.find_rival(new_player_id, amount)
    if not rival:
        return  # Nadie esperando con ese stake

    rival_id = rival["user_id"]
    rival_name = rival["username"] or str(rival_id)
    new_player = db.get_user(new_player_id)
    new_name = new_player["username"] if new_player else str(new_player_id)

    match_id = generate_match_id()

    # Crear partido
    db.create_match(match_id, new_player_id, rival_id, amount, TIMEOUT_REPORTAR_MINUTOS)

    # Sacar a ambos de la cola
    rival_msg_id = rival["group_msg_id"]
    db.remove_from_queue(new_player_id)
    db.remove_from_queue(rival_id)

    # Actualizar estados
    db.set_state(new_player_id, "IN_MATCH")
    db.set_state(rival_id, "IN_MATCH")

    # Borrar mensajes "en espera" del grupo
    for msg_id in [rival_msg_id]:
        if msg_id:
            try:
                await bot.delete_message(GROUP_ID, msg_id)
            except Exception:
                pass

    # Mensaje al grupo
    group_msg = await bot.send_message(
        GROUP_ID,
        GROUP_MATCH_FOUND.format(p1=new_name, p2=rival_name, amount=amount, match_id=match_id),
        parse_mode="Markdown"
    )
    db.set_match_group_msg(match_id, group_msg.message_id)

    # Notificar a jugador 1
    await bot.send_message(
        new_player_id,
        MATCH_FOUND.format(rival=rival_name, amount=amount, match_id=match_id),
        parse_mode="Markdown"
    )

    # Notificar a jugador 2
    await bot.send_message(
        rival_id,
        MATCH_FOUND.format(rival=new_name, amount=amount, match_id=match_id),
        parse_mode="Markdown"
    )

    # Enviar botones de resultado a cada jugador
    await bot.send_message(
        new_player_id,
        REPORT_RESULT_MSG.format(match_id=match_id),
        parse_mode="Markdown",
        reply_markup=kb_report_result(match_id)
    )
    await bot.send_message(
        rival_id,
        REPORT_RESULT_MSG.format(match_id=match_id),
        parse_mode="Markdown",
        reply_markup=kb_report_result(match_id)
    )

    logger.info(f"Match creado: {match_id} | {new_player_id} vs {rival_id} | {amount}€")
