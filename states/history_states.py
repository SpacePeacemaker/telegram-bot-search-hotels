from telebot.handler_backends import State, StatesGroup


class HistoryInfoState(StatesGroup):
    exact_history = State()
