"""
Модуль с обработчиками рекламы
"""

import logging
from datetime import datetime, timedelta
from aiogram import types
from aiogram.dispatcher import FSMContext
from src.config.config import VALID_CONDITIONS
from src.database.database import add_advertisement
from src.keyboards.keyboards import get_main_menu
from src.handlers.states import AdForm

async def choose_ad_type(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа рекламы."""
    ad_type = callback_query.data.split('_')[1].upper()
    async with state.proxy() as data:
        data['ad_type'] = ad_type
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="open_menu"))
    
    await callback_query.message.edit_text(
        f"Введите данные ({ad_type}) в формате:\n"
        "ДД.ММ.ГГГГ, @юзер, время, условия, CPM/сумма",
        reply_markup=keyboard
    )
    await AdForm.waiting_for_data.set()

async def process_ad_data(message: types.Message, ad_type: str = None):
    """Обработка и валидация данных рекламы."""
    try:
        # Заменяем запятые без пробелов на запятые с пробелами
        text = message.text.replace(',', ', ')
        # Удаляем возможные двойные пробелы
        text = ' '.join(text.split())
        parts = text.split(', ')
        
        if len(parts) not in (5, 6):
            await message.reply("❌ Неверный формат! Используйте формат:\nДД.ММ.ГГГГ, @юзер, время, условия, CPM/сумма")
            return

        # Parse input data
        if len(parts) == 5:
            date, username, time, conditions, value = parts
            ad_type = 'CPM' if '.' in value else 'ФИКС'
        else:
            date, username, time, conditions, ad_type_input, value = parts
            ad_type = ad_type_input.upper()

        # Validate advertisement type
        if ad_type not in ['CPM', 'ФИКС']:
            await message.reply("❌ Ошибка в типе рекламы! Допустимые типы: CPM или ФИКС")
            return

        # Validate conditions
        if conditions.lower() not in [c.lower() for c in VALID_CONDITIONS]:
            await message.reply(f"❌ Неверные условия! Допустимые условия: {', '.join(VALID_CONDITIONS)}")
            return

        # Validate date format
        try:
            datetime.strptime(date, "%d.%m.%Y")
        except ValueError:
            await message.reply("❌ Неверный формат даты! Используйте формат ДД.ММ.ГГГГ")
            return

        # Process and save data
        ad_id = await add_advertisement(
            ad_type=ad_type,
            date=date,
            username=username,
            time=time,
            conditions=conditions,
            value=value,
            payment_status='Не оплачено' if ad_type == 'CPM' else 'Оплачено'
        )
        
        # Send confirmation message
        await message.reply(
            f"""
            ✅ Запись успешно сохранена!
            
            📅 Дата: {date}
            ⏰ Время: {time}
            👤 Пользователь: {username}
            📋 Условия: {conditions}
            📈 Тип рекламы: {ad_type}
            💰 Значение: {value}
            """,
            reply_markup=get_main_menu()
        )

    except ValueError as e:
        await message.reply(f"❌ Ошибка в данных: {str(e)}\nПроверьте правильность введенных значений.")
    except Exception as e:
        logging.error(f"Error processing ad data: {e}")
        await message.reply("❌ Произошла непредвиденная ошибка. Попробуйте позже или обратитесь в техподдержку.") 