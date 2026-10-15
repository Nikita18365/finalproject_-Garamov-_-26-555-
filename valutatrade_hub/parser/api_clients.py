# Клиенты внешних API для получения валютных курсов"""
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

# Request можно использовать через библиотеку request, которую проходили на лекции
# Но добавлять лишнюю внешнюю зависимость в pyproject.toml не очень хорошо
# Лучше воспользоваться низкоуровневым интерфейсом urllib
from urllib.request import Request, urlopen

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
        query = urlencode({
                           "ids": "bitcoin,ethereum",
                           "vs_currencies": "usd"
                          })

        url = (
               f"{self._base_url}/simple/price"
               f"?{query}"
              )

        data = self._request_json(url)

        try:
            btc_rate = data["bitcoin"]["usd"]
            eth_rate = data["ethereum"]["usd"]
        except (KeyError, TypeError) as error:
            raise ApiRequestError("CoinGecko вернул данные "
                                  "в неожиданном формате"
                                 ) from error

        return {
                "BTC_USD": self._validate_rate(btc_rate, "BTC"),
                "ETH_USD": self._validate_rate(eth_rate, "ETH")
               }

    def _request_json(self, url: str) -> dict[str, Any]:
        """Выполнение get-запроса и возврат json"""
        request = Request(url, headers = {
                                         "Accept": "application/json",
                                         "User-Agent": "ValutaTrade-Hub/1.0"
                                        })

        try:
            with urlopen(request, timeout = self._timeout) as response:
                status_code = response.status

                if not 200 <= status_code < 300:
                    raise ApiRequestError("CoinGecko вернул HTTP "
                                          f"{status_code}"
                                         )

                response_body = response.read()

        except HTTPError as error:
            raise ApiRequestError("CoinGecko вернул HTTP "
                                  f"{error.code}"
                                 ) from error

        except URLError as error:
            raise ApiRequestError(f"ошибка сети CoinGecko: {error.reason}") from error

        except TimeoutError as error:
            raise ApiRequestError("превышено время ожидания CoinGecko") from error

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise ApiRequestError("CoinGecko вернул некорректный json") from error

        if not isinstance(data, dict):
            raise ApiRequestError("CoinGecko вернул неожиданный "
                                  "формат ответа"
                                 )

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
        """Получить курсы EUR и RUB относительно USD."""
        if not self._api_key:
            raise ApiRequestError("не задан EXCHANGE_RATE_API_KEY")

        url = (f"{self._base_url}/"
               f"{self._api_key}/latest/USD"
              )

        data = self._request_json(url)

        if data.get("result") != "success":
            error_type = data.get("error-type", "unknown-error")
            raise ApiRequestError("ExchangeRate-API вернул ошибку: "
                                  f"{error_type}"
                                 )

        conversion_rates = data.get("conversion_rates")

        if not isinstance(conversion_rates, dict):
            raise ApiRequestError("ExchangeRate-API не вернул "
                                  "conversion_rates"
                                 )

        eur_per_usd = self._get_rate(conversion_rates, "EUR")
        rub_per_usd = self._get_rate(conversion_rates, "RUB")
        return {"EUR_USD": 1.0 / eur_per_usd,
                "RUB_USD": 1.0 / rub_per_usd
               }

    def _request_json(self, url: str) -> dict[str, Any]:
        """Выполнение get-запроса и возврат json"""
        request = Request(url, headers={
                                        "Accept": "application/json",
                                        "User-Agent": "ValutaTrade-Hub/1.0"
                                       })

        try:
            with urlopen(request, timeout=self._timeout) as response:
                status_code = response.status

                if not 200 <= status_code < 300:
                    raise ApiRequestError("ExchangeRate-API вернул HTTP "
                                          f"{status_code}"
                                         )

                response_body = response.read()

        except HTTPError as error:
            raise ApiRequestError("ExchangeRate-API вернул HTTP "
                                  f"{error.code}"
                                 ) from error

        except URLError as error:
            raise ApiRequestError("ошибка сети ExchangeRate-API: "
                                  f"{error.reason}"
                                 ) from error

        except TimeoutError as error:
            raise ApiRequestError("превышено время ожидания "
                                  "ExchangeRate-API"
                                 ) from error

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise ApiRequestError("ExchangeRate-API вернул "
                                  "некорректный json"
                                 ) from error

        if not isinstance(data, dict):
            raise ApiRequestError("ExchangeRate-API вернул "
                                  "неожиданный формат ответа"
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