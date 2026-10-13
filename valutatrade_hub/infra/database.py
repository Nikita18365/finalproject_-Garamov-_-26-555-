# Абстракция над json-хранилищем ValutaTrade Hub
import json
import os
from pathlib import Path
from typing import Any, Self

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Singleton для работы с json-хранилищем"""

    _instance = None
    _initialized = False

    def __new__(cls) -> Self:
        """Создать или вернуть единственный экземпляр"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Инициализация мэнеджера хранилища(только один раз))"""
        if self._initialized:
            return
        self._settings = SettingsLoader()
        self._initialized = True

    def read_json(self, path_key: str) -> Any:
        """Прочитать json-файл по ключу конфигурации"""

        file_path = self._settings.get_path(path_key)
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        with file_path.open("r", encoding = "utf-8") as file:
            return json.load(file)

    def write_json(self,
                   path_key: str,
                   data: Any
                  ) -> None:
        """Атомарно сохранить данные в json-файл"""

        file_path = self._settings.get_path(path_key)
        file_path.parent.mkdir(parents = True, exist_ok = True)
        temp_path = self._get_temp_path(file_path)

        with temp_path.open("w", encoding = "utf-8") as file:
            json.dump(data,
                      file,
                      ensure_ascii = False,
                      indent       = 4,
                     )

        os.replace(temp_path, file_path)

    def load_users(self) -> list[dict]:
        """Загрузка пользователей"""
        data = self.read_json("users_path")
        if not isinstance(data, list):
            raise TypeError("users.json должен содержать список")
        return data

    def save_users(self,
                   users: list[dict]
                  ) -> None:
        """Сохранение пользователей"""
        self.write_json("users_path", users)

    def load_portfolios(self) -> list[dict]:
        """Загрузка портфелей"""
        data = self.read_json("portfolios_path")
        if not isinstance(data, list):
            raise TypeError("portfolios.json должен содержать список")
        return data

    def save_portfolios(self,
                        portfolios: list[dict]
                       ) -> None:
        """Сохранение портфелей"""
        self.write_json("portfolios_path", portfolios)

    def load_rates(self) -> dict:
        """Загрузка кэша валютных курсов"""
        data = self.read_json("rates_path")
        if not isinstance(data, dict):
            raise TypeError("rates.json должен содержать объект json")
        return data

    def save_rates(self,
                   rates: dict
                  ) -> None:
        """Сохранение кэша валютных курсов"""
        self.write_json("rates_path", rates)

    @staticmethod
    def _get_temp_path(file_path: Path) -> Path:
        """Получение путь временного файла"""
        return file_path.with_suffix(f"{file_path.suffix}.tmp")