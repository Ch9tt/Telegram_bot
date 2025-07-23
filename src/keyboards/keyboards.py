"""
Модуль с клавиатурами для бота
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    """Создание главного меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton("Добавить рекламу"),
                KeyboardButton("Просмотреть БД")
            ],
            [
                KeyboardButton("Помощь"),
                KeyboardButton("Настройки")
            ],
            [
                KeyboardButton("🔧 Админ-панель")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Главное меню"
    )

def get_settings_menu():
    """Создание меню настроек."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton("Сменить язык"),
                KeyboardButton("Техподдержка")
            ],
            [
                KeyboardButton("⬅️ Назад")
            ]
        ],
        resize_keyboard=True
    )

def get_ad_type_menu():
    """Создание меню выбора типа рекламы."""
    menu = InlineKeyboardMarkup(row_width=2)
    menu.add(
        InlineKeyboardButton("CPM", callback_data="type_cpm"),
        InlineKeyboardButton("ФИКС", callback_data="type_fixed"),
        InlineKeyboardButton("⬅️ Назад", callback_data="open_menu")
    )
    return menu

def get_language_menu():
    """Создание меню выбора языка."""
    menu = InlineKeyboardMarkup(row_width=2)
    menu.add(
        InlineKeyboardButton("Русский", callback_data="lang_ru"),
        InlineKeyboardButton("English", callback_data="lang_en"),
        InlineKeyboardButton("⬅️ Назад", callback_data="open_menu")
    )
    return menu

def get_admin_keyboard():
    """Create admin control keyboard."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Редактировать записи", callback_data="edit_ads"),
        InlineKeyboardButton("Удалить записи", callback_data="delete_ads"),
        InlineKeyboardButton("Статистика", callback_data="stats"),
        InlineKeyboardButton("⬅️ Назад", callback_data="open_menu")
    )
    return keyboard 