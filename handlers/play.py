from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    user_has_accepted_rules,
    create_payment,
    get_pending_payment_by_user
)
from config import PAYPAL_LINK, ADMINS

router = Router()

STAKE_OPTIONS = [5, 10, 20, 50, 100]

@router.message(F.chat.type == "private", F.text.upper() == "PLAY")
async def play(message: types.Message):
    if not user_has_accepted_rules(message.from_user.id):
        await message.answer("Debes aceptar las reglas primero.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"PLAY {s}", callback_data=f"stake:{s}")]
        for s in STAKE_OPTIONS
    ])

    await message.answer("Elige importe:", reply_markup=kb)

@router.callback_query(F.data.startswith("stake:"))
async def choose_stake(callback: types.CallbackQuery):
    stake = int(callback.data.split(":")[1])
    create_payment(callback.from_user.id, stake)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="He pagado / I have paid", callback_data=f"paid:{stake}")]
    ])

    await callback.message.answer(
        f"Ingresa {stake}€ en PayPal:\n{PAYPAL_LINK}\n\n"
        "Cuando pagues, pulsa el botón.",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("paid:"))
async def paid(callback: types.CallbackQuery):
    stake = int(callback.data.split(":")[1])
    payment = get_pending_payment_by_user(callback.from_user.id)

    if not payment:
        await callback.message.answer("No hay pago pendiente.")
        return

    from aiogram import Bot
    bot = Bot.get_current()

    for admin in ADMINS:
        await bot.send_message(admin,
            f"⚠️ @{callback.from_user.username} afirma haber pagado {stake}€.\n"
            f"ID de pago: {payment['id']}"
        )

    await callback.message.answer("Pago enviado a validación.")
    await callback.answer()
