"""
Телеграм бот для управления рекламой
Этот бот помогает управлять и отслеживать рекламные объявления с разными моделями ценообразования (CPM и Фиксированная).
Возможности:
- Добавление и управление рекламными объявлениями
- Просмотр базы данных рекламы
- Административные функции управления
- Автоматическое планирование постов
- Поддержка нескольких языков (RU/EN)
"""

import logging
import atexit
import os
import sys
import signal
import asyncio
import psutil
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

# === Константы и конфигурация ===
LOCK_FILE = "bot.lock"
API_TOKEN = ''
BOT_USERNAME = ''
ADMIN_ID =''

# Допустимые условия рекламы
VALID_CONDITIONS = {'24ч', '48ч', '72ч', '3дня', 'неделя', 'бессрочно'}

# === Управление блокировкой процесса ===
def is_process_running(pid):
    """Проверка, запущен ли процесс с указанным PID."""
    try:
        return psutil.Process(pid).is_running()
    except psutil.NoSuchProcess:
        return False

def setup_process_lock():
    """Настройка блокировки процесса для предотвращения запуска нескольких экземпляров бота."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            if is_process_running(old_pid):
                print("Бот уже запущен! Пожалуйста, закройте предыдущий экземпляр.")
                sys.exit()
            else:
                os.remove(LOCK_FILE)
        except Exception as e:
            print(f"Ошибка при проверке файла блокировки: {e}")
            os.remove(LOCK_FILE)

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def cleanup():
    """Функция очистки для удаления файла блокировки при выходе."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

# === Bot Initialization ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
scheduler = AsyncIOScheduler()

# === Keyboard Layouts ===
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

