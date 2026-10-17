import shlex

from prettytable import PrettyTable

from valutatrade_hub.core.exceptions import (
                                             ApiRequestError,
                                             CurrencyNotFoundError,
                                             InsufficientFundsError,
                                            )
from valutatrade_hub.core.models import User
from valutatrade_hub.core.usecases import (
                                           buy,
                                           get_portfolio_summary,
                                           get_rate,
                                           login,
                                           register,
                                           sell,
                                          )
from valutatrade_hub.infra.logging_config import parser_console_logging
from valutatrade_hub.parser.updater import RatesUpdater


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


def _format_rate(rate: float) -> str:
    """Отформатированный валютный курс для CLI"""
    if rate < 1:
        return f"{rate:.8f}"
    return f"{rate:.2f}"


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


def _handle_show_portfolio(tokens: list[str],
                           current_user: User | None
                          ) -> None:
    """Обработка CLI-команды show-portfolio"""

    if current_user is None:
        raise ValueError("Сначала выполните login")

    options = _parse_options(tokens)
    base_currency = options.get("base", "USD")
    # CLI ничего не рассчитывает. Он поулчает подготовленные данные и оформляет их:
    summary = get_portfolio_summary(current_user.user_id, base_currency)
    # Бизнес-логика должна оставаться в usecases.py, а CLI только оркестрировать вызовы
    # и показывать результат
    base_currency = summary["base_currency"]

    print(
          f"Портфель пользователя "
          f"'{summary['username']}' "
          f"(база: {base_currency}):"
         )

    if not summary["wallets"]:
        print("У пользователя пока нет кошельков.")
        print(
              f"Итого: "
              f"{summary['total_value']:,.2f} "
              f"{base_currency}"
             )
        return

    value_column = f"Стоимость, {base_currency}"
    table = PrettyTable(["Валюта", "Баланс", value_column])

    table.align["Валюта"] = "l"
    table.align["Баланс"] = "r"
    table.align[value_column] = "r"

    for wallet in summary["wallets"]:
        table.add_row([wallet["currency_code"],
                       f"{wallet['balance']:,.4f}",
                       f"{wallet['value_in_base']:,.2f}"
                      ])

    print(table)
    print(
          f"Итого: "
          f"{summary['total_value']:,.2f} "
          f"{base_currency}"
         )


def _handle_buy(tokens: list[str],
                current_user: User | None,
               ) -> None:
    """Обработка CLI-команды buy"""

    if current_user is None:
        raise ValueError("Сначала выполните login")

    options = _parse_options(tokens)

    currency_code = _require_option(options, "currency")
    amount_text = _require_option(options, "amount")

    try:
        # CLI получает всё как текст, а buy() ожидает уже число
        amount = float(amount_text)
    except ValueError as error:
        raise ValueError("'amount' должен быть положительным числом") from error

    result = buy(current_user.user_id, currency_code, amount)

    print(
          f"Покупка выполнена: "
          f"{result['amount']:.4f} "
          f"{result['currency_code']} "
          f"по курсу "
          f"{result['rate']:.2f} "
          f"{result['base_currency']}/"
          f"{result['currency_code']}"
         )

    print("Изменения в портфеле:")

    print(
          f"- {result['currency_code']}: "
          f"было {result['old_balance']:.4f} "
          f"-> стало {result['new_balance']:.4f}"
         )

    print(
          f"Оценочная стоимость покупки: "
          f"{result['estimated_cost']:,.2f} "
          f"{result['base_currency']}"
         )


def _handle_sell(tokens: list[str],
                 current_user: User | None,
                ) -> None:
    """Обработка CLI-команды sell"""

    if current_user is None:
        raise ValueError("Сначала выполните login")

    options = _parse_options(tokens)

    currency_code = _require_option(options, "currency")
    amount_text = _require_option(options, "amount")

    try:
        amount = float(amount_text)
    except ValueError as error:
        raise ValueError("'amount' должен быть положительным числом") from error

    result = sell(current_user.user_id, currency_code, amount)

    print(
          f"Продажа выполнена: "
          f"{result['amount']:.4f} "
          f"{result['currency_code']} "
          f"по курсу "
          f"{result['rate']:.2f} "
          f"{result['base_currency']}/"
          f"{result['currency_code']}"
         )

    print("Изменения в портфеле:")

    print(
          f"- {result['currency_code']}: "
          f"было {result['old_balance']:.4f} "
          f"-> стало {result['new_balance']:.4f}"
         )

    print(
          f"Оценочная выручка: "
          f"{result['estimated_revenue']:,.2f} "
          f"{result['base_currency']}"
         )


def _handle_get_rate(tokens: list[str]) -> None:
    """Обработка CLI-команды get-rate"""

    options = _parse_options(tokens)
    from_code = _require_option(options, "from")
    to_code = _require_option(options, "to")
    result = get_rate(from_code, to_code)
    rate_text = _format_rate(result["rate"])
    reverse_rate_text = _format_rate(result["reverse_rate"])

    print(
          f"Курс "
          f"{result['from_currency']}->"
          f"{result['to_currency']}: "
          f"{rate_text} "
          f"(обновлено: {result['updated_at']})"
         )

    print(
          f"Обратный курс "
          f"{result['to_currency']}->"
          f"{result['from_currency']}: "
          f"{reverse_rate_text}"
         )


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
    print(
          "  show-portfolio [--base <валюта>]"
         )
    print(
          "  buy --currency <валюта> "
          "--amount <количество>"
         )
    print(
          "  sell --currency <валюта> "
          "--amount <количество>"
         )
    print(
          "  get-rate --from <валюта> "
          "--to <валюта>"
         )
    print("  update-rates")
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

            elif command == "show-portfolio":
                _handle_show_portfolio(arguments, current_user)

            elif command == "buy":
                _handle_buy(arguments, current_user)

            elif command == "sell":
                _handle_sell(arguments, current_user)

            elif command == "get-rate":
                _handle_get_rate(arguments)

            # update-rates->проверить, что нет аргументов->
            # RatesUpdater()->with parser_console_logging()->
            # run_update()->посмотреть result["errors"]->
            # print(итог)
            elif command == "update-rates":
                if arguments:
                    raise ValueError("Команда update-rates не принимает аргументы")
                updater = RatesUpdater()
                with parser_console_logging():
                    result = updater.run_update()
                errors = result["errors"]
                if errors:
                    print(
                          "Обновление завершено с ошибками. "
                          "Подробности смотрите в logs/parser.log"
                         )
                else:
                    print(
                          "Курсы успешно обновлены: "
                          f"{result['updated_count']}."
                         )
                print(
                      "Время обновления: "
                      f"{result['last_refresh']}"
                     )

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
        
        except InsufficientFundsError as error:
            print(error)

        except CurrencyNotFoundError as error:
            print(error)
            print("Проверьте код валюты и повторите команду")

        except ApiRequestError as error:
            print(error)
            print(
                  "Повторите попытку позже "
                  "или проверьте подключение к сети."
                 )

        except (TypeError, ValueError) as error:
            print(error)


def main() -> None:
    """Запуск ValutaTrade Hub CLI"""
    run()