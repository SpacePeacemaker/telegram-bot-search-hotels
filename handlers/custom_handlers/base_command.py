from datetime import date

from loader import bot
from telebot import types
from telebot.types import Message, CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from loguru import logger

from database.db_info import *
from states.search_hotels import HotelInfoState
from utils.misc import api_city_list, api_hotels_list, api_hotel_info
from keyboards.inline import user_choice_keyboard


LSTEP = {'y': 'год', 'm': 'месяц', 'd': 'день'}  # переопределение подписей в календаре от telegram_bot_calendar


@logger.catch()
@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def price(message: Message) -> None:
    """
    Функция начала работы с ботом, когда пользователь выбрал одну из трёх команд: lowprice, highprice или bestdeal.
    :param message: Message
    :return: None
    """
    logger.add(
        "logs/logs.log",
        format="{time} {level} {message}",
        level="DEBUG",
        rotation="1 week",
        compression="zip"
    )  # создание лога или подключение к нему

    logger.info("Пользователь " + message.from_user.username + " ввёл команду: " + message.text)
    bot.set_state(message.from_user.id, HotelInfoState.command, message.chat.id)  # установка состояния бота для
    # приёма значения выбранной пользователем команды бота
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        data_info["command"] = message.text  # хранение в памяти бота выбранной команды
        data_info["price_bestdeal"] = 0  # хранение в памяти бота цены для команды bestdeal
        data_info["dest_bestdeal"] = 0  # хранение в памяти бота расстояния для команды bestdeal
        # установка сообщения для пользователя при выборе соответствующей команды
        if message.text == '/lowprice':
            sort_message = "САМОЙ НИЗКОЙ"
        elif message.text == '/highprice':
            sort_message = "САМОЙ ВЫСОКОЙ"
        elif message.text == '/bestdeal':
            sort_message = "УСТАНОВЛЕННЫМИ ВАМИ РАССТОЯНИЮ ДО ЦЕНТРА ГОРОДА И"
            data_info["price_bestdeal"] = []  # переопределение в памяти бота цен для команды bestdeal
            data_info["dest_bestdeal"] = []  # переопределение в памяти бота расстояний для команды bestdeal

        bot.set_state(message.from_user.id, HotelInfoState.city, message.chat.id)  # установка состояния бота для
        # приёма значения выбранного пользователем города
        bot.send_message(message.from_user.id, f"{message.from_user.first_name}, сейчас я поищу отели по "
                         + sort_message + f" ЦЕНЕ. Сперва мне нужно узнать МЕСТОПОЛОЖЕНИЕ,"
                                          f" в котором мы будем искать отели. Напишите его.")


@logger.catch()
@bot.message_handler(state=HotelInfoState.city)
def get_city(message: Message) -> None:
    """
    Функция для приёма города от пользователя.
    :param message: Message
    :return: None
    """
    logger.info("Пользователь " + message.from_user.username + " ввёл следующее местоположение: " + message.text)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if message.text.isalpha():  # проверка на ввод буквенных значений
            data_info["dict_answer"] = api_city_list.get_city_list(message.text)
            buttons_list = []  # инициализация списка кнопок клавиатуры
            for i_key, i_value in data_info["dict_answer"].items():
                buttons_list.append(types.InlineKeyboardButton(text=i_value, callback_data=i_key))  # создание кнопок
                # с подходящими городами
            keyboard = types.InlineKeyboardMarkup(user_choice_keyboard.create_button_keyboard(buttons_list))
            # создание клавиатуры с кнопками городов
            bot.send_message(message.chat.id, 'Пожалуйста, уточните желаемое МЕСТОПОЛОЖЕНИЕ:', reply_markup=keyboard)
            bot.set_state(message.from_user.id, HotelInfoState.exact_city, message.chat.id)  # установка состояния бота
            # для уточнения города
            logger.info("Бот вывел все подходящие местоположения для уточнения.")

        else:
            logger.warning("Пользователь " + message.from_user.username + " неверно ввёл название города: " +
                           message.text)
            bot.send_message(message.from_user.id, "Такого города нет. Попробуйте снова. Напишите город, "
                                                   "в котором нужно поискать отели")


@logger.catch()
@bot.callback_query_handler(func=lambda call: call.data, state=HotelInfoState.exact_city)
def get_exact_city(call: CallbackQuery) -> None:
    """
    Функция для уточнения города пользователем.
    :param call: CallbackQuery
    :return: None
    """
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        for city_key, city_value in data_info["dict_answer"].items():
            if city_key == call.data:  # в словаре сравниваем искомый id из callback_data нажатой кнопки
                logger.info("Пользователь " + call.message.chat.username + " уточнил местоположение: " +
                            city_value)
                bot.send_message(call.message.chat.id, "Вы выбрали следующее местоположение - " + city_value)
                bot.send_message(call.message.chat.id, "Отлично! Теперь напишите "
                                                       "КОЛИЧЕСТВО ВЗРОСЛЫХ ГОСТЕЙ (не более 5-ти).")

                data_info["city"] = city_value  # занесение в память бота названия конкретного города
                data_info["city_id"] = call.data  # занесение в память бота id конкретного города

                bot.set_state(call.from_user.id, HotelInfoState.adults, call.message.chat.id)  # установка бота
                # в состояние для уточнения количества гостей


