from loguru import logger
from telebot import types
from telebot.types import CallbackQuery
from loader import bot
from database import db_info, read_from_db


@logger.catch()
@bot.callback_query_handler(func=lambda call: True, commands=['history'])
def history(call: CallbackQuery) -> None:
    db_info.db.connect()
