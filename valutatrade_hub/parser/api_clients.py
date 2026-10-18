# Клиенты внешних API для получения валютных курсов"""
from typing import Any

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser.config import ParserConfig


class CoinGeckoClient:
    """Клиент CoinGecko для получения курсов криптовалют"""

    def __init__(self, config: ParserConfig) -> None:
        """Инициализация клиента CoinGecko"""
        self._base_url = config.coingecko_base_url
        self._timeout = config.request_timeout_seconds

    def fetch_rates(self) -> dict[str, float]:
        """Получение курсов BTC и ETH относительно USD"""

        url = f"{self._base_url}/simple/price"
        params = {"ids": "bitcoin,ethereum",
                  "vs_currencies": "usd"
                 }
        data = self._request_json(url, params = params)

        try:
            btc_rate = float(data["bitcoin"]["usd"])
            eth_rate = float(data["ethereum"]["usd"])
        except (KeyError, TypeError, ValueError) as error:
            raise ApiRequestError("CoinGecko вернул некорректные данные") from error

        if btc_rate <= 0 or eth_rate <= 0:
            raise ApiRequestError("CoinGecko вернул неположительный курс")

        return {"BTC_USD": btc_rate,
                "ETH_USD": eth_rate
               }

    def _request_json(self,
                      url: str,
                      params: dict[str, str] | None = None
                     ) -> dict:
        """Выполнение get-запроса и возврат json"""

        try:
            response = requests.get(url, params = params, timeout = self._timeout)
        except requests.RequestException as error:
            raise ApiRequestError("не удалось выполнить запрос к CoinGecko") from error

        if not response.ok:
            raise ApiRequestError("CoinGecko вернул HTTP "
                                  f"{response.status_code}"
                                 )

        try:
            data = response.json()
        except ValueError as error:
            raise ApiRequestError("CoinGecko вернул некорректный json") from error

        if not isinstance(data, dict):
            raise ApiRequestError("CoinGecko вернул неожиданный формат данных")

        return data

    @staticmethod
    def _validate_rate(rate: Any, currency_code: str) -> float:
        """Проверка корректности валютного курса"""
        if (
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or rate <= 0
           ):
            raise ApiRequestError(f"CoinGecko вернул некорректный "
                                  f"курс {currency_code}"
                                 )
        return float(rate)


class ExchangeRateApiClient:
    """Клиент ExchangeRate-API для фиатных валют"""

    def __init__(self, config: ParserConfig) -> None:
        """Инициализация клиента ExchangeRate-API"""
        self._base_url = config.exchange_rate_base_url
        self._api_key = config.exchange_rate_api_key
        self._timeout = config.request_timeout_seconds

    def fetch_rates(self) -> dict[str, float]:
        """Получить курсы EUR и RUB относительно USD"""
        if not self._api_key:
            raise ApiRequestError("не задан ключ ExchangeRate-API")

        url = (f"{self._base_url}/"
               f"{self._api_key}/latest/USD"
              )

        data = self._request_json(url)

        try:
            conversion_rates = data["conversion_rates"]
            eur_to_usd = 1.0 / float(conversion_rates["EUR"])
            rub_to_usd = 1.0 / float(conversion_rates["RUB"])
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
            raise ApiRequestError("ExchangeRate-API вернул "
                                  "некорректные данные") from error

        if eur_to_usd <= 0 or rub_to_usd <= 0:
            raise ApiRequestError("ExchangeRate-API вернул "
                                  "неположительный курс")

        return {"EUR_USD": eur_to_usd,
                "RUB_USD": rub_to_usd
               }

    def _request_json(self, url: str) -> dict:
        """Выполнение get-запроса и возврат json"""
        try:
            response = requests.get(url, timeout = self._timeout)
        except requests.RequestException as error:
            raise ApiRequestError("не удалось выполнить запрос "
                                  "к ExchangeRate-API") from error

        if not response.ok:
            raise ApiRequestError("ExchangeRate-API вернул HTTP "
                                  f"{response.status_code}"
                                 )

        try:
            data = response.json()
        except ValueError as error:
            raise ApiRequestError("ExchangeRate-API вернул "
                                  "некорректный json"
                                 ) from error

        if not isinstance(data, dict):
            raise ApiRequestError("ExchangeRate-API вернул "
                                  "неожиданный формат данных"
                                 )

        return data

    @staticmethod
    def _get_rate(conversion_rates: dict, currency_code: str) -> float:
        """Получение и проверка курса из ответа API"""
        rate = conversion_rates.get(currency_code)

        if (
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or rate <= 0
           ):
            raise ApiRequestError("ExchangeRate-API не вернул "
                                  f"корректный курс {currency_code}"
                                 )

        return float(rate)