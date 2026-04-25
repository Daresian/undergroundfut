# states/states.py

from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    reading_rules       = State()
    idle                = State()
    selecting_stake     = State()
    waiting_payment     = State()
    in_queue            = State()
    in_match            = State()
    reporting_result    = State()
    in_dispute          = State()
