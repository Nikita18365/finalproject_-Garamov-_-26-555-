import json
from pathlib import Path
from typing import Any

# Корень проекта, независимо от того, откуда запускаем программу
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# data дирректория
DATA_DIR = PROJECT_ROOT / "data"

USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"
RATES_FILE = DATA_DIR / "rates.json"


def load_json(file_path: Path) -> Any:
    """Загрузить данные из json-файла"""
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    with file_path.open("r", encoding = "utf-8") as file:
        return json.load(file)


def save_json(file_path: Path, data: Any) -> None:
    """Сохранить данные в JSON-файл."""
    file_path.parent.mkdir(parents = True, exist_ok = True)
    with file_path.open("w", encoding = "utf-8") as file:
        json.dump(data, file, ensure_ascii = False, indent = 4)


def load_users() -> list[dict]:
    """Загрузка списка пользователей"""
    data = load_json(USERS_FILE)
    if not isinstance(data, list):
        raise TypeError("users.json должен содержать список")
    return data


def save_users(users: list[dict]) -> None:
    """Сохранить список пользователей"""
    save_json(USERS_FILE, users)


def load_portfolios() -> list[dict]:
    """Загрузка списка портфелей"""
    data = load_json(PORTFOLIOS_FILE)
    if not isinstance(data, list):
        raise TypeError("portfolios.json должен содержать список")
    return data


def save_portfolios(portfolios: list[dict]) -> None:
    """Сохранить список портфелей"""
    save_json(PORTFOLIOS_FILE, portfolios)


def load_rates() -> dict:
    """Загрузить локальный кэш валютных курсов"""
    data = load_json(RATES_FILE)
    if not isinstance(data, dict):
        raise TypeError("rates.json должен содержать объект json")
    return data


def save_rates(rates: dict) -> None:
    """Сохранить локальный кэш валютных курсов"""
    save_json(RATES_FILE, rates)


def normalize_currency_code(currency_code: str) -> str:
    """Проверка и нормализация кода валюты"""
    if not isinstance(currency_code, str):
        raise TypeError("Код валюты должен быть строкой")
    currency_code = currency_code.strip().upper()
    if not currency_code:
        raise ValueError("Код валюты не может быть пустым")
    return currency_code


def validate_amount(amount: float) -> float:
    """Проверка суммы валютной операции"""
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise TypeError("'amount' должен быть числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return float(amount)