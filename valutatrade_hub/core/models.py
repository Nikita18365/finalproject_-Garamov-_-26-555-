import hashlib
import secrets
from datetime import datetime

DEFAULT_EXCHANGE_RATES = {
                          "USD": 1.0,
                          "EUR": 1.0786,
                          "BTC": 59337.21,
                          "RUB": 0.01016,
                          "ETH": 3720.0,
                         }


class User:
    """Пользователь системы"""

    def __init__(self,
                 user_id: int,
                 username: str,
                 hashed_password: str,
                 salt: str,
                 registration_date: datetime,
                ) -> None:
        """Инициализация пользователя"""
        self.user_id = user_id
        self.username = username
        self.hashed_password = hashed_password
        self.salt = salt
        self.registration_date = registration_date

    @property
    def user_id(self) -> int:
        """Возврат идентификатора пользователя"""
        return self._user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        """Установка идентификатора пользователя"""
        if not isinstance(value, int):
            raise TypeError("user_id должен быть целым числом")
        if value <= 0:
            raise ValueError("user_id должен быть положительным числом")

        self._user_id = value

    @property
    def username(self) -> str:
        """Возврат имени пользователя"""
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        """Установка имени пользователя"""
        if not isinstance(value, str):
            raise TypeError("Имя пользователя должно быть строкой")

        value = value.strip()

        if not value:
            raise ValueError("Имя пользователя не может быть пустым")

        self._username = value

    @property
    def hashed_password(self) -> str:
        """Возврат хеш пароля"""
        return self._hashed_password

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        """Установка хеша пароля"""
        if not isinstance(value, str) or not value:
            raise ValueError("Хеш пароля не может быть пустым")
        self._hashed_password = value

    @property
    def salt(self) -> str:
        """Возврат соли пароля"""
        return self._salt

    @salt.setter
    def salt(self, value: str) -> None:
        """Установка соли пароля"""
        if not isinstance(value, str) or not value:
            raise ValueError("Соль не может быть пустой")
        self._salt = value

    @property
    def registration_date(self) -> datetime:
        """Возврат даты регистрации пользователя"""
        return self._registration_date

    @registration_date.setter
    def registration_date(self, value: datetime) -> None:
        """Установка даты регистрации пользователя"""
        if not isinstance(value, datetime):
            raise TypeError("registration_date должен быть объектом datetime")
        self._registration_date = value

    @staticmethod
    def generate_salt() -> str:
        """Генерация случайной соли для пароля"""
        return secrets.token_hex(16)

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Получение SHA-256 хеша пароля с солью"""
        if not isinstance(password, str):
            raise TypeError("Пароль должен быть строкой")

        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        password_with_salt = password + salt
        return hashlib.sha256(password_with_salt.encode("utf-8")).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверка правильности введённого пароля"""
        password_hash = self.hash_password(password, self._salt)
        return password_hash == self._hashed_password

    def change_password(self, new_password: str) -> None:
        """Изменение пароля пользователя"""
        new_salt = self.generate_salt()
        new_hash = self.hash_password(new_password, new_salt)
        self._salt = new_salt
        self._hashed_password = new_hash

    def get_user_info(self) -> dict:
        """Возврат информации о пользователе без пароля"""
        return {
                "user_id": self._user_id,
                "username": self._username,
                "registration_date": self._registration_date.isoformat(),
               }

    # Небольшой вспомогательный метод, который потом сильно упростит register
    def to_dict(self) -> dict:
        """Преобразование данных пользователя в словарь для сохранения в JSON"""
        return {
                "user_id": self._user_id,
                "username": self._username,
                "hashed_password": self._hashed_password,
                "salt": self._salt,
                "registration_date": self._registration_date.isoformat(),
               }

