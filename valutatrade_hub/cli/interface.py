import shlex

from valutatrade_hub.core.models import User
from valutatrade_hub.core.usecases import login, register


def _parse_options(tokens: list[str]) -> dict[str, str]:
    """Преобразование CLI-аргументов вида key value в словарь"""

    options = {}
    index = 0

    while index < len(tokens):
        token = tokens[index]

        if not token.startswith("--"):
            raise ValueError(f"Неожиданный аргумент '{token}'")
        key = token[2:]
        if not key:
            raise ValueError("Пустое имя аргумента")
        if index + 1 >= len(tokens):
            raise ValueError(f"Для аргумента '--{key}' не указано значение")

        value = tokens[index + 1]
        if value.startswith("--"):
            raise ValueError(f"Для аргумента '--{key}' не указано значение")
        options[key] = value
        index += 2

    return options


def _require_option(options: dict[str, str], name: str) -> str:
    """Получение обязательного аргумента команды"""
    value = options.get(name)
    if value is None:
        raise ValueError(f"Не указан обязательный аргумент '--{name}'")
    return value


def _handle_register(tokens: list[str]) -> None:
    """Обработка CLI-команды register"""

    options = _parse_options(tokens)
    username = _require_option(options, "username")
    password = _require_option(options, "password")

    user = register(username = username, password = password)

    print(
          f"Пользователь '{user.username}' "
          f"зарегистрирован (id={user.user_id})."
         )
    print(
          f"Войдите: login --username "
          f"{user.username} --password ****"
         )


def _handle_login(tokens: list[str]) -> User:
    """Обработка CLI-команды login"""

    options = _parse_options(tokens)
    username = _require_option(options, "username")
    password = _require_option(options, "password")

    user = login(username = username, password = password)
    print(f"Вы вошли как '{user.username}'")

    return user


def _show_help() -> None:
    """Показать список доступных CLI-команд"""

    print("Доступные команды:")
    print(
          "  register --username <имя> "
          "--password <пароль>"
         )
    print(
          "  login --username <имя> "
          "--password <пароль>"
         )
    print("  help")
    print("  exit")


def run() -> None:
    """Запуск основного цикла консольного приложения"""

    current_user = None
    print("ValutaTrade Hub")
    print("Введите 'help' для списка команд")

    while True:
        if current_user is None:
            prompt = "> "
        else:
            prompt = f"{current_user.username}> "

        try:
            command_line = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Завершение работы")
            break

        if not command_line:
            continue

        try:
            tokens = shlex.split(command_line)
        except ValueError as error:
            print(f"Ошибка команды: {error}")
            continue

        command = tokens[0].lower()
        arguments = tokens[1:]

        try:
            if command == "register":
                _handle_register(arguments)

            elif command == "login":
                current_user = _handle_login(arguments)

            elif command == "help":
                _show_help()

            elif command in {"exit", "quit"}:
                print("Завершение работы")
                break

            else:
                print(
                      f"Неизвестная команда '{command}'. "
                      "Введите 'help'"
                     )

        except (TypeError, ValueError) as error:
            print(error)


def main() -> None:
    """Запуск ValutaTrade Hub CLI"""
    run()