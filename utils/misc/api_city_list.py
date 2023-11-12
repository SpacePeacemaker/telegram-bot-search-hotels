import json
from utils.misc.api_request import api_request


def get_city_list(city: str) -> dict:
    """
    Функция для получения списка подходящих городов.
    :param city: str
    :return: dict
    """
    url_city = "locations/v3/search"
    querystring = {
        "q": city,
        "locale": "ru_RU"
    }
    response = api_request(url_city, querystring, "GET")  # получение ответа от API

    if response:  # если от API пришёл непустой ответ
        cities = dict()
        result = json.loads(response)  # расшифровка ответа из json
        for dest in result["sr"]:
            if dest["type"] in "CITY, NEIGHBORHOOD, MULTIREGION":
                cities[dest["gaiaId"]] = dest["regionNames"]["fullName"]
        return cities
    else:
        return None