@logger.catch()
@bot.message_handler(state=HotelInfoState.adults)
def get_adults(message: Message) -> None:
    """
    Функция для получения количества гостей.
    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text) <= 5:  # если сообщение является числом,
        # и оно находится в пределах от 1 до 5
        logger.info("Пользователь " + message.from_user.username + " ввёл количество взрослых гостей: " + message.text)
        bot.send_message(message.from_user.id, "Отлично! Теперь напишите КОЛИЧЕСТВО ДЕТЕЙ, которые будут "
                                               "гостями отеля (не более 5-ти). Если детей не будет, напишите цифру 0.")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
            data_info["adults"] = int(message.text)  # занесение в память бота количества гостей.
        bot.set_state(message.from_user.id, HotelInfoState.children, message.chat.id)  # установка бота в состояние
        # для уточнения количества детей.
    else:
        logger.warning("Пользователь " + message.from_user.username + " неверно ввёл количество взрослых гостей: " +
                       message.text)
        bot.send_message(message.from_user.id, "Что-то пошло не так. Либо вы написали число не от 1 до 5, либо вы "
                                               "написали не число. Попробуйте снова: сколько будет взрослых гостей?")


@logger.catch()
@bot.message_handler(state=HotelInfoState.children)
def get_children(message: Message) -> None:
    """
    Функция для определения количества детей.
    :param message: Message
    :return: None
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if message.text.isdigit() and 0 <= int(message.text) <= 5:  # если сообщение является числом и оно находится
            # в пределах от 0 до 5
            logger.info("Пользователь " + message.from_user.username + " ввёл количество детей: " + message.text)
            if int(message.text) == 0 and data_info["command"] != '/bestdeal':  # если сообщение равно 0,
                # и пользователь НЕ ВЫБРАЛ команду bestdeal
                bot.send_message(message.from_user.id, "Отлично! Теперь введите КОЛИЧЕСТВО ОТЕЛЕЙ, которые вы хотите "
                                                       "посмотреть (не более 10-ти).")
                bot.set_state(message.from_user.id, HotelInfoState.hotels_number, message.chat.id)  # установка бота
                # в состояние для уточнения количества отелей для поиска
            elif int(message.text) == 0 and data_info["command"] == '/bestdeal':  # если сообщение равно нулю,
                # и пользователь ВЫБРАЛ команду bestdeal
                bot.set_state(message.from_user.id, HotelInfoState.price_min, message.chat.id)  # установка бота
                # в состояние для уточнения минимальной цены
                bot.send_message(message.from_user.id, "Отлично! Теперь введите МИНИМАЛЬНУЮ СТОИМОСТЬ (в долларах) "
                                                       "за всю поездку, которую вы готовы потратить на отель.")
            elif 1 <= int(message.text) <= 5:  # если сообщение находится в пределах от 1 до 5
                bot.send_message(message.from_user.id, "Отлично! Теперь вам нужно уточнить ВОЗРАСТ детей.")
                bot.send_message(message.from_user.id, "Введите возраст 1-го ребёнка:")
                bot.set_state(message.from_user.id, HotelInfoState.exact_age_children, message.chat.id)  # установка
                # бота в состояние для уточнения возраста детей
                logger.info("Пользователь " + message.from_user.username + " начинает вводить возраст детей.")

            data_info["children"] = int(message.text)  # занесение в память бота количества детей

        else:
            logger.warning("Пользователь " + message.from_user.username + " неверно ввёл количество детей: "
                           + message.text)
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Либо вы ввели число не от 0 до 5, либо вы ввели "
                             "не число. Попробуйте снова: сколько будет детей?")


