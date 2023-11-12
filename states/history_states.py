from telebot.handler_backends import State, StatesGroup


class HistoryInfoState(StatesGroup):  # создание состояния для уточнения истории поиска
    exact_history = State()  # вывод конкретной истории поиска
