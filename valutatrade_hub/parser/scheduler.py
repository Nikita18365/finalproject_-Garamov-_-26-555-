# Периодическое обновление валютных курсов
import time

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.infra.logging_config import configure_parser_logging
from valutatrade_hub.parser.config import load_parser_config
from valutatrade_hub.parser.updater import RatesUpdater


# scheduler->RatesUpdater.run_update()->CoinGecko(X)->ExchangeRate-API(X)->
# ->ApiRequestError
def run_scheduler() -> None:
    """Периодическое обновление валютных курсов"""
    config = load_parser_config()
    updater = RatesUpdater(config=config)
    logger = configure_parser_logging()

    interval = config.update_interval_seconds

    logger.info("Планировщик обновления курсов запущен "
                "с интервалом %s секунд",
                interval
               )

    try:
        while True:
            try:
                updater.run_update()
            except ApiRequestError:
                logger.exception("Плановое обновление курсов "
                                 "завершилось ошибкой"
                                )

            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Планировщик обновления курсов остановлен")