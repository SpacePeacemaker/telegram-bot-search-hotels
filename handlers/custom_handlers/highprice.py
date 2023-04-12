import requests
from config_data import config
from loader import bot
from telebot.types import Message
from states.search_hotels import HotelInfoState
import json
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import date


headers = {
    "X-RapidAPI-Key": config.RAPID_API_KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}
dict_answer = {}


def get_key(d, user_value):
    for k, v in d.items():
        if v == user_value:
            return k


def api_request(method_endswith, params, method_type):
    url = f"https://hotels4.p.rapidapi.com/{method_endswith}"

    if method_type == "GET":
        return get_request(
            url=url,
            params=params
        )
    else:
        return post_request(
            url=url,
            params=params
        )


def get_request(url, params):
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
        if response.status_code == requests.codes.ok:
            return response.text
    except TypeError:
        print("Ошибка!")


def post_request(url, params):
    try:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
        if response.status_code == requests.codes.ok:
            return response.text
    except TypeError:
        print("Ошибка!")


@bot.message_handler(commands=["highprice"])
def highprice(message: Message) -> None:
    bot.set_state(message.from_user.id, HotelInfoState.city, message.chat.id)
    bot.send_message(message.from_user.id, f"{message.from_user.first_name}, сейчас я поищу отели по самой ВЫСОКОЙ "
                                           f"цене. Сперва мне нужно узнать город, в котором мы будем искать отели. "
                                           f"Напишите его.")


@bot.message_handler(state=HotelInfoState.city)
def get_high_city(message: Message) -> None:
    if message.text.isalpha():
        querystring = {"q": message.text, "locale": "ru_RU"}
        url_city = "locations/v3/search"
        response = api_request(url_city, querystring, "GET")
        result = json.loads(response)
        for key, value in result.items():
            if key == "sr":
                for i_dict in value:
                    for i_key, i_value in i_dict.items():
                        if i_key == "gaiaId":
                            new_key = i_value
                        elif i_key == "type":
                            if i_value not in ("CITY", "NEIGHBORHOOD", "MULTIREGION"):
                                new_key = None
                        elif i_key == "regionNames" and new_key is not None:
                            for j_key, j_value in i_value.items():
                                if j_key == "fullName":
                                    dict_answer[new_key] = j_value
                                    break
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=False, one_time_keyboard=True)
        for i_value in dict_answer.values():
            keyboard.add(types.KeyboardButton(text=i_value))
        bot.send_message(message.chat.id, 'Пожалуйста, уточните желаемое местоположение:', reply_markup=keyboard)
        bot.set_state(message.from_user.id, HotelInfoState.exact_city, message.chat.id)

    else:
        bot.send_message(message.from_user.id, "Такого города нет. Попробуйте снова. Введите город, в котором нужно "
                                               "поискать отели")


