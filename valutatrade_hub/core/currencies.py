"""Иерархия валют платформы"""
from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс валюты"""

    def __init__(self,
                 name: str,
                 code: str
                ) -> None:
        """Инициализация валюты"""

        if not isinstance(name, str):
            raise TypeError("Название валюты должно быть строкой")
        name = name.strip()
        if not name:
            raise ValueError("Название валюты не может быть пустым")
        if not isinstance(code, str):
            raise TypeError("Код валюты должен быть строкой")

        code = code.strip().upper()
        if not 2 <= len(code) <= 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")
        if any(character.isspace() for character in code):
            raise ValueError("Код валюты не должен содержать пробелы")

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Ролбэк строкового представления валюты"""


class FiatCurrency(Currency):
    """Фиатная валюта"""

    def __init__(self,
                 name: str,
                 code: str,
                 issuing_country: str
                ) -> None:
        """Инициализация фиатной валюты"""

        super().__init__(name, code)
        if not isinstance(issuing_country, str):
            raise TypeError("Страна или зона эмиссии должна быть строкой")

        issuing_country = issuing_country.strip()
        if not issuing_country:
            raise ValueError("Страна или зона эмиссии не может быть пустой")

        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        """Возврат информации о фиатной валюте"""
        return (
                f"[FIAT] {self.code} - {self.name} "
                f"(Issuing: {self.issuing_country})"
               )


class CryptoCurrency(Currency):
    """Криптовалюта"""

    def __init__(self,
                 name: str,
                 code: str,
                 algorithm: str,
                 market_cap: float
                ) -> None:
        """Инициализировать криптовалюту"""
        super().__init__(name, code)
        if not isinstance(algorithm, str):
            raise TypeError("Алгоритм криптовалюты должен быть строкой")
        algorithm = algorithm.strip()
        if not algorithm:
            raise ValueError("Алгоритм криптовалюты не может быть пустым")
        if isinstance(market_cap, bool) or not isinstance(market_cap, (int, float)):
            raise TypeError("Рыночная капитализация должна быть числом")
        if market_cap < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной")
        self.algorithm = algorithm
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        """Возврат информации о криптовалюте"""
        market_cap = (f"{self.market_cap:.2e}".replace("e+", "e"))
        return (
                f"[CRYPTO] {self.code} - {self.name} "
                f"(Algo: {self.algorithm}, "
                f"MCAP: {market_cap})"
               )


CURRENCY_REGISTRY: dict[str, Currency] = {
    "USD": FiatCurrency(
                        name            = "US Dollar",
                        code            = "USD",
                        issuing_country = "United States"
                       ),
    "EUR": FiatCurrency(
                        name            = "Euro",
                        code            = "EUR",
                        issuing_country = "Eurozone"
                       ),
    "RUB": FiatCurrency(
                        name            = "Russian Ruble",
                        code            = "RUB",
                        issuing_country = "Russia"
                       ),
    "BTC": CryptoCurrency(
                          name          = "Bitcoin",
                          code          = "BTC",
                          algorithm     = "SHA-256",
                          market_cap    = 1.12e12
                         ),
    "ETH": CryptoCurrency(
                          name          = "Ethereum",
                          code          = "ETH",
                          algorithm     = "Ethash",
                          market_cap    = 4.47e11
                         )
                                         }


def get_currency(code: str) -> Currency:
    """Получение объекта валюты по её коду"""
    if not isinstance(code, str):
        raise TypeError("Код валюты должен быть строкой")
    code = code.strip().upper()
    try:
        return CURRENCY_REGISTRY[code]
    except KeyError as error:
        raise CurrencyNotFoundError(code) from error