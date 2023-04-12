import requests
import json


def get_key(d, user_value):
	for k, v in d.items():
		if v == user_value:
			return k


city = input('Введите город для поиска: ')
url_city = "https://hotels4.p.rapidapi.com/locations/v3/search"
querystring = {"q": city, "locale": "ru_RU"}
headers = {
	"X-RapidAPI-Key": "b78b4d889amsh24119c756aecdb8p1172eajsn89dc55435fdf",
	"X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}

response = requests.request("GET", url_city, headers=headers, params=querystring)
dict_response = json.loads(response.text)
dict_answer = {}

for key, value in dict_response.items():
	if key == 'sr':
		for i_dict in value:
			for i_key, i_value in i_dict.items():
				if i_key == 'gaiaId':
					new_key = i_value
				elif i_key == 'type':
					if i_value not in ('CITY', 'NEIGHBORHOOD', 'MULTIREGION'):
						new_key = None
				elif i_key == 'regionNames' and new_key is not None:
					for j_key, j_value in i_value.items():
						if j_key == 'fullName':
							dict_answer[new_key] = j_value
							break


for i_key, i_value in dict_answer.items():
	print(i_key, '-', i_value)

user_choice = ''
while user_choice == '':
	user_choice = input('Пожалуйста, выберите из списка выше место, где будем искать отели: ')
	if user_choice not in dict_answer.values():
		user_choice = ''
	else:
		user_id = get_key(dict_answer, user_choice)

day_in = int(input('Введите день заезда: '))
month_in = int(input('Введите месяц заезда: '))
year_in = int(input('Введите год заезда: '))
day_out = int(input('Введите день выезда: '))
month_out = int(input('Введите месяц выезда: '))
year_out = int(input('Введите год выезда: '))
adults = int(input('Сколько будет взрослых: '))
children = int(input('Сколько будет детей: '))
if children > 0:
	children_ages = []
	for i_child in range(0, children):
		age = int(input(f'Введите возраст {i_child + 1}-го ребёнка: '))
		children_ages.append(age)
user_price = ''
while user_price == '':
	choice_price = int(input('Как показывать отели? 1 - сначала минимальные цены, 2 - сначала максимальные цены\n'))
	if choice_price == 1:
		user_price = 'PRICE_LOW_TO_HIGH'
	elif choice_price == 2:
		user_price = 'PRICE_HIGH_TO_LOW'
	else:
		print('Вы выбрали неверную сортировку цены. Пожалуйста, попробуйте снова.')

url_hotels = "https://hotels4.p.rapidapi.com/properties/v2/list"
payload = {
	'currency': 'USD',
	'eapid': 1,
	'locale': 'ru_RU',
	'siteId': 300000001,
	'destination': {
		'regionId': str(user_id)
	},
	'checkInDate': {'day': day_in, 'month': month_in, 'year': year_in},
	'checkOutDate': {'day': day_out, 'month': month_out, 'year': year_out},
	'rooms': [
		{
			'adults': adults
		}
	],
	'resultsStartingIndex': 0,
	'resultsSize': 10,
	'sort': 'PRICE_HIGH_TO_LOW',
	'filters': {
		'availableFilter': 'SHOW_AVAILABLE_ONLY'
	}
}
headers = {
	"content-type": "application/json",
	"X-RapidAPI-Key": "b78b4d889amsh24119c756aecdb8p1172eajsn89dc55435fdf",
	"X-RapidAPI-Host": "hotels4.p.rapidapi.com"
}

response = requests.request("POST", url_hotels, json=payload, headers=headers)

dict_hotels = json.loads(response.text)
dict_hotels_answer = {}
id_answer = None
name_answer = None

for value in dict_hotels.values():
	for i_value in value.values():
		for j_key, j_value in i_value.items():
			if j_key == 'properties':
				for k_dict in j_value:
					while not (id_answer or name_answer):
						for l_key, l_value in k_dict.items():
							if l_key == 'id':
								id_answer = l_value
							elif l_key == 'name':
								name_answer = l_value
					dict_hotels_answer[name_answer] = id_answer
					name_answer = None
					id_answer = None

for i_key, i_value in dict_hotels_answer.items():
	print(i_key, '-', i_value)
