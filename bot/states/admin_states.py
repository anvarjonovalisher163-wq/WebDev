from aiogram.fsm.state import State, StatesGroup


class WelcomeStates(StatesGroup):
    waiting_text = State()
    waiting_media = State()


class ChannelStates(StatesGroup):
    waiting_identifier = State()
    waiting_gate_text = State()


class ReferralContentStates(StatesGroup):
    waiting_text = State()
    waiting_image = State()
    waiting_share_text = State()


class RequirementsStates(StatesGroup):
    waiting_count = State()


class SecretChannelStates(StatesGroup):
    waiting_identifier = State()
    waiting_ttl = State()
    waiting_member_limit = State()
    waiting_max_reissue = State()


class BroadcastStates(StatesGroup):
    waiting_content = State()
    waiting_confirmation = State()


class SearchStates(StatesGroup):
    waiting_query = State()
    waiting_message_text = State()


class AdminManageStates(StatesGroup):
    waiting_new_admin_id = State()
