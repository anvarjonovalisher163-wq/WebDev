from aiogram.fsm.state import State, StatesGroup


class CertificateStates(StatesGroup):
    waiting_full_name = State()
