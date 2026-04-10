from aiogram import Router, types, F
from database import validate_payment, add_credits, reset_users, get_user_by_tg_id
from config import ADMINS, GROUP_ID
from .results import current_matches

router = Router()

queues = {5: [], 10: [], 20: [], 50: [], 100: []}

def is_admin(uid):
    return uid in ADMINS

@router.message(F.text.startswith("/validar"))
async def validar(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    _, pid, stake, tg_id = message.text.split()
    pid, stake, tg_id = int(pid), int(stake), int(tg_id)

    validate_payment(pid)
    add_credits(tg_id, stake)

    await message.answer("Pago validado.")

    if tg_id not in queues[stake]:
        queues[stake].append(tg_id)

    await matchmaking(stake)

async def matchmaking(stake):
    from aiogram import Bot
    bot = Bot.get_current()

    while len(queues[stake]) >= 2:
        p1 = queues[stake].pop(0)
        p2 = queues[stake].pop(0)

        current_matches[p1] = {"stake": stake, "opponent": p2, "reported": None}
        current_matches[p2] = {"stake": stake, "opponent": p1, "reported": None}

        u1 = get_user_by_tg_id(p1)
        u2 = get_user_by_tg_id(p2)

        await bot.send_message(GROUP_ID,
            f"🎮 Match encontrado:\n@{u1['username']} vs @{u2['username']}\nStake: {stake}"
        )

@router.message(F.text == "/reset_users")
async def reset_all(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    reset_users()
    await message.answer("Usuarios reseteados.")
