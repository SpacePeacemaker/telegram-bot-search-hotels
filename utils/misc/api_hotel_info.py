import json
from utils.misc.api_request import api_request


def get_hotel_info(exact_hotel_id: int, number_photos: int) -> (str, list):
    """
    Функция для получения информации об отеле.
    :param exact_hotel_id: int
    :param number_photos: int
    :return: str, list
    """
    url_photo = "properties/v2/detail"
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": str(exact_hotel_id)
    }
    response = api_request(url_photo, payload, "POST")  # получение ответа от API

    if response:  # если от API пришёл непустой ответ
        info_hotel = json.loads(response)  # расшифровка ответа из json
        url_photos_list = []
        count = 0

        if number_photos != 0:  # ищем ссылки на фотографии, если требуется
            for photo in info_hotel["data"]["propertyInfo"]["propertyGallery"]["images"]:
                if count != number_photos:
                    count += 1
                    url_photos_list.append(photo["image"]["url"])
                else:
                    break

        return info_hotel["data"]["propertyInfo"]["summary"]["location"]["address"]["addressLine"], url_photos_list
    else:
        return None
