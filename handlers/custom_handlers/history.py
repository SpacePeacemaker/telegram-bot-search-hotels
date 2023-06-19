from loguru import logger
from telebot import types
from telebot.types import CallbackQuery, Message
from loader import bot
from database.db_info import *
from states.history_states import HistoryInfoState


@logger.catch()
@bot.message_handler(commands=['history'])
def history(message: Message) -> None:
    with db:
        try:
            users = User.select()
            for user in users:
                if user.telegram_id == message.from_user.id:
                    user_histories = History.select().where(History.user_id == user.id)
                    keyboard = types.InlineKeyboardMarkup()
                    for user_history in user_histories:
                        cb_data = 'history|' + str(user_history.id)
                        user_date_time = str(user_history.date_time)[:19]
                        keyboard.add(types.InlineKeyboardButton(text=user_date_time + ' - ' + user_history.city
                                                                + ' - ' + user_history.command, callback_data=cb_data))

                    bot.send_message(message.chat.id, 'Пожалуйста, уточните ваш поиск, '
                                                      'детали которого вы хотели бы просмотреть:',
                                     reply_markup=keyboard)
                    bot.set_state(message.from_user.id, HistoryInfoState.exact_history, message.chat.id)
                else:
                    bot.send_message(message.chat.id, 'В базе данных нет записей о вашей истории поисков. '
                                                      'Похоже, вы ещё ни разу не пользовались ботом. '
                                                      'Самое время начать!')
        except BaseException:
            pass


@logger.catch()
@bot.callback_query_handler(func=lambda call: call.data.split('|')[1].isdigit(), state=HistoryInfoState.exact_history)
def get_exact_history(call: CallbackQuery) -> None:
    with db:
        try:
            users = User.select()
            for user in users:
                if user.telegram_id == call.from_user.id:
                    user_history = History.select().where(History.id == call.data.split('|')[1])
                    for row in user_history:
                        bot.send_message(call.message.chat.id, 'Вот детали поиска, который вы выбрали:')

                        text_message = 'Дата и время: ' + str(row.date_time)[:19] + '\n' + \
                                       'Команда: ' + row.command + '\n' + \
                                       'Город: ' + row.city + '\n' + \
                                       'Отель: ' + row.exact_hotel + '\n' + \
                                       'Фотографий: ' + str(row.hotel_photos) + '\n' + \
                                       'Дата заезда: ' + str(row.check_in_date) + '\n' + \
                                       'Дата выезда: ' + str(row.check_out_date) + '\n' + \
                                       'Взрослых: ' + str(row.adults) + '\n' + \
                                       'Детей: ' + str(row.children)

                        if row.exact_age_children is not None:
                            text_message += '\nВозраст детей: ' + row.exact_age_children
                        if row.url_hotel is not None:
                            text_message += '\nСсылка на отель: ' + row.url_hotel
                        if row.night_price is not None:
                            text_message += '\nЦена за 1 ночь: ' + str(row.night_price) + '$'
                        if row.total_price is not None:
                            text_message += '\nЦена за ' + str(row.nights) + ' ночей: ' + str(row.total_price) + '$'
                        if row.price_min is not None:
                            text_message += '\nМинимальная цена в поиске: ' + row.price_min
                        if row.price_max is not None:
                            text_message += '\nМаксимальная цена в поиске: ' + row.price_max
                        if row.dest_min is not None:
                            text_message += '\nМинимальное расстояние до центра в поиске: ' + row.dest_min
                        if row.dest_max is not None:
                            text_message += '\nМаксимальное расстояние до центра в поиске: ' + row.dest_max

                        bot.send_message(call.message.chat.id, text_message)

                        if row.urls_photos is not None:
                            bot.send_message(call.message.chat.id, "Были найдены следующие фотографии:")
                            photos_list = row.urls_photos.splitlines()
                            for photo in photos_list:
                                bot.send_photo(call.message.chat.id, photo)
        except BaseException:
            pass
