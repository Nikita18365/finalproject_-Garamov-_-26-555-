# Обновление валютных курсов через внешние API
from datetime import datetime
from typing import Any

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.infra.logging_config import configure_parser_logging
from valutatrade_hub.parser.api_clients import (
                                                CoinGeckoClient,
                                                ExchangeRateApiClient,
                                               )
from valutatrade_hub.parser.config import (
                                           ParserConfig,
                                           load_parser_config,
                                          )
from valutatrade_hub.parser.storage import RatesStorage


# RatesUpdater получает зависимости снаружи
class RatesUpdater:
    """Получение и сохранение валютных курсов"""

    def __init__(self,
                 config: ParserConfig | None = None,
                 storage: RatesStorage | None = None
                ) -> None:
        """Инициализация сервиса обновления курсов"""
        self._config = (config if config is not None else load_parser_config())
        self._storage = (storage if storage is not None else RatesStorage())
        self._logger = configure_parser_logging()
        self._clients = [("CoinGecko", CoinGeckoClient(self._config)),
                         ("ExchangeRate-API", ExchangeRateApiClient(self._config))
                        ]
        # Так мы одновременно знаем объект клиента и человеческое имя источника
        # И потом это имя можно записать в "source": "CoinGecko"

    def run_update(self) -> dict[str, Any]:
        """Получение и сохранение актуальных валютных курсов"""
        self._logger.info("Запуск обновления валютных курсов...")
        collected_rates: dict[str, tuple[float, str]] = {}
        errors: list[str] = []

        for source_name, client in self._clients:
            self._fetch_client_rates(source_name     = source_name,
                                     client          = client,
                                     collected_rates = collected_rates,
                                     errors          = errors
                                    )

        # Ни один источник ничего не вернул
        if not collected_rates:
            self._logger.error("Обновление курсов не выполнено: "
                               "все API-клиенты завершились ошибкой"
                              )

            raise ApiRequestError("не удалось получить курсы "
                                  "ни от одного внешнего API"
                                 )
         # До этого места RatesStorage ещё не вызывался
         # Поэтому старый rates.json не будет затёрт пустым объектом

        updated_at = datetime.now().astimezone().isoformat()

        rates_data = self._build_snapshot(collected_rates = collected_rates, updated_at = updated_at)
        self._storage.save_current_rates(rates_data)
        history_added = (self._storage.append_history(rates_data))

        self._logger.info("Обновление курсов завершено: "
                          "получено %s курсов",
                          len(collected_rates)
                         )
        self._logger.debug("В историю добавлено %s новых записей", history_added)

        return {
                "updated_count": len(collected_rates),
                "last_refresh": updated_at,
                "errors": errors
               }

    def _fetch_client_rates(self,
                            source_name: str,
                            client: Any,
                            collected_rates: dict[str, tuple[float, str]],
                            errors: list[str]
                           ) -> None:
        """Получение курсов одного API-клиента"""
        self._logger.info("Получение данных из %s...", source_name)

        # CoinGecko->ApiRequestError->RatesUpdater ловит->логирует->
        # errors.append(///)->продолжает цикл->ExchangeRate-API работает
        try:
            rates = client.fetch_rates()
        except ApiRequestError as error:
            # logger.exception() внутри except автоматически записывает traceback
            # В консоль пойдет "ERROR: Не удалось получить данные из"
            self._logger.error("Не удалось получить данные из %s",
                               source_name
                              )
            self._logger.debug("Подробности ошибки при получении данных из %s",
                               source_name,
                               exc_info = True
                              )
            errors.append(f"{source_name}: {error}")
            return

        for pair_code, rate in rates.items():
            collected_rates[pair_code] = (rate, source_name)

        self._logger.info("Данные из %s получены успешно "
                          "(%s курсов)",
                          source_name,
                          len(rates)
                         )

    @staticmethod
    def _build_snapshot(collected_rates: dict[str, tuple[float, str]], 
                        updated_at: str) -> dict[str, Any]:
        """Построение снимка для rates.json"""
        pairs = {}
        for (pair_code, (rate, source)) in collected_rates.items():
            pairs[pair_code] = {"rate": rate,
                                "updated_at": updated_at,
                                "source": source
                               }
        return {"pairs": pairs, "last_refresh": updated_at}