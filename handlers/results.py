from aiogram import Router, types, F
from database import add_credits, remove_credits, get_user_by_tg_id
from config import GROUP_ID

router = Router()

current_matches = {}

@router.message(F.chat.type == "private", F.text == "/gane")
async def gane(message: types.Message):
    uid = message.from_user.id
    if uid not in current_matches:
        await message.answer("No tienes partido activo.")
        return

    current_matches[uid]["reported"] = "win"
    await resolve(uid, message)

@router.message(F.chat.type == "private", F.text == "/perdi")
async def perdi(message: types.Message):
    uid = message.from_user.id
    if uid not in current_matches:
        await message.answer("No tienes partido activo.")
        return

    current_matches[uid]["reported"] = "lose"
    await resolve(uid, message)

async def resolve(uid, message):
    match = current_matches[uid]
    opp = match["opponent"]
    stake = match["stake"]

    if opp not in current_matches:
        await message.answer("Esperando al rival.")
        return

    my = current_matches[uid]["reported"]
    their = current_matches[opp]["reported"]

    if not my or not their:
        await message.answer("Esperando al rival.")
        return

    from aiogram import Bot
    bot = Bot.get_current()

    if my == "win" and their == "lose":
        winner, loser = uid, opp
    elif my == "lose" and their == "win":
        winner, loser = opp, uid
    else:
        await bot.send_message(GROUP_ID, "⚠️ Conflicto en resultado.")
        return

    prize = int(stake * 0.7)
    add_credits(winner, prize)
    remove_credits(loser, stake)

    wu = get_user_by_tg_id(winner)
    lu = get_user_by_tg_id(loser)

    await bot.send_message(GROUP_ID,
        f"🏆 Ganador: @{wu['username']}\n"
        f"❌ Perdedor: @{lu['username']}\n"
        f"Stake: {stake}\n"
        f"Premio: {prize}"
    )

    del current_matches[uid]
    del current_matches[opp]

    await message.answer("Resultado registrado.")
