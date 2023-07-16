from telebot.handler_backends import State, StatesGroup


class HotelInfoState(StatesGroup):  # создание состояний для уточнения поиска отеля
    command = State()  # команда пользователя
    city = State()  # ввод пользователем города
    exact_city = State()  # уточнение города
    price_min = State()  # минимальная цена
    price_max = State()  # максимальная цена
    dest_min = State()  # минимальное расстояние от отеля до центра города
    dest_max = State()  # максимальное расстояние от отеля до центра города
    hotels_number = State()  # количество отелей
    adults = State()  # количество взрослых
    children = State()  # количество детей
    exact_age_children = State()  # уточнение возрастов детей
    check_in_date = State()  # дата заезда
    check_out_date = State()  # дата выезда
    hotel_photos = State()  # уточнение необходимости в фотографиях
    exact_photos = State()  # количество фотографий
    start_process = State()  # запуск поиска процесса
    hotels_list = State()  # вывод списка подходящих отелей
    exact_hotel = State()  # уточнение отеля и вывод детальной информации о нём
