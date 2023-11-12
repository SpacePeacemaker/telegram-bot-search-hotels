import json
from datetime import date

from utils.misc.api_request import api_request


def get_hotels_list(user_payload: dict, nights: date, price: list, dest: list, hotels_number: int) -> dict:
    """
    Функция для получения списка отелей.
    :param user_payload: dict
    :param nights: date
    :param price: list
    :param dest: list
    :param hotels_number: int
    :return: dict
    """
    url_hotels = "properties/v2/list"
    payload = user_payload
    response = api_request(url_hotels, payload, "POST")  # получение ответа от API

    if response:  # если от API пришёл непустой ответ
        dict_hotels = json.loads(response)  # расшифровка ответа из json
        hotels = dict()
        counter = 0

        for hotel in dict_hotels["data"]["propertySearch"]["properties"]:  # вытаскиваем необходимую информацию об отеле
            hotel_id = hotel["id"]
            hotel_name = hotel["name"]
            hotel_night_price = round(hotel["price"]["lead"]["amount"], 2)
            hotel_total_price = round(hotel_night_price * nights.days, 2)
            hotel_distance = hotel["destinationInfo"]["distanceFromDestination"]["value"]
            if (price == 0 or price[0] <= hotel_total_price <= price[1]) and \
                    (dest == 0 or (dest[0] <= round(hotel_distance, 2) <= dest[1])):
                hotels[hotel_name] = [hotel_night_price, hotel_total_price, hotel_distance, hotel_id]
                counter += 1
            if counter == hotels_number:
                break
        return hotels
    else:
        return None
