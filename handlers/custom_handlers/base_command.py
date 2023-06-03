import json
from datetime import date

import requests
from telebot import types
from telebot.types import Message, CallbackQuery
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from config_data import config
from loader import bot
from states.search_hotels import HotelInfoState


class MyStyleCalendar(DetailedTelegramCalendar):
    empty_day_button = ""
    empty_month_button = ""
    empty_year_button = ""


LSTEP = {'y': 'год', 'm': 'месяц', 'd': 'день'}
headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": config.RAPID_API_KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}


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
            json=params,
            headers=headers,
            timeout=15
        )
        if response.status_code == requests.codes.ok:
            return response.text
    except TypeError:
        print("Ошибка!")


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def price(message: Message) -> None:
    bot.set_state(message.from_user.id, HotelInfoState.command, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        data_info["command"] = message.text
        if message.text == '/lowprice':
            sort_message = "САМОЙ НИЗКОЙ"
        elif message.text == '/highprice':
            sort_message = "САМОЙ ВЫСОКОЙ"
        elif message.text == '/bestdeal':
            sort_message = "УСТАНОВЛЕННЫМИ ВАМИ РАССТОЯНИЮ ДО ЦЕНТРА ГОРОДА И"

        bot.set_state(message.from_user.id, HotelInfoState.city, message.chat.id)
        bot.send_message(message.from_user.id, f"{message.from_user.first_name}, сейчас я поищу отели по "
                         + sort_message + f" ЦЕНЕ. Сперва мне нужно узнать МЕСТОПОЛОЖЕНИЕ,"
                                          f" в котором мы будем искать отели. Напишите его.")


@bot.message_handler(state=HotelInfoState.city)
def get_city(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        data_info["dict_answer"] = {}
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
                                        data_info["dict_answer"][new_key] = j_value
                                        break

            keyboard = types.InlineKeyboardMarkup()
            for i_key, i_value in data_info["dict_answer"].items():
                keyboard.add(types.InlineKeyboardButton(text=i_value, callback_data=i_key))
            bot.send_message(message.chat.id, 'Пожалуйста, уточните желаемое МЕСТОПОЛОЖЕНИЕ:', reply_markup=keyboard)
            bot.set_state(message.from_user.id, HotelInfoState.exact_city, message.chat.id)

        else:
            bot.send_message(message.from_user.id, "Такого города нет. Попробуйте снова. Введите город, в котором нужно"
                                                   " поискать отели")


@bot.callback_query_handler(func=lambda call: True, state=HotelInfoState.exact_city)
def get_exact_city(call: CallbackQuery) -> None:
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        for hotel_key, hotel_value in data_info["dict_answer"].items():
            if hotel_key == call.data:
                bot.send_message(call.message.chat.id, "Вы выбрали следующее местоположение - " + hotel_value)
                bot.send_message(call.message.chat.id, "Отлично! Теперь введите "
                                                    "КОЛИЧЕСТВО ВЗРОСЛЫХ ГОСТЕЙ (не более 5-ти).")

                data_info["city"] = hotel_value
                data_info["city_id"] = call.data

                bot.set_state(call.from_user.id, HotelInfoState.adults, call.message.chat.id)


@bot.message_handler(state=HotelInfoState.adults)
def get_adults(message: Message) -> None:
    if message.text.isdigit() and 0 < int(message.text) <= 5:
        bot.send_message(message.from_user.id, "Отлично! Теперь введите КОЛИЧЕСТВО ДЕТЕЙ, которые будут гостями "
                                                "отеля (не более 5-ти).")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
            data_info["adults"] = int(message.text)
        bot.set_state(message.from_user.id, HotelInfoState.children, message.chat.id)
    else:
        bot.send_message(message.from_user.id, "Что-то пошло не так. Либо вы ввели число не от 1 до 5, либо вы ввели "
                                               "не число. Попробуйте снова: сколько будет взрослых гостей?")


@bot.message_handler(state=HotelInfoState.children)
def get_children(message: Message) -> None:
    if message.text.isdigit() and 0 <= int(message.text) <= 5:
        if int(message.text) == 0:
            bot.send_message(message.from_user.id, "Отлично! Теперь введите КОЛИЧЕСТВО ОТЕЛЕЙ, которые вы хотите "
                                                   "посмотреть (не более 10-ти).")
            bot.set_state(message.from_user.id, HotelInfoState.hotels_number, message.chat.id)
        elif 1 <= int(message.text) <= 5:
            bot.send_message(message.from_user.id, "Отлично! Теперь вам нужно уточнить ВОЗРАСТ детей.")
            bot.send_message(message.from_user.id, "Введите возраст 1-го ребёнка:")
            bot.set_state(message.from_user.id, HotelInfoState.exact_age_children, message.chat.id)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
            data_info["children"] = int(message.text)

    else:
        bot.send_message(message.from_user.id,
                         "Что-то пошло не так. Либо вы ввели число не от 0 до 5, либо вы ввели "
                         "не число. Попробуйте снова: сколько будет детей?")


@bot.message_handler(state=HotelInfoState.exact_age_children)
def get_age_children(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
        if "children_age" not in data_info.keys():
            data_info["children_age"] = {}

        if message.text.isdigit() and 0 < int(message.text) < 18:
            data_info["children_age"][len(data_info["children_age"]) + 1] = int(message.text)
        else:
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Либо вы ввели число не от 1 до 17, либо вы ввели "
                             "не число. Попробуйте снова.")

        if data_info["children"] != len(data_info["children_age"]):
            bot.send_message(message.from_user.id, f"Введите возраст {len(data_info['children_age']) + 1}-го ребёнка:")
            bot.set_state(message.from_user.id, HotelInfoState.exact_age_children, message.chat.id)
        else:
            bot.send_message(message.from_user.id, "Отлично! Теперь введите КОЛИЧЕСТВО ОТЕЛЕЙ, которые вы хотите "
                                                   "посмотреть (не более 10-ти).")
            bot.set_state(message.from_user.id, HotelInfoState.hotels_number, message.chat.id)


@bot.message_handler(state=HotelInfoState.hotels_number)
def get_number_hotels(message: Message) -> None:
    if message.text.isdigit() and 0 < int(message.text) <= 10:
        bot.send_message(message.from_user.id, "Отлично! Теперь выберите ДАТУ ЗАЕЗДА.")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
            data_info["hotels_number"] = int(message.text)
        calendar_one, step_one = DetailedTelegramCalendar(calendar_id=1, locale="ru", min_date=date.today()).build()
        bot.send_message(message.chat.id,
                         f"Выберите {LSTEP[step_one]}",
                         reply_markup=calendar_one)
        bot.set_state(message.from_user.id, HotelInfoState.check_in_date, message.chat.id)
    else:
        bot.send_message(message.from_user.id, "Что-то пошло не так. Либо вы ввели число не от 1 до 10, либо вы ввели "
                                               "не число. Попробуйте снова: сколько нужно вывести отелей?")


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1), state=HotelInfoState.check_in_date)
def cal_in(call: CallbackQuery) -> None:
    result_one, key_one, step_one = DetailedTelegramCalendar(calendar_id=1,
                                                             locale="ru",
                                                             min_date=date.today()).process(call.data)
    if not result_one and key_one:
        bot.edit_message_text(f"Выберите {LSTEP[step_one]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key_one)
    elif result_one:
        bot.edit_message_text(f"Вы выбрали {result_one}",
                              call.message.chat.id,
                              call.message.message_id)

        bot.send_message(call.message.chat.id, "Отлично! Теперь выберите ДАТУ ВЫЕЗДА.")
        bot.set_state(call.from_user.id, HotelInfoState.check_out_date, call.message.chat.id)

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
            data_info["check_in_date"] = str(result_one)   # форма записи: yyyy-mm-dd

        calendar_two, step_two = DetailedTelegramCalendar(calendar_id=2,
                                                          locale="ru",
                                                          min_date=result_one).build()
        bot.send_message(call.message.chat.id, f"Выберите {LSTEP[step_two]}", reply_markup=calendar_two)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2), state=HotelInfoState.check_out_date)
