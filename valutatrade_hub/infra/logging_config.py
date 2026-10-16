# Настройка логирования ValutaTrade Hub
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader

PARSER_LOGGER_NAME = "valutatrade_hub.parser"
LOGGER_NAME = "valutatrade_hub"


def configure_logging() -> logging.Logger:
    """Настройка и возрат logger приложения"""

    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    settings = SettingsLoader()

    log_path = settings.get_path("log_path")
    log_path.parent.mkdir(parents = True, exist_ok = True)
    log_level_name = settings.get("log_level", "INFO")
    log_level = getattr(logging, str(log_level_name).upper(), logging.INFO)
    log_format = settings.get("log_format", "%(levelname)s %(asctime)s %(message)s")

    max_bytes = settings.get("log_max_bytes", 1_048_576)
    backup_count = settings.get("log_backup_count", 3)

    handler = RotatingFileHandler(log_path,
                                  maxBytes    = max_bytes,
                                  backupCount = backup_count,
                                  encoding    = "utf-8"
                                 )

    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


# Функция пишет только в файл
def configure_parser_logging() -> logging.Logger:
    """Настройка файлового логирования в парсере"""

    logger = logging.getLogger(PARSER_LOGGER_NAME)
    # Данное условие нужно чтобы при повтороном вызове, не поулчилось
    # N одинаковых FileHandler
    if logger.handlers:
        return logger

    settings = SettingsLoader()

    log_path = settings.get_path("parser_log_path")
    log_path.parent.mkdir(parents = True, exist_ok = True)
    log_level_name = settings.get("parser_log_level", "DEBUG")
    log_level = getattr(logging, str(log_level_name).upper(), logging.DEBUG)

    max_bytes = settings.get("parser_log_max_bytes", 1_048_576)
    backup_count = settings.get("parser_log_backup_count", 3)

    file_handler = RotatingFileHandler(log_path,
                                       maxBytes    = max_bytes,
                                       backupCount = backup_count,
                                       encoding    = "utf-8",
                                      )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s "
                                       "%(levelname)s "
                                       "%(name)s "
                                       "%(message)s"
                                      )

    file_handler.setFormatter(file_formatter)
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


@contextmanager
def parser_console_logging() -> Iterator[None]:
    """Временное включение вывода парсера в консоль"""

    logger = configure_parser_logging()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    try:
        yield
    finally:
        logger.removeHandler(console_handler)
        console_handler.close()