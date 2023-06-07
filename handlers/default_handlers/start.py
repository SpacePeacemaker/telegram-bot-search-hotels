from telebot.types import Message
from loguru import logger
from loader import bot


@bot.message_handler(commands=['start'])
def bot_start(message: Message):
    logger.add("logs/logs.log", format="{time} {level} {message}", level="DEBUG", rotation="1 week",
                          compression="zip")
    logger.info("Пользователь " + message.from_user.username + " начал работу с ботом.")
    bot.reply_to(message, f"Привет, {message.from_user.full_name}! Я - бот по поиску отелей по всему миру. "
                          f"Готов помочь тебе в выборе. Пожалуйста, выбери любую команду из меню или "
                          f"воспользуйся командой /help, чтобы узнать, какие команды я могу выполнить.")