@logger.catch()
@bot.message_handler(state=HotelInfoState.exact_age_children)
def get_age_children(message: Message) -> None:
    """
    Функция для определения возраста детей
    :param message: Message
    :return: None
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if "children_age" not in data_info.keys():  # условие для создания в памяти бота словаря с возрастом детей
            data_info["children_age"] = {}

        if message.text.isdigit() and 0 < int(message.text) < 18:  # если сообщение является числом, и оно находится
            # в пределах от 1 до 18
            logger.info("Пользователь " + message.from_user.username + " ввёл возраст " +
                        str(len(data_info['children_age']) + 1) + "-го ребёнка: " + message.text)
            data_info["children_age"][len(data_info["children_age"]) + 1] = int(message.text)  # занесение в память бота
            # возраста ребёнка
        else:  # если условие для добавления возраста ребёнка в память бота не выполняется
            logger.warning("Пользователь " + message.from_user.username + " неверно ввёл возраст " +
                           str(len(data_info['children_age']) + 1) + "-го ребёнка: " + message.text)
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Либо вы написали число не от 1 до 17, либо вы написали "
                             "не число. Попробуйте снова.")

        if data_info["children"] != len(data_info["children_age"]):  # условие для продолжения уточнения возраста детей,
            # пока не достигнуто количество детей
            bot.send_message(message.from_user.id, f"Напишите возраст {len(data_info['children_age']) + 1}-го ребёнка:")
            # bot.set_state(message.from_user.id, HotelInfoState.exact_age_children, message.chat.id)
        elif data_info["command"] == '/bestdeal':  # если достигнуто количество детей, и пользователь ВЫБРАЛ команду
            # bestdeal
            bot.set_state(message.from_user.id, HotelInfoState.price_min, message.chat.id)  # установка бота в состояние
            # уточнения минимальной цены
            logger.info("Пользователь " + message.from_user.username + " закончил вводить возраст детей.")
            bot.send_message(message.from_user.id, "Отлично! Теперь введите МИНИМАЛЬНУЮ СТОИМОСТЬ (в долларах) "
                                                   "за всю поездку, которую вы готовы потратить на отель.")
        else:  # если достигнуто количество детей, и пользователь НЕ ВЫБРАЛ команду bestdeal
            bot.set_state(message.from_user.id, HotelInfoState.hotels_number, message.chat.id)  # установка бота в
            # состояние уточнения количества отелей для поиска
            logger.info("Пользователь " + message.from_user.username + " закончил вводить возраст детей.")
            bot.send_message(message.from_user.id, "Отлично! Теперь напишите КОЛИЧЕСТВО ОТЕЛЕЙ, которые вы хотите "
                                                   "посмотреть (не более 10-ти).")


@logger.catch()
@bot.message_handler(state=HotelInfoState.price_min)
def get_price_min(message: Message) -> None:
    """
    Функция для уточнения минимальной цены при выборе команды bestdeal.
    :param message: Message
    :return: None
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if message.text.isdigit() and int(message.text) >= 0:  # если сообщение является числом, и это число больше или
            # равно нулю.
            data_info["price_bestdeal"].append(int(message.text))  # занесение в память бота минимальной цены
            bot.set_state(message.from_user.id, HotelInfoState.price_max, message.chat.id)  # установка бота в состояние
            # для уточнения максимальной цены
            bot.send_message(message.from_user.id, "Отлично! Теперь напишите МАКСИМАЛЬНУЮ СУММУ (в долларах) "
                                                   "за всю поездку, которую вы готовы потратить на отель.")
            logger.info("Пользователь " + message.from_user.username + " ввёл минимальную сумму: "
                        + message.text + "$")
        else:
            logger.warning("Пользователь " + message.from_user.username + " неверно ввёл минимальную сумму: "
                           + message.text)
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Скорее всего, вы написали не число или отрицательную сумму. "
                             "Попробуйте снова.")


@logger.catch()
@bot.message_handler(state=HotelInfoState.price_max)
def get_price_max(message: Message) -> None:
    """
    Функция для уточнения максимальной цены при выборе команды bestdeal.
    :param message: Message
    :return: None
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if message.text.isdigit() and int(message.text) > data_info["price_bestdeal"][0]:
            # если сообщение является числом, и это число больше минимальной цены
            data_info["price_bestdeal"].append(int(message.text))  # занесение в память бота максимальной цены
            bot.set_state(message.from_user.id, HotelInfoState.dest_min, message.chat.id)  # установка бота в состояние
            # для уточнения минимального расстояния от отеля до центра города
            bot.send_message(message.from_user.id, "Отлично! Теперь напишите МИНИМАЛЬНОЕ РАССТОЯНИЕ ОТ ОТЕЛЯ "
                                                   "ДО ЦЕНТРА ГОРОДА (в километрах).")
            logger.info("Пользователь " + message.from_user.username + " ввёл максимальную сумму: "
                        + message.text + "$")
        else:
            logger.warning("Пользователь " + message.from_user.username + " неверно ввёл максимальную сумму: "
                           + message.text)
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Скорее всего, вы написали не число или отрицательную сумму. "
                             "Или вы написали число, которое меньше минимальной суммы, ранее введённой вами."
                             "Попробуйте снова.")


@logger.catch()
@bot.message_handler(state=HotelInfoState.dest_min)
def get_dest_min(message: Message) -> None:
    """
    Функция для определения минимального расстояния от отеля до центра города при выборе команды bestdeal.
    :param message: Message
    :return: None
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if message.text.isdigit() and int(message.text) >= 0:  # если сообщение является числом, и это число больше нуля
            data_info["dest_bestdeal"].append(int(message.text))  # занесение в память бота минимального расстояние
            bot.set_state(message.from_user.id, HotelInfoState.dest_max, message.chat.id)  # установка бота в состояние
            # для уточнения максимальногого расстояния от отеля до центра города
            bot.send_message(message.from_user.id, "Отлично! Теперь напишите МАКСИМАЛЬНОЕ РАССТОЯНИЕ ОТ ОТЕЛЯ "
                                                   "ДО ЦЕНТРА ГОРОДА (в километрах).")
            logger.info("Пользователь " + message.from_user.username + " ввёл минимальное расстояние: "
                        + message.text + "км.")
        else:
            logger.warning("Пользователь " + message.from_user.username + " неверно ввёл минимальное расстояние: "
                           + message.text)
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Скорее всего, вы написали не число или отрицательное расстояние. "
                             "Попробуйте снова.")


