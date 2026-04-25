# handlers/admin.py

import time
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import utils.database as db

MARGIN = 0.15  # Comisión del 15% sobre el bote total
from config import ADMIN_ID, GROUP_ID, COOLDOWN_MINUTOS
from keyboards.buttons import kb_play, kb_admin_dispute
from messages.texts import (
    DISPUTE_VERDICT_WINNER, DISPUTE_VERDICT_LOSER,
    DISPUTE_CANCELLED_PLAYER, ADMIN_PAY_WINNER,
    GROUP_WINNER, BANNED_PLAYER
)

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ── /disputas ─────────────────────────────────────────────────────────────────

@router.message(Command("disputas"))
async def cmd_disputas(message: Message):
    if not is_admin(message.from_user.id):
        return

    disputes = db.get_open_disputes()
    if not disputes:
        await message.answer("✅ No hay disputas pendientes.")
        return

    now = int(time.time())
    for d in disputes:
        hours_left = max(0, int((d["deadline"] - now) / 3600))
        await message.answer(
            f"⚠️ *DISPUTA PENDIENTE*\n\n"
            f"Partido: `{d['match_id']}`\n"
            f"@{d['p1_name']} vs @{d['p2_name']}\n"
            f"Stake: *{d['amount']}€*\n"
            f"Tiempo restante: *{hours_left}h*",
            parse_mode="Markdown",
            reply_markup=kb_admin_dispute(
                d["match_id"],
                d["player1_id"], d["player2_id"],
                d["p1_name"], d["p2_name"]
            )
        )