def cal_out(call: CallbackQuery) -> None:
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        result_two, key_two, step_two = DetailedTelegramCalendar(calendar_id=2,
                                                                 locale="ru",
                                                                 min_date=date
                                                                 (int(data_info["check_in_date"][:4]),
                                                                  int(data_info["check_in_date"][5:7]),
                                                                  int(data_info["check_in_date"][8:]) + 1))\
                                                                 .process(call.data)
    if not result_two and key_two:
        bot.edit_message_text(f"Выберите {LSTEP[step_two]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key_two)
    elif result_two:
        bot.edit_message_text(f"Вы выбрали {result_two}",
                              call.message.chat.id,
                              call.message.message_id)

        bot.set_state(call.from_user.id, HotelInfoState.hotel_photos, call.message.chat.id)

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
            data_info["check_out_date"] = str(result_two)   # форма записи: yyyy-mm-dd
            data_info["hotels_photos"] = 0

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Да', callback_data='yes'))
        keyboard.add(types.InlineKeyboardButton(text='Нет', callback_data='no'))
        bot.send_message(call.message.chat.id, 'Отлично! Теперь подскажите, нужны ли вам ФОТОГРАФИИ?',
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True, state=HotelInfoState.hotel_photos)
def get_photos(call: CallbackQuery) -> None:
    if call.data == 'yes':
        bot.send_message(call.message.chat.id, "Сколько фотографий вам нужно? (не больше 5-ти)")
        bot.set_state(call.from_user.id, HotelInfoState.exact_photos, call.message.chat.id)


@bot.message_handler(state=HotelInfoState.exact_photos)
def get_exact_photos(message: Message) -> None:
    if message.text.isdigit() and 0 < int(message.text) <= 5:
        url_hotels = "properties/v2/list"
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data_info:
            data_info["hotels_photos"] = int(message.text)

            date_check_in = date(int(data_info["check_in_date"][:4]),
                                 int(data_info["check_in_date"][5:7]),
                                 int(data_info["check_in_date"][8:]))
            date_check_out = date(int(data_info["check_out_date"][:4]),
                                  int(data_info["check_out_date"][5:7]),
                                  int(data_info["check_out_date"][8:]))
            data_info["nights"] = date_check_out - date_check_in
            children = []
            if "children_age" in data_info.keys():
                for i in data_info["children_age"].keys():
                    children.append({"age": data_info["children_age"][i]})

            if data_info['command'] == '/lowprice':
                sort = "PRICE_LOW_TO_HIGH"
            elif data_info['command'] == '/highprice':
                sort = "PRICE_HIGH_TO_LOW"
            elif data_info['command'] == '/bestdeal':
                sort = "DISTANCE"

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
                "resultsSize": data_info["hotels_number"],
                "sort": sort,
                "filters": {
                    "availableFilter": "SHOW_AVAILABLE_ONLY"
                }
            }

        response = api_request(url_hotels, payload, "POST")
        dict_hotels = json.loads(response)
        id_answer = ""
        name_answer = ""
        night_price_answer = 0.0
        price_answer = 0.0
        distance_answer = 0.0
        data_info["dict_hotels_answer"] = {}

        for value in dict_hotels.values():
            for i_value in value.values():
                for j_key, j_value in i_value.items():
                    if j_key == 'properties':
                        for k_dict in j_value:
                            for l_key, l_value in k_dict.items():
                                if l_key == 'id':
                                    id_answer = l_value
                                elif l_key == 'name':
                                    name_answer = l_value
                                elif l_key == 'destinationInfo':
                                    for m1_key, m1_value in l_value.items():
                                        if m1_key == "distanceFromDestination":
                                            for n1_key, n1_value in m1_value.items():
                                                if n1_key == "value":
                                                    distance_answer = round(n1_value * 1.609, 2)
                                                    break
                                elif l_key == 'price':
                                    for m1_value in l_value.values():
                                        if isinstance(m1_value, dict):
                                            for n1_key, n1_value in m1_value.items():
                                                if n1_key == 'amount':
                                                    night_price_answer = round(n1_value, 2)
                                                    price_answer = round(n1_value * data_info["nights"].days, 2)
                                                    break
                                            break
                                if id_answer != "" and name_answer != "" and price_answer != 0.0 \
                                        and distance_answer != 0.0:
                                    break
                            data_info["dict_hotels_answer"][name_answer] = [night_price_answer,
                                                                       price_answer,
                                                                       distance_answer,
                                                                       id_answer]
                            name_answer = ""
                            id_answer = ""
                            price_answer = 0.0
                            distance_answer = 0.0
                    if data_info["dict_hotels_answer"] != {}:
                        break

        keyboard = types.InlineKeyboardMarkup()

        if sort == "PRICE_HIGH_TO_LOW":
            data_info["dict_hotels_answer"] = dict(reversed(sorted(data_info["dict_hotels_answer"].items(),
                                                                   key=lambda item: item[1][1])))

        for i_key, i_value in data_info["dict_hotels_answer"].items():
            keyboard.add(types.InlineKeyboardButton(text=i_key + ' - ' + str(i_value[1]) + '$',
                                                    callback_data=i_value[3]))
        bot.send_message(message.chat.id, 'Пожалуйста, уточните желаемый отель:', reply_markup=keyboard)
        bot.set_state(message.from_user.id, HotelInfoState.exact_hotel, message.chat.id)

    else:
        bot.send_message(message.from_user.id,
                         "Что-то пошло не так. Либо вы ввели число не от 1 до 5, либо вы ввели "
                         "не число. Попробуйте снова: сколько вам нужно фотографий?")


