from datetime import datetime

from valutatrade_hub.core.models import (
                                         DEFAULT_EXCHANGE_RATES,
                                         Portfolio,
                                         User,
                                         Wallet,
                                        )
from valutatrade_hub.core.utils import (
                                        load_portfolios,
                                        load_rates,
                                        load_users,
                                        normalize_currency_code,
                                        save_portfolios,
                                        save_users,
                                        validate_amount,
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


def _portfolio_from_dict(user: User,
                         portfolio_data: dict,
                        ) -> Portfolio:
    """Создание объекта Portfolio из данных json"""
    wallets = {}
    for currency_code, wallet_data in portfolio_data.get("wallets", {}).items():
        wallets[currency_code] = Wallet(currency_code = wallet_data.get("currency_code", 
                                                                        currency_code
                                                                       ),
                                        balance = wallet_data["balance"]
                                       )
    return Portfolio(user_id = portfolio_data["user_id"], wallets = wallets, user = user,)


def _save_user_portfolio(portfolio: Portfolio) -> None:
    """Сохранить изменённый портфель пользователя"""
    portfolios = load_portfolios()
    for index, portfolio_data in enumerate(portfolios):
        if portfolio_data.get("user_id") == portfolio.user_id:
            portfolios[index] = portfolio.to_dict()
            save_portfolios(portfolios)
            return
    raise ValueError("Портфель пользователя не найден")


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

    portfolio = Portfolio(user_id = user.user_id, user = user,)
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


def get_user_portfolio(user: User) -> Portfolio:
    """Получение портфеля пользователя"""
    if not isinstance(user, User):
        raise TypeError("user должен быть объектом User")

    portfolios = load_portfolios()

    for portfolio_data in portfolios:
        if portfolio_data.get("user_id") == user.user_id:
            return _portfolio_from_dict(user, portfolio_data)

    raise ValueError("Портфель пользователя не найден")


def _get_exchange_rates() -> dict[str, float]:
    """Получение курсов валют к USD из кеша или заглушки"""
    rates_data = load_rates()
    pairs = rates_data.get("pairs", {})

    if not pairs:
        return DEFAULT_EXCHANGE_RATES.copy()

    exchange_rates = {"USD": 1.0}

    for pair_code, pair_data in pairs.items():

        if not pair_code.endswith("_USD"):
            continue

        currency_code = pair_code.removesuffix("_USD")

        if isinstance(pair_data, dict):
            rate = pair_data.get("rate")
        else:
            rate = pair_data

        if isinstance(rate, bool) or not isinstance(rate, (int, float)):
            continue

        exchange_rates[currency_code] = float(rate)

    return exchange_rates


def get_portfolio_summary(user: User,
                          base_currency: str = "USD",
                         ) -> dict:
    """Получение информации о портфеле пользователя"""
    base_currency = normalize_currency_code(base_currency)
    exchange_rates = _get_exchange_rates()

    if base_currency not in exchange_rates:
        raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

    portfolio = get_user_portfolio(user)

    wallets_info = []

    for wallet in portfolio.wallets.values():
        currency_code = wallet.currency_code
        if currency_code not in exchange_rates:
            raise ValueError(f"Не найден курс для валюты '{currency_code}'")
        value_usd = (wallet.balance * exchange_rates[currency_code])
        value_in_base = (value_usd / exchange_rates[base_currency])
        wallets_info.append({
                             "currency_code": currency_code,
                             "balance": wallet.balance,
                             "value_in_base": value_in_base
                            })

    return {"username": user.username,
            "base_currency": base_currency,
            "wallets": wallets_info,
            "total_value": portfolio.get_total_value(base_currency, rates = exchange_rates)
           }


def buy(user: User,
        currency_code: str,
        amount: float,
       ) -> dict:
    """Покупка валюты и обновление портфеля пользователя"""

    if not isinstance(user, User):
        raise TypeError("user должен быть объектом User")

    currency_code = normalize_currency_code(currency_code)
    amount = validate_amount(amount)

    if currency_code not in DEFAULT_EXCHANGE_RATES:
        raise ValueError(f"Не удалось получить курс для {currency_code} -> USD")

    portfolio = get_user_portfolio(user)
    wallet = portfolio.get_wallet(currency_code)

    if wallet is None:
        wallet = portfolio.add_currency(currency_code)

    old_balance = wallet.balance
    rate = DEFAULT_EXCHANGE_RATES[currency_code]

    wallet.deposit(amount)

    new_balance = wallet.balance
    estimated_cost = amount * rate

    _save_user_portfolio(portfolio)

    return {"currency_code": currency_code,
            "amount": amount,
            "rate": rate,
            "base_currency": "USD",
            "old_balance": old_balance,
            "new_balance": new_balance,
            "estimated_cost": estimated_cost,
           }


def sell(user: User,
         currency_code: str,
         amount: float,
        ) -> dict:
    """Продажа валюты и обновление портфеля пользователя"""

    if not isinstance(user, User):
        raise TypeError("user должен быть объектом User")

    currency_code = normalize_currency_code(currency_code)
    amount = validate_amount(amount)

    if currency_code not in DEFAULT_EXCHANGE_RATES:
        raise ValueError(f"Не удалось получить курс для {currency_code} -> USD")

    portfolio = get_user_portfolio(user)
    wallet = portfolio.get_wallet(currency_code)

    if wallet is None:
        raise ValueError(
                         f"У вас нет кошелька '{currency_code}'. "
                         "Добавьте валюту: она создаётся автоматически "
                         "при первой покупке."
                        )

    old_balance = wallet.balance
    rate = DEFAULT_EXCHANGE_RATES[currency_code]

    wallet.withdraw(amount)

    new_balance = wallet.balance
    estimated_revenue = amount * rate

    _save_user_portfolio(portfolio)

    return {"currency_code": currency_code,
            "amount": amount,
            "rate": rate,
            "base_currency": "USD",
            "old_balance": old_balance,
            "new_balance": new_balance,
            "estimated_revenue": estimated_revenue,
           }