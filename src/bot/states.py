# bot/states.py
from aiogram.fsm.state import State, StatesGroup

class CreateCategory(StatesGroup):
    waiting_name = State()

class AddContact(StatesGroup):
    waiting_display_name = State()
    waiting_contact_value = State()
    # category_id мы будем хранить как data в FSMContext
