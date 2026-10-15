# Конфигурация Parser service"""
import os
from dataclasses import dataclass

from valutatrade_hub.infra.settings import SettingsLoader


@dataclass(frozen = True) # делает объект конфигурации неизменяемым
class ParserConfig:
    """Настройка Parser service"""
    coingecko_base_url: str
    exchange_rate_base_url: str
    exchange_rate_api_key: str | None
    request_timeout_seconds: float
    update_interval_seconds: float


def load_parser_config() -> ParserConfig:
    """Загрузка настроек Parser service"""
    settings = SettingsLoader()

    timeout = settings.get("request_timeout_seconds", 10)
    update_interval = settings.get("parser_update_interval_seconds", 300)

    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise TypeError(
                        "Настройка 'request_timeout_seconds' "
                        "должна быть числом"
                       )

    if timeout <= 0:
        raise ValueError(
                         "Настройка 'request_timeout_seconds' "
                         "должна быть положительной"
                        )

    if isinstance(update_interval, bool) or not isinstance(update_interval, (int, float)):
        raise TypeError(
                        "Настройка 'parser_update_interval_seconds' "
                        "должна быть числом"
                       )

    if update_interval <= 0:
        raise ValueError(
                         "Настройка 'parser_update_interval_seconds' "
                         "должна быть положительной"
                        )

    return ParserConfig(
                        coingecko_base_url      = settings.get("coingecko_base_url"),
                        exchange_rate_base_url  = settings.get("exchange_rate_base_url"),
                        exchange_rate_api_key   = os.getenv("EXCHANGE_RATE_API_KEY"),
                        request_timeout_seconds = float(timeout),
                        update_interval_seconds = float(update_interval)
                       )