# === Database Management ===
async def init_db():
    """Инициализация базы данных с необходимыми таблицами."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            await db.execute('''
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_type TEXT NOT NULL,
                date TEXT NOT NULL,
                username TEXT NOT NULL,
                time TEXT NOT NULL,
                conditions TEXT NOT NULL,
                cpm REAL,
                reach INTEGER,
                profit REAL,
                payment_status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка инициализации базы данных: {e}")
        raise

# === State Management ===
class AdForm(StatesGroup):
    """Состояния для формы рекламы."""
    waiting_for_data = State()

# === Message Handlers ===
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """Обработка команды /start."""
    welcome_text = (
        "🚀 Добро пожаловать в рекламный бот!\n\n"
        "Я помогу вам управлять рекламными объявлениями.\n"
        "Используйте меню ниже для навигации."
    )
    await message.reply(welcome_text, reply_markup=get_main_menu())

@dp.message_handler(lambda m: m.text == "Добавить рекламу")
async def add_ad(message: types.Message):
    """Handle 'Add advertisement' button."""
    await message.answer(
        "Выберите тип рекламы:",
        reply_markup=get_ad_type_menu()
    )

@dp.message_handler(lambda m: m.text == "Просмотреть БД")
async def view_db_command(message: types.Message):
    """Обработка команды просмотра базы данных."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            async with db.execute('SELECT * FROM ads') as cursor:
                ads = await cursor.fetchall()
        
        if not ads:
            await message.answer("База данных пуста.", reply_markup=get_main_menu())
            return

        message_text = ["📊 Все записи:"]
        for ad in ads:
            message_text.append(f"""
<b>#{ad[0]}</b>
Тип: {ad[1]}
Дата: {ad[2]}
Время: {ad[4]}
Юзер: {ad[3]}
Условия: {ad[5]}
CPM: {ad[6] or '—'}
Охват: {ad[7] or '—'}
Прибыль: {ad[8] or '—'}
Статус: {ad[9]}
{'='*20}
""")
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="open_menu"))
        
        await message.answer(
            '\n'.join(message_text),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

    except Exception as e:
        logging.error(f"Ошибка при просмотре базы данных: {e}")
        await message.answer(
            "❌ Произошла ошибка при просмотре базы данных.",
            reply_markup=get_main_menu()
        )

@dp.message_handler(lambda m: m.text == "Помощь")
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

@dp.message_handler(lambda m: m.text == "Настройки")
async def open_settings(message: types.Message):
    """Handle 'Settings' button."""
    await message.answer("Выберите настройку:", reply_markup=get_settings_menu())

@dp.message_handler(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: types.Message):
    """Handle 'Back' button."""
    await message.answer("Главное меню:", reply_markup=get_main_menu())

@dp.callback_query_handler(lambda c: c.data == 'open_menu', state='*')
async def show_main_menu(callback_query: types.CallbackQuery, state: FSMContext = None):
    """Обработка возврата в главное меню."""
    try:
        # Если есть активное состояние, отменяем его
        if state:
            await state.finish()
        
        # Пытаемся отредактировать сообщение
        try:
            await callback_query.message.edit_text("Главное меню:", reply_markup=get_main_menu())
        except Exception:
            # Если не удалось отредактировать, отправляем новое сообщение
            await callback_query.message.answer("Главное меню:", reply_markup=get_main_menu())
        
        # Отвечаем на callback, чтобы убрать часики
        await callback_query.answer()
    except Exception as e:
        logging.error(f"Ошибка при возврате в главное меню: {e}")
        await callback_query.message.answer("Главное меню:", reply_markup=get_main_menu())

@dp.callback_query_handler(lambda c: c.data.startswith('type_'), state='*')
async def choose_ad_type(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа рекламы."""
    ad_type = callback_query.data.split('_')[1].upper()
    async with state.proxy() as data:
        data['ad_type'] = ad_type
    
    # Создаем клавиатуру с кнопкой "Назад"
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="open_menu"))
    
    await bot.send_message(
        callback_query.from_user.id,
        f"Введите данные ({ad_type}) в формате:\n"
        "ДД.ММ.ГГГГ, @юзер, время, условия, CPM/сумма",
        reply_markup=keyboard
    )
    await AdForm.waiting_for_data.set()

@dp.message_handler(state=AdForm.waiting_for_data)
async def process_fsm_data(message: types.Message, state: FSMContext):
    """Обработка данных формы."""
    try:
        async with state.proxy() as data:
            ad_type = data['ad_type']
            await process_ad_data(message, ad_type)
        await state.finish()
        await message.answer("Главное меню:", reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"Ошибка при обработке данных формы: {e}")
        await state.finish()
        await message.answer(
            "❌ Произошла ошибка при обработке данных. Возврат в главное меню.",
            reply_markup=get_main_menu()
        )

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
        async with aiosqlite.connect('advertisements.db') as db:
            if ad_type == 'CPM':
                cpm = float(value.replace(',', '.'))
                await db.execute('''
                INSERT INTO ads (ad_type, date, username, time, conditions, cpm, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ad_type, date, username, time, conditions, cpm, 'Не оплачено'))
                
                ad_id = (await (await db.execute('SELECT last_insert_rowid()')).fetchone())[0]
                post_time = datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M")
                
                # Schedule post processing
                scheduler.add_job(
                    lambda: asyncio.create_task(parse_post(ad_id)),
                    'date', 
                    run_date=post_time + timedelta(hours=24)
                )
            else:
                profit = float(value.replace(',', '.'))
                await db.execute('''
                INSERT INTO ads (ad_type, date, username, time, conditions, profit, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ad_type, date, username, time, conditions, profit, 'Оплачено'))

            await db.commit()
            
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

@dp.message_handler(lambda m: m.text.startswith(f"@{BOT_USERNAME}"))
async def handle_mention(message: types.Message):
    clean_text = message.text.replace(f"@{BOT_USERNAME}", "").strip()
    if not clean_text:
        await message.reply("❌ Сообщение не содержит данных")
        return
    message.text = clean_text
    await process_ad_data(message)

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

@dp.callback_query_handler(lambda c: c.data == 'admin')
async def handle_admin_menu(callback_query: types.CallbackQuery):
    """Handle admin menu access."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return
    
    await callback_query.message.edit_text(
        "🔧 Панель администратора:",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == 'edit_ads')
async def edit_ads(callback_query: types.CallbackQuery):
    """Handle advertisement editing."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    try:
        async with aiosqlite.connect('advertisements.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT id, ad_type, username FROM ads ORDER BY created_at DESC')
            rows = await cursor.fetchall()

            if not rows:
                await callback_query.message.edit_text("База данных пуста.")
                return

            keyboard = InlineKeyboardMarkup(row_width=2)
            for row in rows:
                keyboard.add(InlineKeyboardButton(
                    f"ID: {row['id']} | {row['ad_type']} | {row['username']}",
                    callback_data=f"edit_{row['id']}"
                ))
            keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin"))

            await callback_query.message.edit_text(
                "Выберите запись для редактирования:",
                reply_markup=keyboard
            )

    except Exception as e:
        logging.error(f"Error in edit_ads: {e}")
        await callback_query.message.edit_text("❌ Произошла ошибка при загрузке записей.")

@dp.callback_query_handler(lambda c: c.data.startswith('edit_'))
async def edit_ad(callback_query: types.CallbackQuery):
    """Handle individual advertisement editing."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    ad_id = int(callback_query.data.split('_')[1])
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
            row = await cursor.fetchone()

            if not row:
                await callback_query.answer("Запись не найдена.", show_alert=True)
                return

            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("Изменить статус", callback_data=f"status_{ad_id}"),
                InlineKeyboardButton("Удалить", callback_data=f"delete_{ad_id}"),
                InlineKeyboardButton("⬅️ Назад", callback_data="edit_ads")
            )

            response = (
                f"📝 Редактирование записи ID: {ad_id}\n\n"
                f"Тип: {row['ad_type']}\n"
                f"Дата: {row['date']}\n"
                f"Пользователь: {row['username']}\n"
                f"Время: {row['time']}\n"
                f"Условия: {row['conditions']}\n"
            )
            if row['ad_type'] == 'CPM':
                response += f"CPM: {row['cpm']}\n"
            else:
                response += f"Прибыль: {row['profit']}\n"
            response += f"Статус: {row['payment_status']}"

            await callback_query.message.edit_text(response, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in edit_ad: {e}")
        await callback_query.message.edit_text("❌ Произошла ошибка при загрузке записи.")

@dp.callback_query_handler(lambda c: c.data.startswith('status_'))
async def change_status(callback_query: types.CallbackQuery):
    """Handle advertisement status change."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    ad_id = int(callback_query.data.split('_')[1])
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            await db.execute(
                'UPDATE ads SET payment_status = CASE WHEN payment_status = "Оплачено" THEN "Не оплачено" ELSE "Оплачено" END WHERE id = ?',
                (ad_id,)
            )
            await db.commit()
            await callback_query.answer("Статус успешно изменен!")
            await edit_ad(callback_query)  # Refresh the view

    except Exception as e:
        logging.error(f"Error in change_status: {e}")
        await callback_query.answer("❌ Произошла ошибка при изменении статуса.", show_alert=True)

@dp.callback_query_handler(lambda c: c.data.startswith('delete_'))
async def delete_ad(callback_query: types.CallbackQuery):
    """Handle advertisement deletion."""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    ad_id = int(callback_query.data.split('_')[1])
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            await db.execute('DELETE FROM ads WHERE id = ?', (ad_id,))
            await db.commit()
            await callback_query.answer("Запись успешно удалена!")
            await edit_ads(callback_query)  # Return to edit menu

    except Exception as e:
        logging.error(f"Error in delete_ad: {e}")
        await callback_query.answer("❌ Произошла ошибка при удалении записи.", show_alert=True)

async def parse_post(ad_id):
    """Process scheduled advertisement post."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
            ad = await cursor.fetchone()
            
            if ad:
                # Process the advertisement post
                # Add your post processing logic here
                logging.info(f"Processing advertisement post ID: {ad_id}")
    except Exception as e:
        logging.error(f"Error processing post {ad_id}: {e}")

async def on_startup(dp):
    """Initialize bot on startup."""
    try:
        setup_process_lock()
        await init_db()
        scheduler.start()
        logging.info("Bot started successfully")
    except Exception as e:
        logging.error(f"Error during startup: {e}")
        sys.exit(1)

async def shutdown(dispatcher: Dispatcher):
    """Cleanup on bot shutdown."""
    try:
        await dispatcher.storage.close()
        await dispatcher.storage.wait_closed()
        await bot.session.close()
        scheduler.shutdown()
        cleanup()
        logging.info("Bot shutdown completed")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")

def handle_exit(sig, frame):
    """Handle exit signals."""
    logging.info("Shutting down...")
    asyncio.get_event_loop().run_until_complete(shutdown(dp))
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    # Start the bot
    try:
        executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)