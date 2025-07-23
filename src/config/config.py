"""
Конфигурационный файл с основными настройками бота
"""

# Базовые настройки бота
API_TOKEN = ''
BOT_USERNAME = ''
ADMIN_ID =''

# Файл блокировки для предотвращения множественных запусков
LOCK_FILE = "bot.lock"

# Допустимые условия рекламы
VALID_CONDITIONS = {'24ч', '48ч', '72ч', '3дня', 'неделя', 'бессрочно'}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
} 