class Wallet:
    """Кошелёк пользователя для одной валюты"""

    def __init__(self,
                 currency_code: str,
                 balance: float = 0.0,
                ) -> None:
        """Инициализация валютного кошелька"""
        self.currency_code = currency_code
        self.balance = balance

    # self._currency_code чтобы не было wallet.currency_code = ""
    # или wallet.currency_code = 123
    @property
    def currency_code(self) -> str:
        """Возврат кода валюты"""
        return self._currency_code

    @currency_code.setter
    def currency_code(self, value: str) -> None:
        """Установка кода валюты"""
        if not isinstance(value, str):
            raise TypeError("Код валюты должен быть строкой")

        value = value.strip().upper()

        if not value:
            raise ValueError("Код валюты не может быть пустым")

        self._currency_code = value

    @property
    def balance(self) -> float:
        """Вернуть текущий баланс кошелька"""
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        """Установить баланс кошелька"""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")

        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")

        self._balance = float(value)

    @staticmethod
    def _validate_amount(amount: float) -> float:
        """Проверить корректность суммы операции"""
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError("'amount' должен быть числом")

        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        return float(amount)

    def deposit(self, amount: float) -> None:
        """Пополнить баланс кошелька"""
        amount = self._validate_amount(amount)
        self.balance = self._balance + amount

    def withdraw(self, amount: float) -> None:
        """Снять средства с кошелька"""
        amount = self._validate_amount(amount)
        if amount > self._balance:
            raise ValueError(
                             "Недостаточно средств: "
                             f"доступно {self._balance:.4f} {self._currency_code}, "
                             f"требуется {amount:.4f} {self._currency_code}"
                            )

        self.balance = self._balance - amount

    def get_balance_info(self) -> dict:
        """Вернуть информацию о текущем балансе"""
        return {"currency_code": self._currency_code,
                "balance": self._balance,
               }

    def to_dict(self) -> dict:
        """Преобразовать кошелёк в словарь для json"""
        return {"currency_code": self._currency_code,
                "balance": self._balance,
               }

class Portfolio:
    """Портфель со всеми валютными кошельками пользователя"""

    def __init__(self,
                 user: User,
                 wallets: dict[str, Wallet] | None = None,
                ) -> None:
        """Инициализация портфеля пользователя"""
        if not isinstance(user, User):
            raise TypeError("user должен быть объектом User")

        self._user = user
        self._user_id = user.user_id
        self._wallets: dict[str, Wallet] = {}

        if wallets is not None:
            if not isinstance(wallets, dict):
                raise TypeError("wallets должен быть словарём")

            for currency_code, wallet in wallets.items():
                if not isinstance(wallet, Wallet):
                    raise TypeError("Все значения wallets должны быть объектами Wallet")

                code = currency_code.strip().upper()

                if code != wallet.currency_code:
                    raise ValueError(
                                     "Код валюты в словаре должен совпадать "
                                     "с currency_code кошелька"
                                    )

                self._wallets[code] = wallet

    @property
    def user(self) -> User:
        """Вернуть пользователя, которому принадлежит портфель"""
        return self._user

    @property
    def user_id(self) -> int:
        """Вернуть идентификатор пользователя"""
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Вернуть копию словаря кошельков"""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """Добавить новый валютный кошелёк в портфель"""
        if not isinstance(currency_code, str):
            raise TypeError("Код валюты должен быть строкой")

        currency_code = currency_code.strip().upper()

        if not currency_code:
            raise ValueError("Код валюты не может быть пустым")

        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк '{currency_code}' уже существует")

        wallet = Wallet(currency_code)
        self._wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """Возврат кошелька к по коду валюты"""
        if not isinstance(currency_code, str):
            raise TypeError("Код валюты должен быть строкой")

        currency_code = currency_code.strip().upper()

        if not currency_code:
            raise ValueError("Код валюты не может быть пустым")

        return self._wallets.get(currency_code)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Посчитать общую стоимость портфеля в базовой валюте"""
        if not isinstance(base_currency, str):
            raise TypeError("Базовая валюта должна быть строкой")

        base_currency = base_currency.strip().upper()

        if not base_currency:
            raise ValueError("Базовая валюта не может быть пустой")

        if base_currency not in DEFAULT_EXCHANGE_RATES:
            raise ValueError(f"Неизвестная базовая валюта '{base_currency}'")

        total_usd = 0.0

        for wallet in self._wallets.values():
            currency_code = wallet.currency_code

            if currency_code not in DEFAULT_EXCHANGE_RATES:
                raise ValueError(f"Неизвестный курс валюты '{currency_code}'")

            total_usd += (wallet.balance * DEFAULT_EXCHANGE_RATES[currency_code])

        return total_usd / DEFAULT_EXCHANGE_RATES[base_currency]

    def to_dict(self) -> dict:
        """Преобразование портфеля в словарь для сохранения в json"""
        return {
                "user_id": self._user_id,
                "wallets": {
                            currency_code: wallet.to_dict()
                            for currency_code, wallet in self._wallets.items()
                           }
               }