# Декораторы нашей платформы
from collections.abc import Callable
from functools import wraps
from inspect import signature
from typing import Any, TypeVar

from valutatrade_hub.infra.logging_config import configure_logging

F = TypeVar("F", bound = Callable[..., Any])


def log_action(action: str) -> Callable[[F], F]:
    """Логирование результатов выполнения действия"""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound_arguments = signature(func).bind(*args, **kwargs)
            bound_arguments.apply_defaults()
            arguments = bound_arguments.arguments

            user_id = _get_user_id(arguments)
            currency_code = arguments.get("currency_code", "UNKNOWN")
            amount = arguments.get("amount", "UNKNOWN")
            logger = configure_logging()

            try:
                result = func(*args, **kwargs)
            except Exception:
                logger.exception("%s user_id=%s currency=%s "
                                 "amount=%s result=ERROR",
                                 action,
                                 user_id,
                                 currency_code,
                                 amount
                                )
                raise

            rate = _get_result_rate(result)

            logger.info("%s user_id=%s currency=%s "
                        "amount=%s rate=%s result=OK",
                        action,
                        user_id,
                        currency_code,
                        amount,
                        rate
                       )

            return result
        return wrapper  # type: ignore[return-value]
    return decorator


def _get_user_id(arguments: dict[str, Any]) -> Any:
    """Получение user_id из аргументов функции"""
    if "user_id" in arguments:
        return arguments["user_id"]
    user = arguments.get("user")
    if user is not None and hasattr(user, "user_id"):
        return user.user_id
    return "UNKNOWN"


def _get_result_rate(result: Any) -> Any:
    """Получение курса из результата операции"""
    if isinstance(result, dict):
        return result.get("rate", "UNKNOWN")
    return "UNKNOWN"