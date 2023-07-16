from peewee import *
from datetime import datetime


db = SqliteDatabase('database/search_history.db')  # определение рабочей базы данных


class BaseModel(Model):  # описание базовой модели
    id = PrimaryKeyField(unique=True)

    class Meta:
        database = db
        order_by = 'id'  # сортировка по id модели


class User(BaseModel):  # описание модели пользователя
    name = CharField()  # ник пользователя в telegram
    telegram_id = IntegerField(unique=True)  # id пользователя в telegram

    class Meta:
        db_table = 'users'


class History(BaseModel):
    user = ForeignKeyField(User, backref="tg_user")  # id пользователя из модели пользователя
    date_time = DateTimeField(default=datetime.now())  # дата и время поиска
    command = CharField()  # команда, использованная пользователем
    city = TextField()  # город, выбранный пользователем
    city_id = IntegerField()  # id города
    exact_hotel = TextField(null=True, default="Не найдено!")  # название выбранного отеля
    hotel_address = TextField(null=True, default=None)  # адрес отеля
    url_hotel = TextField(null=True, default=None)  # ссылка на страницу отеля на сайте hotels.com
    nights = SmallIntegerField()  # количество ночей
    night_price = FloatField(null=True, default=None)  # цена за одну ночь
    total_price = FloatField(null=True, default=None)  # общая цена
    check_in_date = DateField(formats='%Y-%m-%d')  # дата заезда
    check_out_date = DateField(formats='%Y-%m-%d')  # дата выезда
    hotel_photos = SmallIntegerField()  # количество фотографий
    urls_photos = TextField(null=True, default=None)  # ссылки на фотографии
    price_min = FloatField(null=True, default=None)  # минимальная цена
    price_max = FloatField(null=True, default=None)  # максимальная цена
    dest_min = FloatField(null=True, default=None)  # минимальное расстояние от отеля до центра города в км
    dest_max = FloatField(null=True, default=None)  # максимальное расстояние от отеля до центра города в км
    adults = SmallIntegerField()  # количество взрослых
    children = SmallIntegerField()  # количество детей
    exact_age_children = TextField(null=True, default=None)  # возраста детей

    class Meta:
        db_table = 'histories'
