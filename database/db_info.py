from peewee import *
from datetime import date


db = SqliteDatabase('database/search_history.db')


class BaseModel(Model):
    id = PrimaryKeyField(unique=True)

    class Meta:
        database = db
        order_by = 'id'


class User(BaseModel):
    name = CharField()
    telegram_id = IntegerField(unique=True)

    class Meta:
        db_table = 'users'


class History(BaseModel):
    user = ForeignKeyField(User, backref="tg_user")
    date = DateField(formats='%Y-%m-%d', default=date.today())
    command = CharField()
    city = TextField()
    city_id = IntegerField()
    exact_hotel = TextField(null=True, default="Не найдено!")
    url_hotel = TextField(null=True, default=None)
    nights = SmallIntegerField()
    night_price = FloatField(null=True, default=None)
    total_price = FloatField(null=True, default=None)
    check_in_date = DateField(formats='%Y-%m-%d')
    check_out_date = DateField(formats='%Y-%m-%d')
    hotel_photos = SmallIntegerField()
    urls_photos = TextField(null=True, default=None)
    price_min = FloatField(null=True, default=None)
    price_max = FloatField(null=True, default=None)
    dest_min = FloatField(null=True, default=None)
    dest_max = FloatField(null=True, default=None)
    adults = SmallIntegerField()
    children = SmallIntegerField()
    exact_age_children = TextField(null=True, default=None)

    class Meta:
        db_table = 'histories'
