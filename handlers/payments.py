# handlers/payments.py

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import utils.database as db
from config import ADMIN_ID, GROUP_ID, TIMEOUT_PAGO_MINUTOS, PAYPAL_ADDRESS
from states.states import UserStates
from keyboards.buttons import kb_paid, kb_admin_validate, kb_play
from messages.texts import (
    PAYMENT_INSTRUCTIONS, PAYMENT_PENDING_ADMIN,
    PAYMENT_VALIDATED_PLAYER, PAYMENT_REJECTED_PLAYER,
    GROUP_WAITING
)
from anticheat.monitor import trigger as ac_trigger, check_user_can_play
from services.matchmaking import try_match

logger = logging.getLogger(__name__)
router = Router()


# ── Selección de stake ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("stake_"))
async def cb_stake_selected(callback: CallbackQuery, state: FSMContext, bot: Bot):
    uid = callback.from_user.id
    user = db.get_user(uid)

    # Validar que viene del flujo correcto
    if not user or not user["accepted_rules"]:
        await ac_trigger(bot, uid, "AC01")
        await callback.answer()
        return

    can_play, reason = check_user_can_play(uid)
    if not can_play:
        await callback.answer("No puedes iniciar una partida ahora. / You cannot start a match now.", show_alert=True)
        return

    # Extraer stake y validar que es un valor permitido
    try:
        from config import STAKES
        amount = int(callback.data.split("_")[1])
        if amount not in STAKES:
            raise ValueError
    except (ValueError, IndexError):
        await ac_trigger(bot, uid, "AC11", f"Stake inválido: {callback.data}")
        await callback.answer()
        return

    # Crear pago pendiente
    payment_id = db.create_payment(uid, amount, TIMEOUT_PAGO_MINUTOS)
    db.set_state(uid, "WAITING_PAYMENT")

    username = user["username"] or str(uid)

    # Instrucciones al jugador
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        PAYMENT_INSTRUCTIONS.format(amount=amount, paypal=PAYPAL_ADDRESS),
        parse_mode="Markdown",
        reply_markup=kb_paid()
    )

    # Notificación al admin
    await bot.send_message(
        ADMIN_ID,
        PAYMENT_PENDING_ADMIN.format(
            username=username, user_id=uid,
            amount=amount, payment_id=payment_id
        ),
        parse_mode="Markdown",
        reply_markup=kb_admin_validate(uid, payment_id)
    )

    await state.set_state(UserStates.waiting_payment)
    await callback.answer()


# ── "He pagado" (botón del jugador) ──────────────────────────────────────────

@router.callback_query(F.data == "i_paid")
async def cb_i_paid(callback: CallbackQuery, bot: Bot):
    uid = callback.from_user.id
    user = db.get_user(uid)

    # Si no tiene pago pendiente, ignorar silenciosamente
    if not user or user["state"] != "WAITING_PAYMENT":
        await callback.answer(
            "⏳ Tu solicitud ya está siendo procesada. El admin la revisará en breve.\n\n"
            "⏳ Your request is already being processed. The admin will review it shortly.",
            show_alert=True
        )
        return

    # Solo confirmar recepción — el admin es quien valida
    await callback.answer(
        "✅ Recibido. El admin validará tu pago en breve.\n\n"
        "✅ Received. The admin will validate your payment shortly.",
        show_alert=True
    )


# ── Admin valida el pago ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_pay_ok_"))
async def cb_admin_pay_ok(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await ac_trigger(bot, callback.from_user.id, "AC12", "Intentó validar pago sin ser admin")
        await callback.answer()
        return

    parts = callback.data.split("_")
    # admin_pay_ok_{user_id}_{payment_id}
    player_id  = int(parts[3])
    payment_id = int(parts[4])

    import time
    payment = db.get_payment(payment_id)
    if not payment or payment["status"] != "PENDING":
        await callback.answer("Este pago ya fue procesado.", show_alert=True)
        return

    now = int(time.time())
    if payment["expires_at"] < now:
        db.expire_payment(payment_id)
        db.set_state(player_id, "IDLE")
        await bot.send_message(
            player_id, PAYMENT_INSTRUCTIONS.replace("{amount}", "—") + "\n\n⏰ Pago expirado.",
        )
        from messages.texts import PAYMENT_EXPIRED_PLAYER
        await bot.send_message(player_id, PAYMENT_EXPIRED_PLAYER,
                               parse_mode="Markdown", reply_markup=kb_play())
        await callback.answer("El pago ya expiró.", show_alert=True)
        return

    amount = payment["amount"]
    db.validate_payment(payment_id)
    db.set_state(player_id, "IN_QUEUE")
    db.add_to_queue(player_id, amount)

    user = db.get_user(player_id)
    username = user["username"] if user else str(player_id)

    db.log_audit("PAYMENT_VALIDATED", player_id, detail=f"{amount}€")

    # Notificar al jugador
    await bot.send_message(
        player_id,
        PAYMENT_VALIDATED_PLAYER.format(amount=amount),
        parse_mode="Markdown"
    )

    # Mensaje público al grupo
    group_msg = await bot.send_message(
        GROUP_ID,
        GROUP_WAITING.format(username=username, amount=amount),
        parse_mode="Markdown"
    )
    db.set_queue_msg(player_id, group_msg.message_id)

    # Confirmación al admin
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ Pago de @{username} ({amount}€) validado. Jugador en cola.")
    await callback.answer()

    # Intentar hacer match
    await try_match(bot, player_id, amount)


# ── Admin rechaza el pago ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_pay_ko_"))
async def cb_admin_pay_ko(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await ac_trigger(bot, callback.from_user.id, "AC12", "Intentó rechazar pago sin ser admin")
        await callback.answer()
        return

    parts = callback.data.split("_")
    player_id  = int(parts[3])
    payment_id = int(parts[4])

    db.expire_payment(payment_id)
    db.set_state(player_id, "IDLE")
    db.log_audit("PAYMENT_REJECTED", player_id)

    await bot.send_message(
        player_id, PAYMENT_REJECTED_PLAYER,
        parse_mode="Markdown", reply_markup=kb_play()
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"❌ Pago de {player_id} rechazado.")
    await callback.answer()
