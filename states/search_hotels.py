from telebot.handler_backends import State, StatesGroup


class HotelInfoState(StatesGroup):
    city = State()
    exact_city = State()
    hotels_number = State()
    adults = State()
    check_in_date = State()
    check_out_date = State()
    hotel_photos = State()
    exact_hotel = State()
