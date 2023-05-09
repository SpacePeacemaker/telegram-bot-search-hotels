import requests
from config_data import config
from loader import bot
from telebot.types import Message, CallbackQuery
from states.search_hotels import HotelInfoState
import json
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import date


class MyStyleCalendar(DetailedTelegramCalendar):
    empty_day_button = ''
    empty_month_button = ''
    empty_year_button = ''


headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": config.RAPID_API_KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}
dict_answer = {}
dict_hotels_answer = {}
check_in = None


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


@bot.message_handler(commands=["highprice"])
def highprice(message: Message) -> None:
    bot.set_state(message.from_user.id, HotelInfoState.city, message.chat.id)
    bot.send_message(message.from_user.id, f"{message.from_user.first_name}, сейчас я поищу отели по самой ВЫСОКОЙ "
                                           f"цене. Сперва мне нужно узнать МЕСТОПОЛОЖЕНИЕ, "
                                           f"в котором мы будем искать отели. Напишите его.")


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
        bot.send_message(message.chat.id, 'Пожалуйста, уточните желаемое МЕСТОПОЛОЖЕНИЕ:', reply_markup=keyboard)
        bot.set_state(message.from_user.id, HotelInfoState.exact_city, message.chat.id)

    else:
        bot.send_message(message.from_user.id, "Такого города нет. Попробуйте снова. Введите город, в котором нужно "
                                               "поискать отели")


@bot.message_handler(state=HotelInfoState.exact_city)
def get_high_exact_city(message: Message) -> None:
    user_id = get_key(dict_answer, message.text)
    bot.send_message(message.from_user.id, "Вы выбрали следующее местоположение - " + message.text)
    bot.send_message(message.from_user.id, "Отлично! Теперь введите КОЛИЧЕСТВО ВЗРОСЛЫХ ГОСТЕЙ (не более 5-ти).")

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["city"] = message.text
        data["city_id"] = user_id

    bot.set_state(message.from_user.id, HotelInfoState.adults, message.chat.id)


@bot.message_handler(state=HotelInfoState.adults)
def get_adults(message: Message) -> None:
    if message.text.isdigit() and 0 < int(message.text) <= 5:
        bot.send_message(message.from_user.id, "Отлично! Теперь введите КОЛИЧЕСТВО ДЕТЕЙ, которые будут гостями "
                                                "отеля (не более 5-ти).")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["adults"] = int(message.text)
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

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["children"] = int(message.text)

    else:
        bot.send_message(message.from_user.id,
                         "Что-то пошло не так. Либо вы ввели число не от 0 до 5, либо вы ввели "
                         "не число. Попробуйте снова: сколько будет детей?")


@bot.message_handler(state=HotelInfoState.exact_age_children)
def get_age_children(message: Message) -> None:
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if "children_age" not in data.keys():
            data["children_age"] = {}

        if message.text.isdigit() and 0 < int(message.text) < 18:
            data["children_age"][len(data["children_age"]) + 1] = int(message.text)
        else:
            bot.send_message(message.from_user.id,
                             "Что-то пошло не так. Либо вы ввели число не от 1 до 17, либо вы ввели "
                             "не число. Попробуйте снова.")

        if data["children"] != len(data["children_age"]):
            bot.send_message(message.from_user.id, f"Введите возраст {len(data['children_age']) + 1}-го ребёнка:")
            bot.set_state(message.from_user.id, HotelInfoState.exact_age_children, message.chat.id)
        else:
            bot.send_message(message.from_user.id, "Отлично! Теперь введите КОЛИЧЕСТВО ОТЕЛЕЙ, которые вы хотите "
                                                   "посмотреть (не более 10-ти).")
            bot.set_state(message.from_user.id, HotelInfoState.hotels_number, message.chat.id)


@bot.message_handler(state=HotelInfoState.hotels_number)
def get_number_hotels(message: Message) -> None:
    if message.text.isdigit() and 0 < int(message.text) <= 10:
        bot.send_message(message.from_user.id, "Отлично! Теперь выберите ДАТУ ЗАЕЗДА.")
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["hotels_number"] = int(message.text)
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

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["check_in_date"] = str(result_one)   # форма записи: yyyy-mm-dd

        calendar_two, step_two = DetailedTelegramCalendar(calendar_id=2,
                                                          locale="ru",
                                                          min_date=result_one).build()
        bot.send_message(call.message.chat.id, f"Выберите {LSTEP[step_two]}", reply_markup=calendar_two)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2), state=HotelInfoState.check_out_date)
def cal_out(call: CallbackQuery) -> None:
    with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
        result_two, key_two, step_two = DetailedTelegramCalendar(calendar_id=2,
                                                                 locale="ru",
                                                                 min_date=date
                                                                 (int(data["check_in_date"][:4]),
                                                                  int(data["check_in_date"][5:7]),
                                                                  int(data["check_in_date"][8:]) + 1))\
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

        with bot.retrieve_data(call.from_user.id, call.message.chat.id) as data:
            data["check_out_date"] = str(result_two)   # форма записи: yyyy-mm-dd
            data["hotels_photos"] = 0

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=False, one_time_keyboard=True)
        keyboard.add(types.KeyboardButton(text='Да'))
        keyboard.add(types.KeyboardButton(text='Нет'))
        bot.send_message(call.message.chat.id, 'Отлично! Теперь подскажите, нужны ли вам ФОТОГРАФИИ?',
                         reply_markup=keyboard)


