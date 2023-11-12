from telebot.types import Message
from loguru import logger
from loader import bot
from database.db_info import *


@bot.message_handler(commands=['start'])
def bot_start(message: Message):
    logger.add(
        "logs/logs.log",
        format="{time} {level} {message}",
        level="DEBUG",
        rotation="1 week",
        compression="zip"
    )  # создание лога или подключение к нему

    logger.info("Пользователь " + message.from_user.username + " начал работу с ботом.")

    with db:  # подключение к базе данных для того, чтобы определить,
        # работал ли этот пользователь с данным ботом или нет
        db.create_tables([User, History])  # создание или подключение к таблицам пользователей и историй поиска
        # определение пользователя

        if len(User.select()) != 0 and User.get(User.telegram_id == message.from_user.id):
            bot.reply_to(message, f"Рад снова приветствовать тебя, {message.from_user.full_name}! "
                                  f"Я - бот по поиску отелей по всему миру. Готов снова помочь тебе в выборе. "
                                  f"Напомню, что ты можешь выбрать любую команду из меню или воспользоваться "
                                  f"командой /help, чтобы вспомнить, какие команды я могу выполнить.")
        else:
            bot.reply_to(message, f"Привет, {message.from_user.full_name}! Я - бот по поиску отелей по всему миру. "
                                  f"Готов помочь тебе в выборе. Пожалуйста, выбери любую команду из меню или "
                                  f"воспользуйся командой /help, чтобы узнать, какие команды я могу выполнить.")

