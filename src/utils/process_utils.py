"""
Утилиты для управления процессом и блокировками
"""

import os
import sys
import psutil
import logging
from src.config.config import LOCK_FILE

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

def setup_logging():
    """Настройка логирования."""
    from src.config.config import LOGGING_CONFIG
    logging.basicConfig(
        level=LOGGING_CONFIG['level'],
        format=LOGGING_CONFIG['format']
    ) 