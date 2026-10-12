# Пользовательские исключения платформы
class CurrencyNotFoundError(Exception):
    """Ошибка неизвестной валюты"""

    def __init__(self, code: str) -> None:
        """Инициализация ошибки неизвестной валюты"""
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")