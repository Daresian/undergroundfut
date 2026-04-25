# handlers/results.py

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

import utils.database as db

MARGIN = 0.15  # Comisión del 15% sobre el bote total
from config import ADMIN_ID, GROUP_ID, COOLDOWN_MINUTOS, TIMEOUT_DISPUTA_HORAS
from keyboards.buttons import kb_play, kb_admin_dispute
from messages.texts import (
    RESULT_WINNER_PRIVATE, RESULT_LOSER_PRIVATE,
    ADMIN_PAY_WINNER, GROUP_WINNER,
    DISPUTE_OPENED_PLAYER, DISPUTE_ADMIN_NOTIFY
)
from anticheat.monitor import trigger as ac_trigger

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("result_"))
async def cb_result(callback: CallbackQuery, bot: Bot):
    uid = callback.from_user.id
    parts = callback.data.split("_")
    # result_{match_id}_won  OR  result_{match_id}_lost
    match_id = parts[1]
    result   = parts[2]  # "won" or "lost"

    import time
    now = int(time.time())

    # Validar que el usuario está en este partido
    match = db.get_match(match_id)
    if not match or uid not in (match["player1_id"], match["player2_id"]):
        await ac_trigger(bot, uid, "AC12", f"Intentó reportar partido ajeno: {match_id}")
        await callback.answer()
        return

    if match["status"] != "IN_PROGRESS":
        await ac_trigger(bot, uid, "AC03", f"Partido {match_id} no está en progreso")
        await callback.answer()
        return

    # Verificar tiempo límite
    if now > match["report_deadline"]:
        await ac_trigger(bot, uid, "AC04", f"Reportó fuera de tiempo en {match_id}")
        await callback.answer()
        return

    # Verificar que no haya reportado ya
    if db.has_reported(match_id, uid):
        await callback.answer(
            "Ya reportaste el resultado de este partido. / You already reported this match result.",
            show_alert=True
        )
        return

    # Guardar reporte
    db.save_report(match_id, uid, result)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(
        "✅ Resultado guardado. Esperando al rival. / Result saved. Waiting for opponent.",
        show_alert=True
    )

    # Verificar si el rival ya reportó
    reports = db.get_reports(match_id)
    if len(reports) == 2:
        await _process_results(bot, match, reports)


async def _process_results(bot: Bot, match, reports):
    match_id  = match["match_id"]
    p1_id     = match["player1_id"]
    p2_id     = match["player2_id"]
    amount    = match["amount"]

    r1 = {r["user_id"]: r["result"] for r in reports}

    r1_result = r1.get(p1_id)
    r2_result = r1.get(p2_id)

    # Caso válido: uno ganó y el otro perdió (y no coinciden en ganador)
    if r1_result == "won" and r2_result == "lost":
        winner_id = p1_id
        loser_id  = p2_id
    elif r1_result == "lost" and r2_result == "won":
        winner_id = p2_id
        loser_id  = p1_id
    else:
        # Ambos dicen lo mismo → disputa
        await _open_dispute(bot, match)
        return

    # Resultado válido
    prize = amount * 2
    winner = db.get_user(winner_id)
    loser  = db.get_user(loser_id)
    winner_name = winner["username"] if winner else str(winner_id)
    loser_name  = loser["username"]  if loser  else str(loser_id)

    db.close_match(match_id, winner_id, "COMPLETED")
    db.set_state(winner_id, "IDLE")
    db.set_state(loser_id, "IDLE")
    db.set_cooldown(winner_id, COOLDOWN_MINUTOS)
    db.set_cooldown(loser_id,  COOLDOWN_MINUTOS)

    # Notificar al ganador
    await bot.send_message(
        winner_id,
        RESULT_WINNER_PRIVATE.format(match_id=match_id, prize=prize),
        parse_mode="Markdown",
        reply_markup=kb_play()
    )

    # Notificar al perdedor
    await bot.send_message(
        loser_id,
        RESULT_LOSER_PRIVATE.format(match_id=match_id),
        parse_mode="Markdown",
        reply_markup=kb_play()
    )

    # Aviso al admin para pagar
    bote = amount * 2
    comision = round(bote * MARGIN, 2)
    neto = round(bote - comision, 2)
    await bot.send_message(
        ADMIN_ID,
        ADMIN_PAY_WINNER.format(
            match_id=match_id, bote=bote,
            comision=comision, neto=neto,
            username=winner_name
        ),
        parse_mode="Markdown"
    )

    # Mensaje público de felicitación en el grupo
    await bot.send_message(
        GROUP_ID,
        GROUP_WINNER.format(username=winner_name, amount=prize),
        parse_mode="Markdown"
    )

    db.log_audit("MATCH_COMPLETED", winner_id, match_id, f"Prize: {prize}€")
    logger.info(f"Partido {match_id} completado. Ganador: {winner_id} | Premio: {prize}€")


async def _open_dispute(bot: Bot, match):
    match_id = match["match_id"]
    p1_id    = match["player1_id"]
    p2_id    = match["player2_id"]
    amount   = match["amount"]

    db.open_dispute(match_id, TIMEOUT_DISPUTA_HORAS)
    db.set_state(p1_id, "IN_DISPUTE")
    db.set_state(p2_id, "IN_DISPUTE")

    p1 = db.get_user(p1_id)
    p2 = db.get_user(p2_id)
    p1_name = p1["username"] if p1 else str(p1_id)
    p2_name = p2["username"] if p2 else str(p2_id)

    # Notificar a ambos jugadores
    for uid in [p1_id, p2_id]:
        await bot.send_message(
            uid,
            DISPUTE_OPENED_PLAYER.format(match_id=match_id),
            parse_mode="Markdown"
        )

    # Notificar al admin con botones de resolución
    await bot.send_message(
        ADMIN_ID,
        DISPUTE_ADMIN_NOTIFY.format(
            match_id=match_id, p1=p1_name, p2=p2_name, amount=amount
        ),
        parse_mode="Markdown",
        reply_markup=kb_admin_dispute(match_id, p1_id, p2_id, p1_name, p2_name)
    )

    db.log_audit("DISPUTE_OPENED", match_id=match_id)
    logger.info(f"Disputa abierta: {match_id}")
