# from loader import bot
# from states.search_hotels import HotelInfoState
# from telebot.types import Message
# from telebot import types
# import requests
# import re
# import json
# from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
# from config_data import config
#
# #
# # def get_key(d, user_value):
# #     for k, v in d.items():
# #         if v == user_value:
# #             return k
# #
# #
# # def api_request(method_endswith, params, method_type):
# #     url = f'https://hotels4.p.rapidapi.com/{method_endswith}'
# #
# #     if method_type == 'GET':
# #         return get_request(
# #             url=url,
# #             params=params
# #         )
# #     else:
# #         return post_request(
# #             url=url,
# #             params=params
# #         )
# #
# #
# # def get_request(url, params):
# #     try:
# #         response = requests.get(
# #             url,
# #             headers=...,
# #             params=params,
# #             timeout=15
# #         )
# #         if response.status_code == requests.codes.ok:
# #             return response.text
# #     except ...
# #         ...
# #
# #
# # def post_request(url, params):
# #     try:
# #         response = requests.post(
# #             url,
# #             headers=...,
# #             params=params,
# #             timeout=15
# #         )
# #         if response.status_code == requests.codes.ok:
# #             return response.text
# #     except ...
# #         ...
# #
# #
#
#
# def request_to_api(url, queryheaders, querystring):
#     try:
#         response = requests.request("GET", url, headers=queryheaders, params=querystring, timeout=10)
#         if response.status_code == requests.codes.ok:
#             return response.text
#     except TypeError:
#         print('Ошибка!')
#
#
# url_city = "https://hotels4.p.rapidapi.com/locations/v3/search"
# headers = {
#     "X-RapidAPI-Key": config.RAPID_API_KEY,
#     "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
# }
#
#
# @bot.message_handler(commands=['lowprice'])
# def lowprice(message: Message) -> None:
#     bot.set_state(message.from_user.id, HotelInfoState.city, message.chat.id)
#     bot.send_message(message.from_user.id, f'{message.from_user.first_name}, сейчас я поищу отели по самой НИЗКОЙ '
#                                            f'цене. Сперва мне нужно узнать город, в котором мы будем искать отели. '
#                                            f'Напишите его.')
#
#
# @bot.message_handler(state=HotelInfoState.city)
# def get_low_city(message: Message) -> None:
#     if message.text.isalpha():
#         querystring = {"query": message.text, "locale": "ru_RU"}
#         response = request_to_api(url_city, headers, querystring)
#         pattern = r'(?<="CITY_GROUP",).+?[\]]'
#         find = re.search(pattern, response)
#         if find:
#             result = json.loads(f"{{{find[0]}}}")
#             bot.send_message(message.from_user.id, 'Отлично! Теперь введите количество отелей, которые вы хотите '
#                                                    'посмотреть (не более 10-ти).')
#             bot.set_state(message.from_user.id, HotelInfoState.hotel_number, message.chat.id)
#
#             with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
#                 data['city'] = message.text
#     else:
#         bot.send_message(message.from_user.id, 'Такого города нет. Попробуйте снова. Введите город, в котором нужно '
#                                                'поискать отели')
#
#
# @bot.message_handler(state=HotelInfoState.dates)
# def get_dates(message: Message) -> None:
#     calendar, step = DetailedTelegramCalendar().build()
#     bot.send_message(message.from_user.id, f'Выберите {LSTEP[step]}', reply_markup=calendar)
#     if message.text.isdigit() and (10 >= int(message.text) > 0):
#         bot.send_message(message.from_user.id, 'Супер! Теперь подскажите, вам нужны фотографии отелей или нет?')
#         bot.set_state(message.from_user.id, HotelInfoState.hotel_photos, message.chat.id)
#
#         with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
#             data['hotel_number'] = int(message.text)
#     else:
#         bot.send_message(message.from_user.id, 'Что-то пошло не так. Либо вы ввели число не от 1 до 10, либо вы ввели'
#                                                'не число. Попробуйте снова: сколько нужно вывести отелей?')
#
#
# @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
# def cal(c):
#     result, key, step = DetailedTelegramCalendar().process(c.data)
#     if not result and key:
#         bot.edit_message_text(f"Выберите {LSTEP[step]}",
#                               c.message.chat.id,
#                               c.message.message_id,
#                               reply_markup=key)
#     elif result:
#         bot.edit_message_text(f"Вы выбрали {result}",
#                               c.message.chat.id,
#                               c.message.message_id)
#     bot.send_message(c.message.from_user.id, 'Супер! Теперь подскажите, вам нужны фотографии отелей или нет?')
#     bot.set_state(c.message.from_user.id, HotelInfoState.hotel_photos, c.message.chat.id)
#
#     with bot.retrieve_data(c.message.from_user.id, c.message.chat.id) as data:
#         data['hotel_number'] = int(c.message.text)
#
#     bot.send_message(c.message.from_user.id, 'Что-то пошло не так. Либо вы ввели число не от 1 до 10, либо вы ввели'
#                                        'не число. Попробуйте снова: сколько нужно вывести отелей?')
#
#
# @bot.message_handler(state=HotelInfoState.hotel_number)
# def get_hotel_number(message: Message) -> None:
#     if message.text.isdigit() and (10 >= int(message.text) > 0):
#         bot.send_message(message.from_user.id, 'Супер! Теперь подскажите, вам нужны фотографии отелей или нет?')
#         bot.set_state(message.from_user.id, HotelInfoState.hotel_photos, message.chat.id)
#
#         with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
#             data['hotel_number'] = int(message.text)
#     else:
#         bot.send_message(message.from_user.id, 'Что-то пошло не так. Либо вы ввели число не от 1 до 10, либо вы ввели'
#                                                'не число. Попробуйте снова: сколько нужно вывести отелей?')
#
#
# @bot.message_handler(state=HotelInfoState.hotel_photos)
# def get_hotel_photos(message: Message) -> None:
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
#     yes = types.KeyboardButton('Да')
#     no = types.KeyboardButton('Нет')
#     markup.add(yes, no)
#     bot.send_message(message.chat.id, 'Нужны фотографии?', reply_markup=markup)
#     user_number = 0
#
#     if message.text == 'Да':
#         bot.send_message(message.from_user.id, 'Сколько? Введите число от 1 до 5:')
#         if message.text.isdigit() and (5 >= int(message.text) > 0):
#             user_number = int(message.text)
#             ...
#         else:
#             bot.send_message(message.from_user.id,
#                              'Что-то пошло не так. Либо вы ввели число не от 1 до 5, либо вы ввели'
#                              'не число. Попробуйте снова: сколько нужно вывести фотографий?')
#
#     with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
#         data['hotel_photos'] = user_number
#
#         text = f'Спасибо за предоставленную информацию. Ваши данные: \n' \
#                f'Город: {data["city"]}\n' \
#                f'Количество отелей: {data["hotel_number"]}\n' \
#                f'Количество фотографий: {data["hotel_photos"]}'
#         bot.send_message(message.from_user.id, text)
