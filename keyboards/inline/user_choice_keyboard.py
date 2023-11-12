def create_button_keyboard(buttons: list) -> list:
    """
    Функция для создания кнопок в inline-клавиатуре.
    :param buttons: list
    :return: list
    """
    kb = [buttons[i:i + 1] for i in range(0, len(buttons))]
    return kb
