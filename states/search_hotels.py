from telebot.handler_backends import State, StatesGroup


class HotelInfoState(StatesGroup):
    command = State()
    city = State()
    exact_city = State()
    price_min = State()
    price_max = State()
    dest_min = State()
    dest_max = State()
    hotels_number = State()
    adults = State()
    children = State()
    exact_age_children = State()
    check_in_date = State()
    check_out_date = State()
    hotel_photos = State()
    exact_photos = State()
    hotels_list = State()
    exact_hotel = State()