@bot.callback_query_handler(func=lambda call: True, state=HotelInfoState.exact_hotel)
def get_exact_hotel(call: CallbackQuery) -> None:
    url_photo = "properties/v2/detail"
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data_info:
        exact_hotel_id = call.data
        payload = {
            "currency": "USD",
            "eapid": 1,
            "locale": "ru_RU",
            "siteId": 300000001,
            "propertyId": str(exact_hotel_id)
        }
        response = api_request(url_photo, payload, "POST")
        dict_photos = json.loads(response)
        count = 0

        for my_value in dict_photos.values():
            for i_value in my_value.values():
                for j_key, j_value in i_value.items():
                    if j_key == "summary":
                        for k1_key, k1_value in j_value.items():
                            if k1_key == "location":
                                for l1_key, l1_value in k1_value.items():
                                    if l1_key == "address":
                                        for m1_key, m1_value in l1_value.items():
                                            if m1_key == "addressLine":
                                                data_info["hotel_address"] = m1_value
                                                for key, value in data_info["dict_hotels_answer"].items():
                                                    for deep_key, deep_value in enumerate(value):
                                                        if call.data == deep_value:
                                                            url = 'https://www.hotels.com/h{}.Hotel-Information'.\
                                                                format(value[3])
                                                            text_message = f"Вы выбрали следующий отель: {key}\n" \
                                                                           f"Адрес: {data_info['hotel_address']}\n" \
                                                                           f"Дата заезда: " \
                                                                           f"{data_info['check_in_date']}\n" \
                                                                           f"Дата выезда: " \
                                                                           f"{data_info['check_out_date']}\n" \
                                                                           f"Стоимость за 1 ночь: {str(value[0])}$\n" \
                                                                           f"Стоимость за " \
                                                                           f"{data_info['nights'].days} дней:" \
                                                                           f" {str(value[1])}$\n" \
                                                                           f"Расстояние до центра города: " \
                                                                           f"{str(value[2])} км\nСсылка на отель: " \
                                                                           f"{url}"
                                                            bot.send_message(call.message.chat.id, text_message)
                                                            break
                                                break
                    elif j_key == 'propertyGallery' and data_info["hotels_photos"] != 0:
                        for k2_key, k2_value in j_value.items():
                            if k2_key == "images":
                                for l2_value in k2_value:
                                    if count != data_info["hotels_photos"]:
                                        for m2_key, m2_value in l2_value.items():
                                            if m2_key == "image":
                                                for n2_key, n2_value in m2_value.items():
                                                    if n2_key == "url":
                                                        count += 1
                                                        bot.send_message(call.message.chat.id,
                                                                         f"Отправляю {count}-ю фотографию:")
                                                        bot.send_photo(call.message.chat.id, n2_value)
                                                        break
                                    else:
                                        break
    bot.delete_state(call.from_user.id, call.message.chat.id)
