# Настройка логирования ValutaTrade Hub
import logging
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader

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