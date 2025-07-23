"""
Модуль для работы с базой данных
"""

import logging
import aiosqlite
from datetime import datetime

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

async def add_advertisement(ad_type, date, username, time, conditions, value, payment_status="Не оплачено"):
    """Добавление новой рекламы в базу данных."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            if ad_type == 'CPM':
                await db.execute('''
                INSERT INTO ads (ad_type, date, username, time, conditions, cpm, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ad_type, date, username, time, conditions, float(value), payment_status))
            else:
                await db.execute('''
                INSERT INTO ads (ad_type, date, username, time, conditions, profit, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ad_type, date, username, time, conditions, float(value), payment_status))
            await db.commit()
            return (await (await db.execute('SELECT last_insert_rowid()')).fetchone())[0]
    except Exception as e:
        logging.error(f"Ошибка при добавлении рекламы: {e}")
        raise

async def get_all_ads():
    """Получение всех рекламных объявлений."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM ads ORDER BY created_at DESC') as cursor:
                return await cursor.fetchall()
    except Exception as e:
        logging.error(f"Ошибка при получении реклам: {e}")
        raise

async def get_ad_by_id(ad_id):
    """Получение рекламы по ID."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM ads WHERE id = ?', (ad_id,)) as cursor:
                return await cursor.fetchone()
    except Exception as e:
        logging.error(f"Ошибка при получении рекламы по ID: {e}")
        raise

async def update_ad_field(ad_id, field, value):
    """Обновление поля рекламы."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            await db.execute(f'UPDATE ads SET {field} = ? WHERE id = ?', (value, ad_id))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при обновлении поля рекламы: {e}")
        raise

async def delete_ad(ad_id):
    """Удаление рекламы."""
    try:
        async with aiosqlite.connect('advertisements.db') as db:
            await db.execute('DELETE FROM ads WHERE id = ?', (ad_id,))
            await db.commit()
    except Exception as e:
        logging.error(f"Ошибка при удалении рекламы: {e}")
        raise 