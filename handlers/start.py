from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_or_create_user, set_rules_accepted, user_has_accepted_rules
from rules import RULES_ES_PARTS, RULES_EN_PARTS

router = Router()

@router.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    for member in message.new_chat_members:
        if not member.is_bot:
            await send_rules(member.id, member.full_name)

async def send_rules(user_id, full_name):
    from aiogram import Bot
    bot = Bot.get_current()

    await bot.send_message(user_id,
        f"Bienvenido/a {full_name} 👑\nWelcome {full_name} 👑\n\n"
        "Debes aceptar las reglas para jugar.\nYou must accept the rules to play."
    )

    for part in RULES_ES_PARTS:
        await bot.send_message(user_id, part)

    for part in RULES_EN_PARTS:
        await bot.send_message(user_id, part)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Acepto / I Accept", callback_data="accept")],
        [InlineKeyboardButton(text="❌ No acepto / I Decline", callback_data="decline")]
    ])

    await bot.send_message(user_id, "Aceptas las reglas?", reply_markup=kb)

@router.callback_query(F.data == "accept")
async def accept_rules(callback: types.CallbackQuery):
    set_rules_accepted(callback.from_user.id)
    await callback.message.answer("Perfecto. Escribe PLAY para comenzar.")
    await callback.answer()

@router.callback_query(F.data == "decline")
async def decline_rules(callback: types.CallbackQuery):
    await callback.message.answer("No puedes jugar sin aceptar las reglas.")
    await callback.answer()
