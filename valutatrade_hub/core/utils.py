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
