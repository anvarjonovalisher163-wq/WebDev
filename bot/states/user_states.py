from aiogram.fsm.state import State, StatesGroup


class CertificateStates(StatesGroup):
    waiting_full_name = State()  # kanalga qo'shilgach avtomatik so'raladigan eski oqim
    waiting_first_name = State()  # admin "sertifikat ro'yxati" xabari orqali so'ralganda
    waiting_last_name = State()