@bot.message_handler(state=HotelInfoState.hotel_photos)
def get_photos(message: Message) -> None:
    if message.text == 'Да':
        bot.send_message(message.from_user.id, "Сколько фотографий вам нужно? (не больше 5-ти)")
        bot.set_state(message.from_user.id, HotelInfoState.exact_photos, message.chat.id)


@bot.message_handler(state=HotelInfoState.exact_photos)
def get_exact_photos(message: Message) -> None:
    if message.text.isdigit() and 0 < int(message.text) <= 5:
        url_hotels = "properties/v2/list"
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["hotels_photos"] = int(message.text)

            date_check_in = date(int(data["check_in_date"][:4]),
                                 int(data["check_in_date"][5:7]),
                                 int(data["check_in_date"][8:]))
            date_check_out = date(int(data["check_out_date"][:4]),
                                  int(data["check_out_date"][5:7]),
                                  int(data["check_out_date"][8:]))
            data["nights"] = date_check_out - date_check_in
            children = []
            if "children_age" in data.keys():
                for i in data["children_age"].keys():
                    children.append({"age": data["children_age"][i]})

            payload = {
                "currency": "USD",
                "eapid": 1,
                "locale": "ru_RU",
                "siteId": 300000001,
                "destination": {"regionId": str(data["city_id"])},
                "checkInDate": {
                    "day": int(data["check_in_date"][8:]),
                    "month": int(data["check_in_date"][5:7]),
                    "year": int(data["check_in_date"][:4])},
                "checkOutDate": {
                    "day": int(data["check_out_date"][8:]),
                    "month": int(data["check_out_date"][5:7]),
                    "year": int(data["check_out_date"][:4])},
                "rooms": [
                    {
                        "adults": data["adults"],
                        "children": children
                    }
                ],
                "resultsStartingIndex": 0,
                "resultsSize": data["hotels_number"],
                "sort": "PRICE_HIGH_TO_LOW",
                "filters": {
                    "availableFilter": "SHOW_AVAILABLE_ONLY"
                }
            }

        response = api_request(url_hotels, payload, "POST")
        dict_hotels = json.loads(response)
        id_answer = ""
        name_answer = ""
        price_answer = 0.0

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
                                elif l_key == 'price':
                                    for m_value in l_value.values():
                                        if isinstance(m_value, dict):
                                            for n_key, n_value in m_value.items():
                                                if n_key == 'amount':
                                                    price_answer = n_value * data["nights"].days
                                                    break
                                            break
                                if id_answer != "" and name_answer != "" and price_answer != 0.0:
                                    break
                            dict_hotels_answer[name_answer] = [round(price_answer, 2), id_answer]
                            name_answer = ""
                            id_answer = ""
                            price_answer = 0.0
                    if dict_hotels_answer != {}:
                        break

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=False, one_time_keyboard=True)
        for i_key, i_value in dict_hotels_answer.items():
            keyboard.add(types.KeyboardButton(text=i_key + ' ' + str(i_value[0]) + '$'))
        bot.send_message(message.chat.id, 'Пожалуйста, уточните желаемый отель:', reply_markup=keyboard)
        bot.set_state(message.from_user.id, HotelInfoState.exact_hotel, message.chat.id)

    else:
        bot.send_message(message.from_user.id,
                         "Что-то пошло не так. Либо вы ввели число не от 1 до 5, либо вы ввели "
                         "не число. Попробуйте снова: сколько вам нужно фотографий?")


@bot.message_handler(state=HotelInfoState.exact_hotel)
def get_exact_hotel(message: Message) -> None:
    url_photo = "properties/v2/detail"
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        for i_key, i_value in dict_hotels_answer.items():
            if message.text.startswith(i_key):
                exact_hotel_id = i_value[1]
                bot.send_message(message.from_user.id, "Вы выбрали следующий отель: " + i_key)
                bot.send_message(message.from_user.id,
                                 f"Его стоимость за {data['nights'].days} дней: " + str(i_value[0]))
                break
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

        for value in dict_photos.values():
            for i_value in value.values():
                for j_key, j_value in i_value.items():
                    if j_key == 'propertyGallery':
                        for k_key, k_value in j_value.items():
                            if k_key == "images":
                                for l_value in k_value:
                                    if count != data["hotels_photos"]:
                                        for m_key, m_value in l_value.items():
                                            if m_key == "image":
                                                for n_key, n_value in m_value.items():
                                                    if n_key == "url":
                                                        count += 1
                                                        bot.send_message(message.chat.id,
                                                                         f"Отправляю {count}-ю фотографию:")
                                                        bot.send_message(message.chat.id, n_value)
                                                        break
                                    else:
                                        break
