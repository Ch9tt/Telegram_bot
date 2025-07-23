"""
Модуль с состояниями для FSM (Finite State Machine)
"""

from aiogram.dispatcher.filters.state import State, StatesGroup

class AdForm(StatesGroup):
    """Состояния для формы рекламы."""
    waiting_for_data = State()

class EditAdForm(StatesGroup):
    """Состояния для редактирования рекламы."""
    waiting_for_field = State()
    waiting_for_date = State()
    waiting_for_username = State()
    waiting_for_time = State()
    waiting_for_conditions = State()
    waiting_for_cpm = State()
    waiting_for_profit = State()
    waiting_for_type = State() 