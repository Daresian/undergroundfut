# handlers/group_events.py

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION

import utils.database as db
from config import GROUP_ID, TEST_USERS
from messages.texts import WELCOME_NEW_MEMBER

logger = logging.getLogger(__name__)
router = Router()


@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    """Cuando un usuario se une al grupo."""
    if event.chat.id != GROUP_ID:
        return

    uid      = event.new_chat_member.user.id
    username = event.new_chat_member.user.username or ""
    fullname = event.new_chat_member.user.full_name or ""
    name     = f"@{username}" if username else fullname

    # Registrar o actualizar usuario
    db.upsert_user(uid, username, fullname)

    # Si es usuario de prueba → reset total
    if uid in TEST_USERS:
        db.reset_user(uid)
        logger.info(f"Usuario de prueba {uid} reseteado al entrar al grupo.")

    # Enviar mensaje privado de bienvenida
    try:
        await bot.send_message(
            uid,
            WELCOME_NEW_MEMBER.format(name=name),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.warning(f"No se pudo enviar bienvenida privada a {uid}: {e}")


@router.chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def on_user_leave(event: ChatMemberUpdated, bot: Bot):
    """Cuando un usuario sale del grupo."""
    if event.chat.id != GROUP_ID:
        return

    uid = event.old_chat_member.user.id

    # Si es usuario de prueba → reset total
    if uid in TEST_USERS:
        db.reset_user(uid)
        logger.info(f"Usuario de prueba {uid} reseteado al salir del grupo.")
