from loguru import logger
from telebot import types
from telebot.types import CallbackQuery, Message
from loader import bot
from database.db_info import *
from states.history_states import HistoryInfoState
from keyboards.inline import user_choice_keyboard
from collections import namedtuple


@logger.catch()
@bot.message_handler(commands=['history'])
def history(message: Message) -> None:
    """
    Функция истории поиска теущего пользователя.
    :param message: Message
    :return: None
    """
    logger.add("logs/logs.log",
               format="{time} {level} {message}",
               level="DEBUG",
               rotation="1 week",
               compression="zip")  # создание лога или подключение к нему

    logger.info("Пользователь " + message.from_user.username + " ввёл команду: " + message.text)
    temp_arr = []  # создание временного массива для сохранения историй поиска пользователя
    # в памяти бота для логирования

    with db:  # открываем менеджер базы данных
        try:
            users = User.select()  # выбираем всех имеющихся пользователей
            for user in users:  # цикл поиска текущего пользователя в базе данных
                if user.telegram_id == message.from_user.id:
                    user_histories = History.select().where(History.user_id == user.id)
                    buttons_list = []
                    for user_history in user_histories:  # формируем клавиатуру с историей поиска текущего пользователя
                        cb_data = 'history|' + str(user_history.id)
                        text = str(user_history.date_time)[:19] + ' - ' \
                            + user_history.city + ' - ' + user_history.command
                        info_button = namedtuple('Button_Info', 'text cb_data')
                        but_cor = info_button(text, cb_data)
                        temp_arr.append(but_cor)
                        buttons_list.append(types.InlineKeyboardButton(text=text, callback_data=cb_data))
                    keyboard = types.InlineKeyboardMarkup(user_choice_keyboard.create_button_keyboard(buttons_list))
                    bot.send_message(message.chat.id,
                                     'Пожалуйста, уточните ваш поиск, детали которого вы хотели бы просмотреть:',
                                     reply_markup=keyboard)
                    logger.info("Пользователь " + message.from_user.username + " получил список своих поисков.")
                    # установка бота в состояние для уточнения истории поиска
                    bot.set_state(message.from_user.id, HistoryInfoState.exact_history, message.chat.id)
                else:
                    bot.send_message(message.chat.id, 'В базе данных нет записей о вашей истории поисков. '
                                                      'Похоже, вы ещё ни разу не пользовались ботом. '
                                                      'Самое время начать!')
                    logger.warning("Пользователь " + message.from_user.username + " отсутствует в базе данных.")
        except DatabaseError:  # ошибка отсутствия базы данных
            bot.send_message(message.chat.id, 'Базы данных пока что не существует. '
                                              'Самое время начать пользоваться ботом!')
            logger.warning("База данных отсутствует!")

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        data_info["choice_history"] = temp_arr  # занесение информации об истории поиска пользователя в память бота
        # для логирования


@logger.catch()
@bot.callback_query_handler(func=lambda call: call.data.split('|')[1], state=HistoryInfoState.exact_history)
def get_exact_history(call: CallbackQuery) -> None:
    """
    Функция вывода конкретного поиска текущего пользователя.
    :param call: CallbackQuery
    :return: None
    """
    # логирование выбора пользователем истории поиска
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        for u_ch in data_info['choice_history']:
            if u_ch.cb_data == call.data:
                logger.info("Пользователь " + call.message.chat.username + " выбрал следующий поиск: " + u_ch.text)

    with db:  # открываем менеджер базы данных
        try:
            user_history = History.select().where(History.id == call.data.split('|')[1])  # выбор конкретного поиска
            # пользователя, совпадающего с callback-информацией кнопки, которую он нажал
            for row in user_history:  # вывод деталей истории поиска
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
                    arr_age = row.exact_age_children.split()
                    age_children = ""
                    for age in arr_age:
                        if arr_age.index(age) == len(arr_age) - 1 and len(arr_age) != 1:
                            age_children = age_children[:-2] + " и " + age
                        elif len(arr_age) == 1:
                            age_children = age
                        else:
                            age_children += age + ", "
                    text_message += '\nВозраст детей: ' + age_children
                if row.hotel_address is not None:
                    text_message += '\nСсылка на отель: ' + row.hotel_address
                if row.url_hotel is not None:
                    text_message += '\nСсылка на отель: ' + row.url_hotel
                if row.night_price is not None:
                    text_message += '\nЦена за 1 ночь: ' + str(row.night_price) + '$'
                if row.total_price is not None:
                    text_message += '\nЦена за ' + str(row.nights) + ' ночей: ' + str(row.total_price) + '$'
                if row.price_min is not None:
                    text_message += '\nМинимальная цена в поиске: ' + str(row.price_min)
                if row.price_max is not None:
                    text_message += '\nМаксимальная цена в поиске: ' + str(row.price_max)
                if row.dest_min is not None:
                    text_message += '\nМинимальное расстояние до центра в поиске: ' + str(row.dest_min)
                if row.dest_max is not None:
                    text_message += '\nМаксимальное расстояние до центра в поиске: ' + str(row.dest_max)

                bot.send_message(call.message.chat.id, text_message)

                if row.urls_photos is not None:
                    bot.send_message(call.message.chat.id, "Были найдены следующие фотографии:")
                    photos_list = row.urls_photos.splitlines()
                    for photo in photos_list:
                        bot.send_photo(call.message.chat.id, photo)

        except DatabaseError:  # ошибка с базой данных
            bot.send_message(call.message.chat.id, "Возникла проблема с базой данных. Пожалуйста, попробуйте позже.")

    bot.delete_state(call.from_user.id, call.message.chat.id)  # удаление состояния бота для новой команды