@logger.catch()
@bot.message_handler(state=HotelInfoState.dest_max)
def get_dest_max(message: Message) -> None:
    """
    Функция для определения максимального расстояния от отеля до центра города при выборе команды bestdeal.
    :param message: Message
    :return: None
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if message.text.isdigit() and int(message.text) > data_info["dest_bestdeal"][0]:  # если сообщение является
            # числом, и это число больше минимального расстояния
            data_info["dest_bestdeal"].append(int(message.text))  # занесение в память бота максимального расстояния
            bot.set_state(message.from_user.id, HotelInfoState.hotels_number, message.chat.id)  # установка бота в
            # состояние для уточнения количества отелей для поиска
            bot.send_message(message.from_user.id, "Отлично! Теперь напишите КОЛИЧЕСТВО ОТЕЛЕЙ, которые вы хотите "
                                                   "посмотреть (не более 10-ти).")
            logger.info("Пользователь " + message.from_user.username + " ввёл максимальное расстояние: "
                        + message.text + "км.")
        else:
            logger.warning("Пользователь " + message.from_user.username + " неверно ввёл максимальное расстояние: "
                           + message.text)
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Скорее всего, вы написали не число или отрицательное расстояние. "
                             "Или вы написали расстояние, которое меньше минимального расстояния, ранее введёного вами."
                             " Попробуйте снова.")


@logger.catch()
@bot.message_handler(state=HotelInfoState.hotels_number)
def get_number_hotels(message: Message) -> None:
    """
    Функция для определения количества отелей для поиска.
    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text) <= 10:  # если сообщение является числом, и это число
        # находится в пределах от 1 до 10
        logger.info("Пользователь " + message.from_user.username + " ввёл количество отелей: " + message.text)
        bot.send_message(message.from_user.id, "Отлично! Теперь выберите ДАТУ ЗАЕЗДА.")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
            data_info["hotels_number"] = int(message.text)  # занесение в память бота количества отелей для поиска
        # создание календаря для определения даты заезда
        calendar_one, step_one = DetailedTelegramCalendar(calendar_id=1, locale="ru", min_date=date.today()).build()
        bot.send_message(message.chat.id,
                         f"Выберите {LSTEP[step_one]}",
                         reply_markup=calendar_one)
        logger.info("Пользователь " + message.from_user.username + " начинает выбирать дату заезда.")
        bot.set_state(message.from_user.id, HotelInfoState.check_in_date, message.chat.id)  # установка бота
        # в состояние для уточнения даты заезда
    else:
        logger.warning("Пользователь " + message.from_user.username + " неверно ввёл количество отелей: "
                       + message.text)
        bot.send_message(message.from_user.id, "Что-то пошло не так. Либо вы написали число не от 1 до 10, либо вы "
                                               "написали не число. Попробуйте снова: сколько нужно вывести отелей?")


