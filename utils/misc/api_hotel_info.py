import json
from utils.misc.api_request import api_request


def get_hotel_info(exact_hotel_id, number_photos):
    url_photo = "properties/v2/detail"
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": str(exact_hotel_id)
    }
    response = api_request(url_photo, payload, "POST")

    if response:
        info_hotel = json.loads(response)
        url_photos_list = []
        count = 0

        if number_photos != 0:
            for photo in info_hotel["data"]["propertyInfo"]["propertyGallery"]["images"]:
                if count != number_photos:
                    count += 1
                    url_photos_list.append(photo["image"]["url"])
                else:
                    break

        return info_hotel["data"]["propertyInfo"]["summary"]["location"]["address"]["addressLine"], url_photos_list
    else:
        return None
