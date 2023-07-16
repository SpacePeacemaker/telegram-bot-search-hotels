import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()
"""
Хранение токена бота, ключа API и списка команд бота
"""
BOT_TOKEN = os.getenv('BOT_TOKEN')  # токен бота
RAPID_API_KEY = os.getenv('RAPID_API_KEY')  # ключ API
DEFAULT_COMMANDS = (  # список команд бота
    ('start', "Запустить бота"),
    ('help', "Вывести справку"),
    ('lowprice', "Найти отель по самой низкой цене"),
    ('highprice', "Найти отель по самой высокой цене"),
    ('bestdeal', "Найти отель по лучшей цене и расстоянию от центра города"),
    ('history', "Вывести историю поиска отелей"),
)
