# services/scheduler.py

import time
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import utils.database as db
from config import ADMIN_ID, GROUP_ID, BLOQUEO_HORAS
from messages.texts import BLOCKED_PLAYER, GROUP_PENALTY

logger = logging.getLogger(__name__)


def start_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_payment_timeouts,  "interval", minutes=2,  args=[bot])
    scheduler.add_job(check_match_timeouts,    "interval", minutes=5,  args=[bot])
    scheduler.add_job(check_dispute_timeouts,  "interval", hours=1,    args=[bot])
    scheduler.add_job(unblock_expired_users,   "interval", minutes=15)
    scheduler.start()
    logger.info("Scheduler iniciado.")
    return scheduler


async def check_payment_timeouts(bot: Bot):
    """Expira pagos que llevan más de 15 min sin validar."""
    now = int(time.time())
    with db.get_conn() as conn:
        expired = conn.execute("""
            SELECT p.id, p.user_id, u.username FROM payments p
            JOIN users u ON p.user_id = u.telegram_id
            WHERE p.status = 'PENDING' AND p.expires_at < ?
        """, (now,)).fetchall()

    for p in expired:
        db.expire_payment(p["id"])
        db.set_state(p["user_id"], "IDLE")
        from keyboards.buttons import kb_play
        from messages.texts import PAYMENT_EXPIRED_PLAYER
        try:
            await bot.send_message(
                p["user_id"], PAYMENT_EXPIRED_PLAYER,
                parse_mode="Markdown", reply_markup=kb_play()
            )
        except Exception as e:
            logger.error(f"Error notificando pago expirado a {p['user_id']}: {e}")


async def check_match_timeouts(bot: Bot):
    """AC04: Bloquea a jugadores que no reportaron resultado a tiempo."""
    now = int(time.time())
    with db.get_conn() as conn:
        expired = conn.execute("""
            SELECT * FROM matches
            WHERE status = 'IN_PROGRESS' AND report_deadline < ?
        """, (now,)).fetchall()

    for match in expired:
        match_id = match["match_id"]
        with db.get_conn() as conn:
            reports = conn.execute(
                "SELECT user_id FROM result_reports WHERE match_id=?",
                (match_id,)
            ).fetchall()
        reported_ids = [r["user_id"] for r in reports]

        for uid in [match["player1_id"], match["player2_id"]]:
            if uid not in reported_ids:
                user = db.get_user(uid)
                username = user["username"] if user else str(uid)
                db.log_anticheat(uid, "AC04", f"No reportó en {match_id}")
                db.set_blocked(uid, BLOQUEO_HORAS)
                try:
                    await bot.send_message(
                        uid, BLOCKED_PLAYER.format(hours=BLOQUEO_HORAS),
                        parse_mode="Markdown"
                    )
                    await bot.send_message(
                        ADMIN_ID,
                        f"🚨 *ANTITRAMPA AC04*\n\n"
                        f"@{username} (`{uid}`) no reportó resultado del partido `{match_id}`.\n"
                        f"Bloqueado {BLOQUEO_HORAS} horas.",
                        parse_mode="Markdown"
                    )
                    await bot.send_message(GROUP_ID, GROUP_PENALTY)
                except Exception as e:
                    logger.error(f"Error en timeout match {match_id}: {e}")

        with db.get_conn() as conn:
            conn.execute(
                "UPDATE matches SET status='EXPIRED' WHERE match_id=?", (match_id,)
            )


async def check_dispute_timeouts(bot: Bot):
    """Avisa al admin cuando una disputa lleva más de 48h sin resolverse."""
    now = int(time.time())
    with db.get_conn() as conn:
        overdue = conn.execute("""
            SELECT d.match_id, d.deadline FROM disputes d
            WHERE d.status = 'OPEN' AND d.deadline < ?
        """, (now,)).fetchall()

    for d in overdue:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔴 *DISPUTA CADUCADA*\n\n"
                f"Partido: `{d['match_id']}`\n"
                f"Han pasado más de 48h sin resolución.\n"
                f"Usa /disputas para gestionarla.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error avisando disputa caducada {d['match_id']}: {e}")


async def unblock_expired_users():
    """Desbloquea automáticamente a usuarios cuyo bloqueo temporal venció."""
    now = int(time.time())
    with db.get_conn() as conn:
        conn.execute("""
            UPDATE users SET state='IDLE', blocked_until=0
            WHERE state='BLOCKED' AND blocked_until > 0 AND blocked_until <= ?
        """, (now,))
