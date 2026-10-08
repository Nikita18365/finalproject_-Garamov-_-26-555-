from datetime import datetime

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
                                        load_portfolios,
                                        load_users,
                                        save_portfolios,
                                        save_users,
                                       )


# Функция нужна только внутри usecases.py, поэтому делаем её с "_%"
def _generate_user_id(users: list[dict]) -> int:
    """Генерация следующего уникального идентификатора пользователя"""
    user_ids = [user["user_id"] for user in users if isinstance(user.get("user_id"), int)]
    return max(user_ids, default=0) + 1


def _user_from_dict(user_data: dict) -> User:
    """Создание объекта User из данных json"""
    return User(user_id = user_data["user_id"],
                username = user_data["username"],
                hashed_password = user_data["hashed_password"],
                salt = user_data["salt"],
                registration_date = datetime.fromisoformat(user_data["registration_date"])
               )


def register(username: str, password: str) -> User:
    """Регистрация нового пользователя"""
    if not isinstance(username, str):
        raise TypeError("Имя пользователя должно быть строкой")
    username = username.strip()
    if not username:
        raise ValueError("Имя пользователя не может быть пустым")

    users = load_users()

    for user_data in users:
        if user_data.get("username") == username:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = _generate_user_id(users)
    salt = User.generate_salt()
    hashed_password = User.hash_password(password, salt)

    user = User(user_id = user_id,
                username = username,
                hashed_password = hashed_password,
                salt = salt,
                registration_date = datetime.now().astimezone()
               )

    portfolio = Portfolio(user)
    portfolios = load_portfolios()

    users.append(user.to_dict())
    portfolios.append(portfolio.to_dict())

    save_users(users)
    save_portfolios(portfolios)

    return user

def login(username: str, password: str) -> User:
    """Вход пользователя в систему"""

    if not isinstance(username, str):
        raise TypeError("Имя пользователя должно быть строкой")

    if not isinstance(password, str):
        raise TypeError("Пароль должен быть строкой")

    username = username.strip()

    if not username:
        raise ValueError("Имя пользователя не может быть пустым")

    users = load_users()

    for user_data in users:
        if user_data.get("username") != username:
            continue

        user = _user_from_dict(user_data)

        if len(password) < 4 or not user.verify_password(password):
            raise ValueError("Неверный пароль")

        return user

    raise ValueError(f"Пользователь '{username}' не найден")
