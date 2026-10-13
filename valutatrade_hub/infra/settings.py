# Загрузка и хранение конфигурации ValutaTrade Hub
import tomllib
from pathlib import Path
from typing import Any, Self

_MISSING = object()


class SettingsLoader:
    """Singleton для загрузки конфигурации приложения"""

    _instance = None
    _initialized = False

    def __new__(cls) -> Self:
        """Создать или вернуть единственный экземпляр"""

        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        """Инициализация загрузчика конфигурации(только 1 раз)"""

        # В противном случае конфигурация будет загружаться заново
        # при каждом обращении
        if self._initialized:
            return

        self._project_root = Path(__file__).resolve().parents[2]
        self._config_path = self._project_root/"pyproject.toml"
        self._settings: dict[str, Any] = {}

        self.reload()
        self._initialized = True

    @property
    def project_root(self) -> Path:
        """Возврат корневой директории проекта"""
        return self._project_root

    def reload(self) -> None:
        """Перезагрузка настройки из pyproject.toml"""

        if not self._config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {self._config_path}")

        with self._config_path.open("rb") as file:
            config = tomllib.load(file)

        self._settings = (config
                          .get("tool", {})
                          .get("valutatrade", {})
                          .copy()
                         )

    def get(self,
            key: str,
            default: Any = _MISSING
           ) -> Any:
        """Получение значения настройки по ключу"""

        if key in self._settings:
            return self._settings[key]
        if default is not _MISSING:
            return default
        raise KeyError(f"Настройка '{key}' не найдена")

    def get_path(self, key: str) -> Path:
        """Получение абсолютного пути из конфигурации"""

        value = self.get(key)
        if not isinstance(value, str):
            raise TypeError(f"Настройка '{key}' должна содержать путь")
        path = Path(value)
        if path.is_absolute():
            return path

        return self._project_root / path