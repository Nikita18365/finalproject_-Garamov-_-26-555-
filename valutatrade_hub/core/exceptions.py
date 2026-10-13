# Пользовательские исключения платформы
class InsufficientFundsError(Exception):
    """Ошибка недостаточного количества средств"""
    def __init__(self,
                 available: float,
                 required: float,
                 code: str
                ) -> None:
        """Инициализация ошибки недостатка средств"""

        self.available = available
        self.required = required
        self.code = code

        message = (
                   "Недостаточно средств: "
                   f"доступно {available:.4f} {code}, "
                   f"требуется {required:.4f} {code}"
                  )

        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """Ошибка неизвестной валюты"""

    def __init__(self, code: str) -> None:
        """Инициализация ошибки неизвестной валюты"""
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class ApiRequestError(Exception):
    """Ошибка обращения к внешнему API"""

    def __init__(self, reason: str) -> None:
        """Инициализация ошибки внешнего API"""
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")