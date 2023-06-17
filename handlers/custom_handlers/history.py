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
                        keyboard.add(types.InlineKeyboardButton(text=user_history.date + ' - ' + user_history.city
                                                                + ' - ' + user_history.command, callback_data=cb_data))

                    bot.send_message(message.chat.id, 'Пожалуйста, уточните ваш поиск, '
                                                           'детали которого вы хотели бы просмотреть:',
                                     reply_markup=keyboard)
                    bot.set_state(message.from_user.id, HistoryInfoState.exact_history, message.chat.id)
                    # break
                else:
                    bot.send_message(message.chat.id, "В базе данных нет записей о вашей истории поисков. "
                                                           "Похоже, вы ещё ни разу не пользовались ботом. "
                                                           "Самое время начать!")
        except BaseException:
            pass


@logger.catch()
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == "history", state=HistoryInfoState.exact_history)
def get_exact_history(call: CallbackQuery) -> None:
    with db:
        try:
            histories = History.select()
            for user_history in histories:
                if user_history.id == call.data:
                    bot.send_message(call.message.chat.id, 'Вот детали поиска, который вы выбрали:')
                    text_message = 'Дата: ' + str(user_history.date) + '\n' + \
                        'Команда: ' + user_history.command + '\n' + \
                        'Город: ' + user_history.city + '\n' + \
                        'Отель: ' + user_history.exact_hotel + '\n' + \
                        'Ссылка на отель: ' + user_history.url_hotel + '\n' + \
                        'Цена за 1 ночь: ' + str(user_history.night_price) + '$\n' + \
                        'Цена за ' + str(user_history.nights) + ' ночей: ' + str(user_history.total_price) + '$\n' + \
                        'Дата заезда: ' + str(user_history.check_in_date) + '\n' + \
                        'Дата выезда: ' + str(user_history.check_out_date) + '\n' + \
                        'Взрослых: ' + str(user_history.adults) + '\n' + \
                        'Детей: ' + str(user_history.children) + '\n' + \
                        'Возраст детей: ' + user_history.exact_age_children + '\n' + \
                        'Фотографий: ' + str(user_history.hotel_photos) + '\n' + \
                        'Ссылки на фотографии: ' + '\n' + user_history.urls_photos + '\n'
                    bot.send_message(call.message.chat.id, text_message)
                    # break
        except BaseException:
            pass
