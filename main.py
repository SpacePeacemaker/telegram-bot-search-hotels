from typing import Any
import telebot


bot = telebot.TeleBot('5409088393:AAEpmUtps4eDAxYgdw1irb-MO-1nxu2PDes')


@bot.message_handler(content_types=['text', 'document', 'audio'])
def get_text_messages(message: Any) -> None:
    if message.text == 'Привет':
        bot.send_message(message.from_user.id, 'Привет, чем я могу тебе помочь?')
    elif message.text == '/help':
        bot.send_message(message.from_user.id, 'Напиши Привет или /hello_world')
    elif message.text == '/hello_world':
        bot.send_message(message.from_user.id, 'Hello, world!')
    else:
        bot.send_message(message.from_user.id, 'Я тебя не понимаю. Напиши /help.')


bot.polling(none_stop=True, interval=0)
