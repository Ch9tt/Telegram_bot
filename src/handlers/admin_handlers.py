"""
Модуль с обработчиками админ-панели
"""

import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from src.config.config import ADMIN_ID, VALID_CONDITIONS
from src.database.database import get_all_ads, get_ad_by_id, update_ad_field, delete_ad
from src.handlers.states import EditAdForm
from src.keyboards.keyboards import get_admin_keyboard

async def handle_admin_menu(callback_query: types.CallbackQuery):
    """Handle admin menu access."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return
    
    await callback_query.message.edit_text(
        "🔧 Панель администратора:",
        reply_markup=get_admin_keyboard()
    )

async def edit_ads(callback_query: types.CallbackQuery):
    """Handle advertisement editing."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    try:
        ads = await get_all_ads()
        if not ads:
            await callback_query.message.edit_text("База данных пуста.")
            return

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for ad in ads:
            keyboard.add(types.InlineKeyboardButton(
                f"ID: {ad['id']} | {ad['ad_type']} | {ad['username']}",
                callback_data=f"edit_{ad['id']}"
            ))
        keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin"))

        await callback_query.message.edit_text(
            "Выберите запись для редактирования:",
            reply_markup=keyboard
        )

    except Exception as e:
        logging.error(f"Error in edit_ads: {e}")
        await callback_query.message.edit_text("❌ Произошла ошибка при загрузке записей.")

async def edit_ad(callback_query: types.CallbackQuery):
    """Handle individual advertisement editing."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    ad_id = int(callback_query.data.split('_')[1])
    try:
        ad = await get_ad_by_id(ad_id)
        if not ad:
            await callback_query.answer("Запись не найдена.", show_alert=True)
            return

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("Изменить тип", callback_data=f"edit_type_{ad_id}"),
            types.InlineKeyboardButton("Изменить дату", callback_data=f"edit_date_{ad_id}"),
            types.InlineKeyboardButton("Изменить юзер", callback_data=f"edit_username_{ad_id}"),
            types.InlineKeyboardButton("Изменить время", callback_data=f"edit_time_{ad_id}"),
            types.InlineKeyboardButton("Изменить условия", callback_data=f"edit_conditions_{ad_id}"),
            types.InlineKeyboardButton("Изменить CPM/прибыль", callback_data=f"edit_value_{ad_id}"),
            types.InlineKeyboardButton("Изменить статус", callback_data=f"status_{ad_id}"),
            types.InlineKeyboardButton("Удалить", callback_data=f"delete_{ad_id}"),
            types.InlineKeyboardButton("⬅️ Назад", callback_data="edit_ads")
        )

        response = (
            f"📝 Редактирование записи ID: {ad_id}\n\n"
            f"Тип: {ad['ad_type']}\n"
            f"Дата: {ad['date']}\n"
            f"Пользователь: {ad['username']}\n"
            f"Время: {ad['time']}\n"
            f"Условия: {ad['conditions']}\n"
        )
        if ad['ad_type'] == 'CPM':
            response += f"CPM: {ad['cpm']}\n"
        else:
            response += f"Прибыль: {ad['profit']}\n"
        response += f"Статус: {ad['payment_status']}"

        await callback_query.message.edit_text(response, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in edit_ad: {e}")
        await callback_query.message.edit_text("❌ Произошла ошибка при загрузке записи.")

async def change_status(callback_query: types.CallbackQuery):
    """Handle advertisement status change."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    ad_id = int(callback_query.data.split('_')[1])
    try:
        ad = await get_ad_by_id(ad_id)
        new_status = "Не оплачено" if ad['payment_status'] == "Оплачено" else "Оплачено"
        await update_ad_field(ad_id, 'payment_status', new_status)
        await callback_query.answer("Статус успешно изменен!")
        await edit_ad(callback_query)

    except Exception as e:
        logging.error(f"Error in change_status: {e}")
        await callback_query.answer("❌ Произошла ошибка при изменении статуса.", show_alert=True)

async def delete_ad(callback_query: types.CallbackQuery):
    """Handle advertisement deletion."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    ad_id = int(callback_query.data.split('_')[1])
    try:
        await delete_ad(ad_id)
        await callback_query.answer("Запись успешно удалена!")
        await edit_ads(callback_query)

    except Exception as e:
        logging.error(f"Error in delete_ad: {e}")
        await callback_query.answer("❌ Произошла ошибка при удалении записи.", show_alert=True) 