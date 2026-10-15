# Хранилище данных Parser Service
# Данный модуль отвечает за смысл хранения
# RatesUpdater->RatesStorage->DatabaseManager->tmp-файл->os.replace()->json
from typing import Any

from valutatrade_hub.infra.database import DatabaseManager


class RatesStorage:
    """Хранилище актуальных и исторических валютных курсов"""

    def __init__(self) -> None:
        """Инициализация хранилища"""
        self._database = DatabaseManager()

    def save_current_rates(self, rates_data: dict[str, Any]) -> None:
        """Сохранение актуальных снимков курса"""
        self._validate_rates_snapshot(rates_data)
        self._database.write_json("rates_path", rates_data)

    def load_current_rates(self) -> dict:
        """Загрузка актуальных снимков курса"""
        data = self._database.read_json("rates_path")

        if not isinstance(data, dict):
            raise TypeError("rates.json должен содержать json-объект")

        return data

    def append_history(self, rates_data: dict[str, Any]) -> int:
        """Добавление новых курсов в историю без дублей"""
        self._validate_rates_snapshot(rates_data)
        history = self._database.read_json("exchange_rates_path")

        if not isinstance(history, list):
            raise TypeError("exchange_rates.json должен содержать json-массив")

        existing_ids = {item.get("id")
                        for item in history if isinstance(item, dict)
                       }

        added_count = 0

        for pair_code, pair_data in rates_data["pairs"].items():
            updated_at = pair_data["updated_at"]
            record_id = self._build_history_id(pair_code, updated_at)
            if record_id in existing_ids:
                continue

            history.append({
                            "id":         record_id,
                            "pair":       pair_code,
                            "rate":       pair_data["rate"],
                            "updated_at": updated_at,
                            "source":     pair_data["source"]
                           })

            existing_ids.add(record_id)
            added_count += 1

        self._database.write_json("exchange_rates_path", history)

        return added_count

    @staticmethod
    def _build_history_id(pair_code: str, updated_at: str) -> str:
        """Построение уникальных идентификаторов записи истории"""
        timestamp = (updated_at.replace(":", "-").replace("+", "_"))
        return f"{pair_code}_{timestamp}"

    @staticmethod
    def _validate_rates_snapshot(rates_data: dict[str, Any]) -> None:
        """Проверка структуры снимка валютных курсов"""
        if not isinstance(rates_data, dict):
            raise TypeError("Данные курсов должны быть словарём")

        pairs = rates_data.get("pairs")
        last_refresh = rates_data.get("last_refresh")

        if not isinstance(pairs, dict):
            raise TypeError("В данных курсов отсутствует корректный 'pairs'")

        if not isinstance(last_refresh, str):
            raise TypeError("В данных курсов отсутствует корректный "
                             "'last_refresh'"
                            )

        for pair_code, pair_data in pairs.items():
            if not isinstance(pair_code, str):
                raise TypeError("Код валютной пары должен быть строкой")

            if not isinstance(pair_data, dict):
                raise TypeError(f"Данные пары '{pair_code}' "
                                "должны быть словарём"
                               )

            rate = pair_data.get("rate")
            updated_at = pair_data.get("updated_at")
            source = pair_data.get("source")

            if (
                isinstance(rate, bool)
                or not isinstance(rate, (int, float))
                or rate <= 0
               ):
                raise ValueError(f"Некорректный курс '{pair_code}'")

            if not isinstance(updated_at, str):
                raise TypeError(f"Некорректный updated_at "
                                 f"для '{pair_code}'"
                                )

            if (not isinstance(source, str) or not source.strip()):
                raise ValueError(f"Некорректный source "
                                 f"для '{pair_code}'"
                                )