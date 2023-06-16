import json
from utils.misc.api_request import api_request


def get_city_list(city: str) -> dict:
    """

    :param city:
    :return:
    """
    url_city = "locations/v3/search"
    querystring = {
        "q": city,
        "locale": "ru_RU"
    }
    response = api_request(url_city, querystring, "GET")

    if response:
        cities = dict()
        result = json.loads(response)
        for dest in result["sr"]:
            if dest["type"] in "CITY, NEIGHBORHOOD, MULTIREGION":
                destination = dest["regionNames"]["fullName"]
                cities[dest["gaiaId"]] = destination
        return cities
    else:
        return None
