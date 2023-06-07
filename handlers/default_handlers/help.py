from telebot.types import Message
from loguru import logger
from config_data.config import DEFAULT_COMMANDS
from loader import bot


@bot.message_handler(commands=['help'])
def bot_help(message: Message):
    logger.add("logs/logs.log", format="{time} {level} {message}", level="DEBUG", rotation="1 week",
                          compression="zip")
    logger.info("Пользователь " + message.from_user.username + "воспользовался командой /help")
    text = [f'/{command} - {desk}' for command, desk in DEFAULT_COMMANDS]
    bot.reply_to(message, '\n'.join(text))
