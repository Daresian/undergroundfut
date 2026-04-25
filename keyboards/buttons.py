# keyboards/buttons.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import STAKES
from messages.texts import (
    ACCEPT_BUTTON, PLAY_BUTTON, PAID_BUTTON,
    VALIDATE_PAYMENT_BUTTON, REJECT_PAYMENT_BUTTON,
    WON_BUTTON, LOST_BUTTON
)


def kb_accept_rules() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=ACCEPT_BUTTON, callback_data="accept_rules")
    ]])


def kb_play() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=PLAY_BUTTON, callback_data="play")
    ]])


def kb_stakes() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=f"{s}€", callback_data=f"stake_{s}")
        for s in STAKES
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_paid() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=PAID_BUTTON, callback_data="i_paid")
    ]])


def kb_admin_validate(user_id: int, payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=VALIDATE_PAYMENT_BUTTON,
            callback_data=f"admin_pay_ok_{user_id}_{payment_id}"
        ),
        InlineKeyboardButton(
            text=REJECT_PAYMENT_BUTTON,
            callback_data=f"admin_pay_ko_{user_id}_{payment_id}"
        )
    ]])


def kb_report_result(match_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=WON_BUTTON,  callback_data=f"result_{match_id}_won")],
        [InlineKeyboardButton(text=LOST_BUTTON, callback_data=f"result_{match_id}_lost")],
    ])


def kb_admin_dispute(match_id: str, p1_id: int, p2_id: int,
                     p1_name: str, p2_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🏆 Gana @{p1_name}",
            callback_data=f"admin_verdict_{match_id}_{p1_id}"
        )],
        [InlineKeyboardButton(
            text=f"🏆 Gana @{p2_name}",
            callback_data=f"admin_verdict_{match_id}_{p2_id}"
        )],
        [InlineKeyboardButton(
            text="🔄 Anular partido (devolver stakes)",
            callback_data=f"admin_verdict_{match_id}_cancel"
        )],
    ])
