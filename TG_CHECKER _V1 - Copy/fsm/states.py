from aiogram.fsm.state import StatesGroup, State

class SessionStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()
    waiting_for_numbers = State()
    waiting_for_plus_numbers = State()

    # ⏳ Timeout/Idle markers
    timeout_phone = State()
    timeout_code = State()
    timeout_password = State()
    timeout_number_input = State()