@logger.catch()
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1), state=HotelInfoState.check_in_date)
def cal_in(call: CallbackQuery) -> None:
    """
    Функция для определения даты заезда.
    :param call: CallbackQuery
    :return: None
    """
    # отлов выбора года, месяца и дня заезда
    result_one, key_one, step_one = DetailedTelegramCalendar(calendar_id=1,
                                                             locale="ru",
                                                             min_date=date.today()).process(call.data)
    if not result_one and key_one:  # если НЕ выбраны год, месяц и день
        bot.edit_message_text(f"Выберите {LSTEP[step_one]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key_one)
    elif result_one:  # если выбраны год, месяц и день
        bot.edit_message_text(f"Вы выбрали {result_one}",
                              call.message.chat.id,
                              call.message.message_id)

        bot.send_message(call.message.chat.id, "Отлично! Теперь выберите ДАТУ ВЫЕЗДА.")
        logger.info("Пользователь " + call.message.chat.username + " выбрал дату заезда: " + str(result_one))
        bot.set_state(call.from_user.id, HotelInfoState.check_out_date, call.message.chat.id)  # установка бота
        # в состояние для уточнения даты выезда

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
            data_info["check_in_date"] = str(result_one)   # занесение в память бота даты заезда,
            # форма записи: yyyy-mm-dd
        # создание календаря для определения даты выезда
        calendar_two, step_two = DetailedTelegramCalendar(calendar_id=2,
                                                          locale="ru",
                                                          min_date=result_one).build()
        bot.send_message(call.message.chat.id, f"Выберите {LSTEP[step_two]}", reply_markup=calendar_two)
        logger.info("Пользователь " + call.message.chat.username + " начинает выбирать дату выезда.")


@logger.catch()
@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2), state=HotelInfoState.check_out_date)
def cal_out(call: CallbackQuery) -> None:
    """
    Функция для определения даты выезда.
    :param call: CallbackQuery
    :return: None
    """
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        # определение дня, следующего за днём заезда, чтобы у пользователя не было возможности
        # выбрать день выезда ранее, чем день заезда

        # массивы с месяцами
        february = [2]
        small_months = [4, 6, 9, 11]
        big_months = [1, 3, 5, 7, 8, 10, 12]

        # определение года заезда
        if int(data_info["check_in_date"][8:]) == 31 and int(data_info["check_in_date"][5:7]) == 12:
            second_year = int(data_info["check_in_date"][:4]) + 1
        else:
            second_year = int(data_info["check_in_date"][:4])

        # определение является ли год заезда высокосным
        if (int(data_info["check_in_date"][:4]) % 400 == 0) or (int(data_info["check_in_date"][:4]) % 100 != 0) or \
                (int(data_info["check_in_date"][:4]) % 4 == 0):
            leap_year = True
        else:
            leap_year = False

        # определение дня и месяца заезда
        if (int(data_info["check_in_date"][8:]) == 30 and int(data_info["check_in_date"][5:7]) in small_months) or \
                (int(data_info["check_in_date"][8:]) == 31 and int(data_info["check_in_date"][5:7]) in big_months) or \
                (int(data_info["check_in_date"][8:]) == 29 and int(data_info["check_in_date"][5:7] in february) and
                 not leap_year) or (int(data_info["check_in_date"][8:]) == 28 and
                                    int(data_info["check_in_date"][5:7] in february) and leap_year):
            second_day = 1
            second_month = int(data_info["check_in_date"][5:7]) + 1
        else:
            second_day = int(data_info["check_in_date"][8:]) + 1
            second_month = int(data_info["check_in_date"][5:7])

        # отлов выбора года, месяца и дня выезда
        result_two, key_two, step_two = DetailedTelegramCalendar(calendar_id=2, locale="ru",
                                                                 min_date=date(second_year,
                                                                               second_month,
                                                                               second_day)).process(call.data)
    if not result_two and key_two:  # если НЕ выбраны год, месяц и день
        bot.edit_message_text(f"Выберите {LSTEP[step_two]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key_two)
    elif result_two:  # если выбраны год, месяц и день
        bot.edit_message_text(f"Вы выбрали {result_two}",
                              call.message.chat.id,
                              call.message.message_id)

        logger.info("Пользователь " + call.message.chat.username + " выбрал дату выезда: " + str(result_two))
        bot.set_state(call.from_user.id, HotelInfoState.hotel_photos, call.message.chat.id)  # установка бота
        # в состояние для уточнения необходимости фотографий

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
            data_info["check_out_date"] = str(result_two)   # занесение в память бота даты выезда,
            # форма записи: yyyy-mm-dd
            data_info["hotel_photos"] = 0  # занесение в память бота количества фотографий

        # создание клавиатуры для определения необходимости фотографий
        buttons_list = [
            types.InlineKeyboardButton(text='Да', callback_data='yes'),
            types.InlineKeyboardButton(text='Нет', callback_data='no')
        ]
        keyboard = types.InlineKeyboardMarkup(user_choice_keyboard.create_button_keyboard(buttons_list))
        bot.send_message(call.message.chat.id, 'Отлично! Теперь подскажите, нужны ли вам ФОТОГРАФИИ?',
                         reply_markup=keyboard)


@logger.catch()
@bot.callback_query_handler(func=lambda call: True, state=HotelInfoState.hotel_photos)
def get_photos(call: CallbackQuery) -> None:
    """
    Функция для определения необходимости в фотографиях.
    :param call: CallbackQuery
    :return: None
    """
    if call.data == 'yes':  # если пользователь нажал кнопку "Да"
        logger.info("Пользователь " + call.message.chat.username + " выбрал, что ему нужны фотографии.")
        bot.set_state(call.from_user.id, HotelInfoState.exact_photos, call.message.chat.id)  # установка бота 
        # в состояние уточнения количества фотографий
        bot.send_message(call.message.chat.id, "Сколько фотографий вам нужно? (не больше 5-ти)")
    elif call.data == 'no':  # если пользователь нажал кнопку "Нет"
        logger.info("Пользователь " + call.message.chat.username + " выбрал, что ему не нужны фотографии.")
        bot.set_state(call.from_user.id, HotelInfoState.hotels_list, call.message.chat.id)  # установка бота в состояние
        # уточнения количества фотографий
        
        # создание кнопки для начала поиска отелей 
        buttons_list = [
            types.InlineKeyboardButton(text='Начать поиск отелей', callback_data='start_process')
        ]
        keyboard = types.InlineKeyboardMarkup(user_choice_keyboard.create_button_keyboard(buttons_list))
        bot.send_message(call.message.chat.id, 'Всё готово! Теперь нажимте кнопку "Начать поиск отелей", '
                                               'чтобы запустить процесс поиска.', reply_markup=keyboard)


@logger.catch()
@bot.message_handler(state=HotelInfoState.exact_photos)
def get_exact_photos(message: Message) -> None:
    """
    Функция для уточнения количества фотографий.
    :param message: Message
    :return: None
    """
    if message.text.isdigit() and 0 < int(message.text) <= 5:  # если сообщение является числом, 
        # и это число находится в пределах от 1 до 5
        logger.info("Пользователь " + message.from_user.username + " выбрал количество фотографий: " + message.text)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
            data_info["hotel_photos"] = int(message.text)  # занесение в память бота количества фотографий
        bot.set_state(message.from_user.id, HotelInfoState.hotels_list, message.chat.id)  # установка бота в состояние 
        # получения списка отелей

        # создание кнопки для начала поиска отелей
        buttons_list = [
            types.InlineKeyboardButton(text='Начать поиск отелей', callback_data='start_process')
        ]
        keyboard = types.InlineKeyboardMarkup(user_choice_keyboard.create_button_keyboard(buttons_list))
        bot.send_message(message.chat.id, 'Всё готово! Теперь нажимте кнопку "Начать поиск отелей", '
                                          'чтобы запустить процесс поиска.', reply_markup=keyboard)
    else:
        logger.warning("Пользователь " + message.from_user.username + " неверно выбрал количество фотографий: "
                       + message.text)
        bot.send_message(message.from_user.id, "Что-то пошло не так. Либо вы ввели число не от 1 до 5, либо вы ввели "
                         "не число. Попробуйте снова: сколько вам нужно фотографий?")


@logger.catch()
@bot.callback_query_handler(func=lambda call: 'start_process', state=HotelInfoState.hotels_list)
def get_hotels_list(call: CallbackQuery) -> None:
    """
    Функция получения списка отелей.
    :param call: CallbackQuery
    :return: None
    """
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        bot.send_message(call.message.chat.id, "Ищу отели...")
        logger.info("Бот начал поиск подходящих отелей.")
        # установка даты заезда в загрузку для поиска
        date_check_in = date(int(data_info["check_in_date"][:4]),
                             int(data_info["check_in_date"][5:7]),
                             int(data_info["check_in_date"][8:]))
        # установка даты выезда в загрузку для поиска
        date_check_out = date(int(data_info["check_out_date"][:4]),
                              int(data_info["check_out_date"][5:7]),
                              int(data_info["check_out_date"][8:]))
        data_info["nights"] = date_check_out - date_check_in  # установка количества ночей в загрузку для поиска

        # установка количества и возраста детей в загрузку для поиска
        children = []
        if "children_age" in data_info.keys():
            for i in data_info["children_age"].keys():
                children.append({"age": data_info["children_age"][i]})

        # установка минимальной и максимальной цен в загрузку для поиска 
        price_filter = {}
        if "price" in data_info.keys() and isinstance(data_info["price"], list):
            price_filter = {
                "max": data_info["price"][1],
                "min": data_info["price"][0]
            }

        # установка сортировки в загрузку для поиска
        if data_info['command'] == '/lowprice':
            sort = "PRICE_LOW_TO_HIGH"
        elif data_info['command'] == '/highprice':
            sort = "PRICE_HIGH_TO_LOW"
        elif data_info['command'] == '/bestdeal':
            sort = "DISTANCE"

        # загрузка
        payload = {
            "currency": "USD",
            "eapid": 1,
            "locale": "ru_RU",
            "siteId": 300000001,
            "destination": {"regionId": str(data_info["city_id"])},
            "checkInDate": {
                "day": int(data_info["check_in_date"][8:]),
                "month": int(data_info["check_in_date"][5:7]),
                "year": int(data_info["check_in_date"][:4])},
            "checkOutDate": {
                "day": int(data_info["check_out_date"][8:]),
                "month": int(data_info["check_out_date"][5:7]),
                "year": int(data_info["check_out_date"][:4])},
            "rooms": [
                {
                    "adults": data_info["adults"],
                    "children": children
                }
            ],
            "resultsStartingIndex": 0,
            "resultsSize": 200,
            "sort": sort,
            "filters": {
                "availableFilter": "SHOW_AVAILABLE_ONLY",
                "price": price_filter
            }
        }

        # получение ответа от API в память бота
        data_info["dict_hotels_answer"] = api_hotels_list.get_hotels_list(payload, data_info["nights"],
                                                                          data_info["price_bestdeal"],
                                                                          data_info["dest_bestdeal"],
                                                                          data_info["hotels_number"])
        logger.info("Бот завершил поиск подходящих отелей.")

        # определение сортировки ответа в памяти бота
        if sort == "PRICE_HIGH_TO_LOW":
            data_info["dict_hotels_answer"] = dict(reversed(sorted(data_info["dict_hotels_answer"].items(),
                                                                   key=lambda item: item[1][1])))
        elif sort == "DISTANCE":
            data_info["dict_hotels_answer"] = dict(sorted(data_info["dict_hotels_answer"].items(),
                                                          key=lambda item: item[1][1]))

        # подключение к базе данных
        with db:
            db.create_tables([User, History])  # создание или подключение к таблицам пользователей и историй поиска
            logger.info("Создание базы данных или подключение к ней.")
            # определение пользователя
            user = [
                {'name': call.from_user.username, 'telegram_id': call.from_user.id}
            ]
            try:
                User.insert(user).execute()  # попытка занести пользователя и его id в телеграме в базу данных
            except BaseException:
                pass

            users = User.select()
            # определение истории пользователя
            history = [
                {
                    'user_id': users.select().where(User.telegram_id == call.from_user.id), 'date_time': datetime.now(),
                    'command': data_info["command"], 'city': data_info["city"], 'city_id': data_info["city_id"],
                    'adults': data_info["adults"], 'children': data_info["children"],
                    'hotel_photos': data_info["hotel_photos"], 'nights': data_info["nights"].days,
                    'check_in_date': data_info["check_in_date"], 'check_out_date': data_info["check_out_date"],
                }
            ]
            History.insert(history).execute()  # попытка занести историю пользователя в базу данных

            # занесение возраста и количества детей, если такие значения не являются пустыми
            if "children_age" in data_info.keys():
                age_list_row = ''
                for age in data_info["children_age"].values():
                    age_list_row += str(age) + "\n"
                for row_history in History.select():
                    if row_history.id == len(History):
                        row_history.exact_age_children = age_list_row
                        row_history.save()

            # занесение минимальной и максимальной цен и минимального и максимального расстояния 
            # от отеля до центра города, если была выбрана команда bestdeal
            if data_info["price_bestdeal"] and data_info["dest_bestdeal"] != 0:
                for row_history in History.select():
                    if row_history.id == len(History):
                        row_history.price_min = data_info["price_bestdeal"][0]
                        row_history.price_max = data_info["price_bestdeal"][1]
                        row_history.dest_min = data_info["dest_bestdeal"][0]
                        row_history.dest_max = data_info["dest_bestdeal"][1]
                        row_history.save()

        # формирование клавиатуры с подходящими отелями, если был найден хоть один ответ по запросу
        if len(data_info["dict_hotels_answer"]) != 0:
            buttons_list = []
            for i_key, i_value in data_info["dict_hotels_answer"].items():
                buttons_list.append(types.InlineKeyboardButton(text=i_key + ' - ' + str(i_value[1]) + '$',
                                                               callback_data=i_value[3]))
            keyboard = types.InlineKeyboardMarkup(user_choice_keyboard.create_button_keyboard(buttons_list))

            bot.send_message(call.message.chat.id, 'Пожалуйста, уточните желаемый отель:', reply_markup=keyboard)
            bot.set_state(call.from_user.id, HotelInfoState.exact_hotel, call.message.chat.id)  # установка бота
            # в состояние уточнения отеля
        else:
            logger.warning("Отелей по запросу пользователя " + call.message.from_user.username + " не было найдено.")
            bot.send_message(call.message.chat.id, "К сожалению, по вашему запросу не было найдено ни одного "
                                                   "подходящего отеля. Пожалуйста, попробуйте запустить поиск отелей "
                                                   "с другими параметрами.")
            bot.send_message(call.message.chat.id, "Работа по поиску отелей завершена. Чтобы запустить новый поиск "
                                                   "или посмотреть историю поиска, выберите соответствующую команду "
                                                   "в меню бота.")
            logger.info("Команда " + data_info["command"] + " завершена.")
            bot.delete_state(call.from_user.id, call.message.chat.id)  # удаление состояние бота для новой команды


@logger.catch()
@bot.callback_query_handler(func=lambda call: True, state=HotelInfoState.exact_hotel)
def get_exact_hotel(call: CallbackQuery) -> None:
    """
    Функция для уточнения отеля.
    :param call: CallbackQuery
    :return: None
    """
    bot.send_message(call.message.chat.id, "Уточняю информацию...")
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        for i_key, i_value in data_info["dict_hotels_answer"].items():
            if i_value[3] == call.data:
                logger.info("Пользователь " + call.message.chat.username + " уточнил отель: " + i_key)
                data_info["hotel"] = i_key
                break

        logger.info("Бот начал поиск информации по уточнённому отелю.")

        # функция уточнения отеля через API
        data_info["hotel_address"], photos_list = api_hotel_info.get_hotel_info(call.data, data_info["hotel_photos"])
        # определение информации для отображения в телеграм-боте
        for key, value in data_info["dict_hotels_answer"].items():
            for deep_key, deep_value in enumerate(value):
                if call.data == deep_value:
                    data_info["url"] = 'https://www.hotels.com/h{}.Hotel-Information'.format(value[3])
                    data_info["night_price"] = str(value[0])
                    data_info["total_price"] = str(value[1])
                    data_info["dest_hotel"] = str(value[2])
                    text_message = f"ВАШИ ДАННЫЕ \n" \
                                   f"Взрослых гостей: {str(data_info['adults'])}\n" \
                                   f"Детей: {str(data_info['children'])}\n" \
                                   f"Город: {data_info['city']}\n" \
                                   f"Вы выбрали следующий отель: {key}\n" \
                                   f"Адрес: {data_info['hotel_address']}\n" \
                                   f"Дата заезда: {data_info['check_in_date']}\n" \
                                   f"Дата выезда: {data_info['check_out_date']}\n" \
                                   f"Стоимость за 1 ночь: {data_info['night_price']}$\n" \
                                   f"Стоимость за {data_info['nights'].days} дней: {data_info['total_price']}$\n" \
                                   f"Расстояние до центра города: {data_info['dest_hotel']} км\n" \
                                   f"Ссылка на отель: {data_info['url']}"
                    bot.send_message(call.message.chat.id, text_message)
                    logger.info("Пользователь " + call.message.chat.username + " получил информацию об отеле.")
                    break
        # поиск и отправка фотографий отеля
        if len(photos_list) != 0:
            count = 0
            for photo in photos_list:
                if count != data_info["hotel_photos"]:
                    count += 1
                    bot.send_message(call.message.chat.id, f"Отправляю {count}-ю фотографию:")
                    bot.send_photo(call.message.chat.id, photo)
                else:
                    logger.info("Пользователь " + call.message.chat.username + " получил все фотографии.")
                    break
        # создание или подключение к базе данных
        with db:
            db.create_tables([User, History])  # создание или подключение к таблицам пользователей и историй поиска
            # определение пользователя
            user = [
                {'name': call.from_user.username, 'telegram_id': call.from_user.id}
            ]
            try:
                User.insert(user).execute()
            except BaseException:
                pass

            # занесение фотографий в базу данных истории поиска
            if len(photos_list) != 0:
                url_list_row = ''
                for url in photos_list:
                    if url == photos_list[-1]:
                        url_list_row += url
                    else:
                        url_list_row += url + "\n"
                for row_history in History.select():
                    if row_history.id == len(History):
                        row_history.urls_photos = url_list_row
                        row_history.save()

            # занесение основной информации в базу данных истории поиска
            for row_history in History.select():
                if row_history.id == len(History):
                    row_history.exact_hotel = data_info["hotel"]
                    row_history.hotel_address = data_info["hotel_address"]
                    row_history.url_hotel = data_info["url"]
                    row_history.night_price = data_info["night_price"]
                    row_history.total_price = data_info["total_price"]
                    row_history.save()

        bot.send_message(call.message.chat.id, "Работа по поиску отелей завершена. Чтобы запустить новый поиск "
                                               "или посмотреть историю поиска, выберите соответствующую команду "
                                               "в меню бота.")
        logger.info("Команда " + data_info["command"] + " завершена.")
    bot.delete_state(call.from_user.id, call.message.chat.id)  # удаление состояния бота для новой команды
