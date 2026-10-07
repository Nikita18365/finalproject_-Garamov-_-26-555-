import hashlib
import secrets
from datetime import datetime


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