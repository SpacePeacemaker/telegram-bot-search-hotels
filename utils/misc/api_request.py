import requests
from config_data import config

# заголовки для запроса
headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": config.RAPID_API_KEY,
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}


def api_request(method_endswith: str, params, method_type: str):
    """
    Функция взаимодействия с API.
    :param method_endswith: str
    :param params:
    :param method_type: str
    :return:
    """
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


def get_request(url: str, params) -> str:
    """
    GET-функция запроса к API.
    :param url:
    :param params:
    :return: str
    """
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


def post_request(url: str, params) -> str:
    """
    POST-функция запроса к API.
    :param url: str
    :param params:
    :return: str
    """
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
