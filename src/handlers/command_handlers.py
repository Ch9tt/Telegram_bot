"""
Модуль с обработчиками команд
"""

import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from src.keyboards.keyboards import get_main_menu, get_settings_menu, get_ad_type_menu
from src.config.config import ADMIN_ID, BOT_USERNAME
from src.database.database import get_all_ads

async def send_welcome(message: types.Message):
    """Обработка команды /start."""
    welcome_text = (
        "🚀 Добро пожаловать в рекламный бот!\n\n"
        "Я помогу вам управлять рекламными объявлениями.\n"
        "Используйте меню ниже для навигации."
    )
    await message.reply(welcome_text, reply_markup=get_main_menu())

async def add_ad(message: types.Message):
    """Handle 'Add advertisement' button."""
    await message.answer(
        "Выберите тип рекламы:",
        reply_markup=get_ad_type_menu()
    )

async def view_db_command(message: types.Message):
    """Обработка команды просмотра базы данных."""
    try:
        ads = await get_all_ads()
        
        if not ads:
            await message.answer("База данных пуста.", reply_markup=get_main_menu())
            return

        message_text = ["📊 Все записи:"]
        for ad in ads:
            message_text.append(f"""
<b>#{ad['id']}</b>
Тип: {ad['ad_type']}
Дата: {ad['date']}
Время: {ad['time']}
Юзер: {ad['username']}
Условия: {ad['conditions']}
CPM: {ad['cpm'] or '—'}
Охват: {ad['reach'] or '—'}
Прибыль: {ad['profit'] or '—'}
Статус: {ad['payment_status']}
{'='*20}
""")
        
        await message.answer(
            '\n'.join(message_text),
            parse_mode='HTML',
            reply_markup=get_main_menu()
        )

    except Exception as e:
        logging.error(f"Ошибка при просмотре базы данных: {e}")
        await message.answer(
            "❌ Произошла ошибка при просмотре базы данных.",
            reply_markup=get_main_menu()
        )

async def show_help(message: types.Message):
    """Show help information."""
    help_text = """
    📚 Инструкция по использованию бота:

    1. Добавление рекламы:
       - Нажмите "Добавить рекламу"
       - Выберите тип (CPM или ФИКС)
       - Введите данные в формате:
         ДД.ММ.ГГГГ, @юзер, время, условия, CPM/сумма

    2. Допустимые условия:
       - 24ч, 48ч, 72ч
       - 3дня, неделя
       - бессрочно

    3. Просмотр базы данных:
       - Нажмите "Просмотреть БД"
       - Используйте фильтры для поиска

    4. Настройки:
       - Смена языка
       - Техническая поддержка
    """
    await message.answer(help_text, reply_markup=get_main_menu())

async def open_settings(message: types.Message):
    """Handle 'Settings' button."""
    await message.answer("Выберите настройку:", reply_markup=get_settings_menu())

async def back_to_main(message: types.Message):
    """Handle 'Back' button."""
    await message.answer("Главное меню:", reply_markup=get_main_menu())

async def admin_panel(message: types.Message):
    """Обработка нажатия кнопки админ-панели."""
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет доступа к этой функции.")
        return
    
    from src.keyboards.keyboards import get_admin_keyboard
    await message.answer(
        "🔧 Панель администратора:",
        reply_markup=get_admin_keyboard()
    )

async def handle_mention(message: types.Message):
    """Обработка упоминания бота."""
    clean_text = message.text.replace(f"@{BOT_USERNAME}", "").strip()
    if not clean_text:
        await message.reply("❌ Сообщение не содержит данных")
        return
    message.text = clean_text
    from src.handlers.ad_handlers import process_ad_data
    await process_ad_data(message) 