@bot.message_handler(state=HotelInfoState.exact_city)
def get_high_exact_city(message: Message) -> None:
    user_id = get_key(dict_answer, message.text)
    bot.send_message(message.from_user.id, "Вы выбрали следующее местоположение - " + message.text)
    bot.send_message(message.from_user.id, "Отлично! Теперь введите количество отелей, которые вы хотите "
                                           "посмотреть (не более 10-ти).")
    bot.set_state(message.from_user.id, HotelInfoState.hotels_number, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["city"] = message.text
        data["city_id"] = user_id

    bot.send_message(message.from_user.id, data["city"], data["city_id"])


@bot.message_handler(state=HotelInfoState.hotels_number)
def get_high_hotels(message: Message) -> None:
    if message.text.isdigit() and 0 < int(message.text) <= 10:
        bot.send_message(message.from_user.id, "Отлично! Теперь выберите дату заезда.")
        bot.set_state(message.from_user.id, HotelInfoState.check_in_date, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["hotels_number"] = int(message.text)

        bot.send_message(message.from_user.id, data["hotels_number"])

    else:
        bot.send_message(message.from_user.id, "Что-то пошло не так. Либо вы ввели число не от 1 до 10, либо вы ввели "
                                               "не число. Попробуйте снова: сколько нужно вывести отелей?")


@bot.message_handler(state=HotelInfoState.check_in_date)
def get_high_check_in(message: Message) -> None:
    bot.send_message(message.chat.id, "Дата заезда:")
    calendar, step = DetailedTelegramCalendar(calendar_id=1, locale="ru", min_date=date.today()).build()
    bot.send_message(message.chat.id, f"Выберите {LSTEP[step]}", reply_to_message_id=message.message_id , reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal_in(c):
    result, key, step = DetailedTelegramCalendar(calendar_id=1, locale="ru", min_date=date.today()).process(c.data)
    if not result and key:
        bot.edit_message_text(f"Выберите {LSTEP[step]}",
                              c.message.chat.id,
                              c.message.message_id,
                              reply_markup=key)
    elif result:
        bot.edit_message_text(f"Вы выбрали {result}",
                              c.message.chat.id,
                              c.message.message_id)

        bot.send_message(c.message.chat.id, "Отлично! Теперь выберите дату выезда.")
        bot.set_state(c.message.chat.id, HotelInfoState.check_out_date, c.message.chat.id)

        with bot.retrieve_data(c.message.from_user.id, c.message.chat.id) as data:
            data["check_in_date"] = str(result)   # форма записи: yyyy-mm-dd

        bot.send_message(c.message.from_user.id, data["check_in_date"])


@bot.message_handler(state=HotelInfoState.check_out_date)
def get_high_check_out(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        calendar, step = DetailedTelegramCalendar(calendar_id=2, locale="ru", min_date=data["check_in_date"]).build()
        bot.send_message(message.chat.id, f"Выберите {LSTEP[step]}", reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal_out(c):
    with bot.retrieve_data(c.message.from_user.id, c.message.chat.id) as data:
        result, key, step = DetailedTelegramCalendar(calendar_id=2, locale="ru", min_date=data["check_in_date"]).process(c.data)
        if not result and key:
            bot.edit_message_text(f"Выберите {LSTEP[step]}",
                                c.message.chat.id,
                                c.message.message_id,
                                reply_markup=key)
        elif result:
            bot.edit_message_text(f"Вы выбрали {result}",
                                c.message.chat.id,
                                c.message.message_id)

            keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=False, one_time_keyboard=True)
            keyboard.add(types.KeyboardButton(text='Да'))
            keyboard.add(types.KeyboardButton(text='Нет'))
            bot.send_message(c.message.chat.id, "Отлично! Теперь подскажите, нужны ли вам фотографии.")
            bot.set_state(c.message.chat.id, HotelInfoState.hotel_photos, c.message.chat.id)

            data["check_out_date"] = str(result)   # форма записи: yyyy-mm-dd


@bot.message_handler(state=HotelInfoState.hotel_photos)
def get_high_photos(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["hotels_photos"] = 0
    if message.text == 'Да':
        bot.send_message(message.from_user.id, "Сколько фотографий вам нужно? (не больше 5-ти)")
        if message.text.isdigit() and 0 < int(message.text) <= 5:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data["hotels_photos"] = int(message.text)
        else:
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Либо вы ввели число не от 1 до 5, либо вы ввели "
                             "не число. Попробуйте снова: сколько вам нужно фотографий?")

#     url_hotels = "properties/v2/list"
#     with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
#         payload = {
#             'currency': 'USD',
#             'eapid': 1,
#             'locale': 'ru_RU',
#             'siteId': 300000001,
#             'destination': {
#                 'regionId': data["city_id"]
#             },
#             'checkInDate': {'day': day_in, 'month': month_in, 'year': year_in},
#             'checkOutDate': {'day': day_out, 'month': month_out, 'year': year_out},
#             'rooms': [
#                 {
#                     'adults': adults
#                 }
#             ],
#             'resultsStartingIndex': 0,
#             'resultsSize': 10,
#             'sort': 'PRICE_HIGH_TO_LOW',
#             'filters': {
#                 'availableFilter': 'SHOW_AVAILABLE_ONLY'
#             }
#         }
#         headers = {
#             "content-type": "application/json",
#             "X-RapidAPI-Key": config_data.config.RAPID_API_KEY,
#             "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
#         }
#
#     response = requests.request("POST", url_hotels, json=payload, headers=headers)
#
#     dict_hotels = json.loads(response.text)
#     dict_hotels_answer = {}
#     id_answer = None
#     name_answer = None
#
#     for value in dict_hotels.values():
#         for i_value in value.values():
#             for j_key, j_value in i_value.items():
#                 if j_key == 'properties':
#                     for k_dict in j_value:
#                         while not (id_answer or name_answer):
#                             for l_key, l_value in k_dict.items():
#                                 if l_key == 'id':
#                                     id_answer = l_value
#                                 elif l_key == 'name':
#                                     name_answer = l_value
#                         dict_hotels_answer[name_answer] = id_answer
#                         name_answer = None
#                         id_answer = None
#
#     for i_key, i_value in dict_hotels_answer.items():
#         print(i_key, '-', i_value)

