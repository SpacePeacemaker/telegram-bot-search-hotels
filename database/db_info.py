from peewee import SqliteDatabase, Model, CharField, IntegerField, TextField, ForeignKeyField, DateField, FloatField, \
    SmallIntegerField

db = SqliteDatabase('database/search_history.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    name = CharField()
    telegram_id = IntegerField()


class History(BaseModel):
    user = ForeignKeyField(User, backref="user")
    date = DateField()
    command = CharField()
    city = TextField()
    city_id = IntegerField()
    adults = IntegerField()
    children = IntegerField()
    exact_age_children = TextField()
    hotel_photos = IntegerField()
    urls_photos = TextField()
    exact_hotel = TextField()
    nights = SmallIntegerField()
    url_hotel = TextField()
    check_in_date = DateField()
    check_out_date = DateField()
    price_min = FloatField(null=False)
    price_max = FloatField(null=False)
    dest_min = FloatField(null=False)
    dest_max = FloatField(null=False)




