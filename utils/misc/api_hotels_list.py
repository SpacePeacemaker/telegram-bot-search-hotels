import json
from utils.misc.api_request import api_request


def get_hotel_list(user_payload, nights, price, dest, hotels_number):
    url_hotels = "properties/v2/list"
    payload = user_payload
    response = api_request(url_hotels, payload, "POST")

    if response:
        dict_hotels = json.loads(response)
        hotels = dict()
        counter = 0

        for hotel in dict_hotels["data"]["propertySearch"]["properties"]:
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