# ── Veredicto de disputa ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_verdict_"))
async def cb_admin_verdict(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("No tienes permiso. / No permission.", show_alert=True)
        return

    parts = callback.data.split("_")
    # admin_verdict_{match_id}_{winner_id_or_cancel}
    match_id = parts[2]
    action   = parts[3]

    match = db.get_match(match_id)
    if not match:
        await callback.answer("Partido no encontrado.", show_alert=True)
        return

    p1_id   = match["player1_id"]
    p2_id   = match["player2_id"]
    amount  = match["amount"]
    prize   = amount * 2
    p1      = db.get_user(p1_id)
    p2      = db.get_user(p2_id)
    p1_name = p1["username"] if p1 else str(p1_id)
    p2_name = p2["username"] if p2 else str(p2_id)

    if action == "cancel":
        # Anular partido → devolver stakes a ambos
        db.close_match(match_id, winner_id=0, status="CANCELLED")
        db.close_dispute(match_id, verdict_user_id=0)
        db.set_state(p1_id, "IDLE")
        db.set_state(p2_id, "IDLE")
        db.set_cooldown(p1_id, COOLDOWN_MINUTOS)
        db.set_cooldown(p2_id, COOLDOWN_MINUTOS)

        for uid, name in [(p1_id, p1_name), (p2_id, p2_name)]:
            await bot.send_message(
                uid,
                DISPUTE_CANCELLED_PLAYER.format(match_id=match_id, amount=amount),
                parse_mode="Markdown", reply_markup=kb_play()
            )

        await bot.send_message(
            ADMIN_ID,
            f"🔄 *PARTIDO ANULADO*\n\n"
            f"Debes devolver *{amount}€* a @{p1_name} y *{amount}€* a @{p2_name}.",
            parse_mode="Markdown"
        )
        db.log_audit("DISPUTE_CANCELLED", match_id=match_id)

    else:
        # Hay un ganador
        winner_id = int(action)
        loser_id  = p2_id if winner_id == p1_id else p1_id
        winner    = db.get_user(winner_id)
        winner_name = winner["username"] if winner else str(winner_id)

        db.close_match(match_id, winner_id=winner_id, status="COMPLETED")
        db.close_dispute(match_id, verdict_user_id=winner_id)
        db.set_state(winner_id, "IDLE")
        db.set_state(loser_id,  "IDLE")
        db.set_cooldown(winner_id, COOLDOWN_MINUTOS)
        db.set_cooldown(loser_id,  COOLDOWN_MINUTOS)

        await bot.send_message(
            winner_id,
            DISPUTE_VERDICT_WINNER.format(match_id=match_id, prize=prize),
            parse_mode="Markdown", reply_markup=kb_play()
        )
        await bot.send_message(
            loser_id,
            DISPUTE_VERDICT_LOSER.format(match_id=match_id),
            parse_mode="Markdown", reply_markup=kb_play()
        )
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
        await bot.send_message(
            GROUP_ID,
            GROUP_WINNER.format(username=winner_name, amount=prize),
            parse_mode="Markdown"
        )
        db.log_audit("DISPUTE_RESOLVED", winner_id, match_id, f"Prize: {prize}€")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ Resuelto.")


# ── /bloquear @usuario horas ──────────────────────────────────────────────────

@router.message(Command("bloquear"))
async def cmd_bloquear(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Uso: /bloquear @usuario <horas>")
        return
    username = args[1].lstrip("@")
    hours = int(args[2])
    with db.get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
    if not user:
        await message.answer(f"@{username} no encontrado.")
        return
    db.set_blocked(user["telegram_id"], hours)
    db.log_audit("ADMIN_BLOCK", user["telegram_id"], detail=f"{hours}h")
    await message.answer(f"🚫 @{username} bloqueado {hours}h.")
    await bot.send_message(
        user["telegram_id"],
        f"🚫 Tu cuenta ha sido bloqueada temporalmente.\n"
        f"Duración: *{hours} horas*.\n\n"
        f"Your account has been temporarily blocked.\n"
        f"Duration: *{hours} hours*.",
        parse_mode="Markdown"
    )
    await bot.send_message(
        GROUP_ID,
        "⚠️ Un usuario ha sido bloqueado temporalmente por incumplir las normas.\n\n"
        "A user has been temporarily blocked for violating the rules."
    )


# ── /desbloquear @usuario ─────────────────────────────────────────────────────

@router.message(Command("desbloquear"))
async def cmd_desbloquear(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Uso: /desbloquear @usuario")
        return
    username = args[1].lstrip("@")
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE users SET state='IDLE', blocked_until=0 WHERE username=?",
            (username,)
        )
    db.log_audit("ADMIN_UNBLOCK", detail=username)
    await message.answer(f"✅ @{username} desbloqueado.")
    with db.get_conn() as conn:
        user = conn.execute(
            "SELECT telegram_id FROM users WHERE username=?", (username,)
        ).fetchone()
    if user:
        await bot.send_message(
            user["telegram_id"],
            "✅ Tu bloqueo ha sido levantado. Puedes volver a jugar.\n\n"
            "Your block has been lifted. You can play again.",
        )


# ── /banear @usuario ──────────────────────────────────────────────────────────

@router.message(Command("banear"))
async def cmd_banear(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Uso: /banear @usuario")
        return
    username = args[1].lstrip("@")
    with db.get_conn() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
    if not user:
        await message.answer(f"@{username} no encontrado.")
        return
    with db.get_conn() as conn:
        conn.execute(
            "UPDATE users SET state='BANNED' WHERE username=?", (username,)
        )
    db.log_audit("ADMIN_BAN", user["telegram_id"])
    await message.answer(f"⛔ @{username} baneado permanentemente.")
    await bot.send_message(
        user["telegram_id"], BANNED_PLAYER, parse_mode="Markdown"
    )
    await bot.send_message(
        GROUP_ID,
        "⚠️ Un usuario ha sido expulsado permanentemente de la comunidad.\n\n"
        "A user has been permanently expelled from the community."
    )


# ── /stats ────────────────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    with db.get_conn() as conn:
        users    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        matches  = conn.execute("SELECT COUNT(*) FROM matches WHERE status='COMPLETED'").fetchone()[0]
        disputes = conn.execute("SELECT COUNT(*) FROM disputes WHERE status='OPEN'").fetchone()[0]
        queue    = conn.execute("SELECT COUNT(*) FROM queue").fetchone()[0]
    await message.answer(
        f"📊 *ESTADÍSTICAS*\n\n"
        f"👥 Usuarios: {users}\n"
        f"⚽ Partidos completados: {matches}\n"
        f"⏳ En cola ahora: {queue}\n"
        f"⚠️ Disputas abiertas: {disputes}",
        parse_mode="Markdown"
    )
