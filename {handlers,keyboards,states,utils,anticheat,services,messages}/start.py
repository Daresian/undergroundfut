# handlers/start.py

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

import utils.database as db
from config import ADMIN_ID, TEST_USERS
from states.states import UserStates
from keyboards.buttons import kb_accept_rules, kb_play, kb_stakes
from messages.texts import (
    WELCOME_PRIVATE, RULES_ES, RULES_EN,
    RULES_ACCEPTED, SELECT_STAKE, STATUS_MESSAGES,
    ALREADY_IN_FLOW, NOT_REGISTERED,
    COOLDOWN_ACTIVE, BANNED_PLAYER
)
from anticheat.monitor import check_user_can_play

logger = logging.getLogger(__name__)
router = Router()


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return

    uid = message.from_user.id
    db.upsert_user(uid, message.from_user.username, message.from_user.full_name)

    # Si es usuario de prueba → reset completo en cada /start
    if uid in TEST_USERS:
        db.reset_user(uid)
        logger.info(f"Usuario de prueba {uid} reseteado en /start")

    user = db.get_user(uid)

    # Si ya aceptó reglas, ir directo al botón PLAY
    if user and user["accepted_rules"] and uid not in TEST_USERS:
        await state.set_state(UserStates.idle)
        await message.answer(RULES_ACCEPTED, parse_mode="Markdown", reply_markup=kb_play())
        return

    # Primera vez: bienvenida + reglas completas ES + reglas completas EN + botón
    await message.answer(WELCOME_PRIVATE, parse_mode="Markdown")
    await message.answer(RULES_ES, parse_mode="Markdown")
    await message.answer(RULES_EN, parse_mode="Markdown")
    await message.answer(
        "─────────────────────────",
        reply_markup=kb_accept_rules()
    )
    await state.set_state(UserStates.reading_rules)


# ── Botón "Acepto / I Accept" ────────────────────────────────────────────────

@router.callback_query(F.data == "accept_rules")
async def cb_accept_rules(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    db.upsert_user(uid, callback.from_user.username, callback.from_user.full_name)
    db.accept_rules(uid)

    await callback.message.edit_reply_markup(reply_markup=None)
    # Enviar botón PLAY sin ningún mensaje de confirmación extra
    await callback.message.answer(
        RULES_ACCEPTED, parse_mode="Markdown", reply_markup=kb_play()
    )
    await state.set_state(UserStates.idle)
    await callback.answer()


# ── Botón PLAY ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "play")
async def cb_play(callback: CallbackQuery, state: FSMContext, bot: Bot):
    uid = callback.from_user.id
    user = db.get_user(uid)

    if not user or not user["accepted_rules"]:
        await callback.answer(NOT_REGISTERED, show_alert=True)
        return

    can_play, reason = check_user_can_play(uid)

    if not can_play:
        if reason == "banned":
            await callback.message.answer(BANNED_PLAYER, parse_mode="Markdown")
        elif reason.startswith("blocked:"):
            minutes = reason.split(":")[1]
            await callback.answer(
                f"🚫 Bloqueado. Tiempo restante: {minutes} min. / "
                f"Blocked. Time remaining: {minutes} min.",
                show_alert=True
            )
        elif reason.startswith("cooldown:"):
            minutes = reason.split(":")[1]
            await callback.message.answer(
                COOLDOWN_ACTIVE.format(minutes=minutes), parse_mode="Markdown"
            )
        elif reason == "busy":
            await callback.answer(ALREADY_IN_FLOW, show_alert=True)
        await callback.answer()
        return

    # Mostrar explicación breve + stakes
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "🎮 *¡Vamos a jugar!*\n\n"
        "El proceso es muy sencillo:\n"
        "1️⃣ Elige el importe que quieres apostar\n"
        "2️⃣ Realiza el pago por PayPal\n"
        "3️⃣ El admin confirma tu pago\n"
        "4️⃣ El bot te empareja con un rival\n"
        "5️⃣ Jugáis el partido y reportáis el resultado\n"
        "6️⃣ El ganador recibe el premio en máx. 12h\n\n"
        "🎮 *Let's play!*\n\n"
        "The process is simple:\n"
        "1️⃣ Choose the amount you want to bet\n"
        "2️⃣ Make the payment via PayPal\n"
        "3️⃣ The admin confirms your payment\n"
        "4️⃣ The bot matches you with an opponent\n"
        "5️⃣ Play the match and report the result\n"
        "6️⃣ The winner receives the prize within max. 12h",
        parse_mode="Markdown"
    )
    await callback.message.answer(
        SELECT_STAKE, parse_mode="Markdown", reply_markup=kb_stakes()
    )
    await state.set_state(UserStates.selecting_stake)
    await callback.answer()


# ── /estado ───────────────────────────────────────────────────────────────────

@router.message(Command("estado"))
async def cmd_estado(message: Message):
    if message.chat.type != "private":
        return
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user:
        await message.answer(NOT_REGISTERED)
        return
    msg = STATUS_MESSAGES.get(user["state"], STATUS_MESSAGES["IDLE"])
    await message.answer(msg)
