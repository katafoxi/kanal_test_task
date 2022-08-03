import time
import psycopg2
import requests

from googleapi import get_data_from_sheet
from psycopg2 import Error as DB_Error
from pycbrf.toolbox import ExchangeRates
from utills import get_config, get_time

PARAMS = get_config(section="postgresql")
WORK_PERIOD = 10
OLD_VALUES = None


def interrupt_it(func):
    def wrapper():
        try:
            func()
        except KeyboardInterrupt:
            print(f"{get_time()}[INFO] Спасибо, что выбрали уральские авиалинии!")

    return wrapper


@interrupt_it
def main():
    today = None
    global OLD_VALUES

    print("===================================")
    print("To exit please push Ctrl+C")
    print("===================================")

    create_table_db()
    OLD_VALUES = get_set_values_from_db()

    print(f"{get_time()}[INFO] Application start")

    connection = None
    try:
        connection = psycopg2.connect(**PARAMS)
        cursor = connection.cursor()

        cursor.execute("SET datestyle TO  dmy;")
        connection.commit()
        while True:
            if queue := get_queue():
                execute_query_to_db(cursor=cursor, queue=queue)
                connection.commit()
            if not today and today != time.strftime("%d-%m-%Y"):
                today = time.strftime("%d-%m-%Y")
                notifications = get_notification_from_db(today)
                send_telegram(notifications)

            time.sleep(WORK_PERIOD)  # work period

    except (Exception, DB_Error) as error:
        print(f"{get_time()}[ERR] ", error)

    finally:
        if connection:
            cursor.close()
            connection.close()
            print(f"{get_time()}[INFO] Database connection terminated")


def get_answer(question: str) -> bool:
    """
    Looping a question until you get the correct answer

    :param question:
    :return: bool
    """
    while True:
        user_input = input(f"{question}:(y/n) ")
        try:
            if user_input.lower() == "n":
                return False
            elif user_input.lower() == "y":
                return True
            else:
                raise ValueError
        except ValueError:
            print(r"¯\_(ツ)_/¯ incomprehensible answer")


def execute_query_to_db(cursor: object, queue: tuple) -> None:
    """
    формирует и исполняет запросы к БД на основе режима входных данных.
    generates and executes queries to the database based on the input data mode.

    :cursor: курсор подключения к БД
    :queue: tuple like a ( ('delete', {'30|1773045|977|27.05.2022', ...}),
                            ('insert', {'30|654665|654|27.05.6546',...})     )
    """
    rate = ExchangeRates()["USD"].value
    for sub_queue in queue:
        mod, collection = sub_queue

        for row in sorted(collection):
            id_, contract, price_usd, date = row.split("|")
            price_rub = int(price_usd) * rate

            if mod == "delete":
                sql_string = "DELETE FROM Contracts WHERE id = %s;"
                cursor.execute(sql_string, (id_,))
                print(f"{get_time()}[INFO] Delete entry={id_}")

            elif mod == "insert":
                sql_string = "INSERT INTO Contracts (id, contract, price_usd, price_rub, date)\
                            VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql_string, (id_, contract, price_usd, price_rub, date))
                print(f"{get_time()}[INFO] Insert entry with id={id_}")


def create_table_db() -> None:
    """
    Create table in database
    """
    connection = None
    try:
        connection = psycopg2.connect(**PARAMS)
        cursor = connection.cursor()
        sql_string = """ CREATE TABLE IF NOT EXISTS Contracts(
                            id integer NOT NULL  PRIMARY KEY,
                            contract integer NOT NULL,
                            price_usd integer NOT NULL,
                            price_rub decimal(10,2),
                            date date);"""

        cursor.execute(sql_string)
        connection.commit()
        cursor.execute("SET datestyle TO  dmy;")
        connection.commit()
        print(f"{get_time()}[INFO] Table ready")
    except (Exception, DB_Error) as error:
        print(f"{get_time()}[CREATE_TABLE_ERR] ", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print(f"{get_time()}[INFO] Database connection terminated")


def get_queue() -> tuple:
    """
    При первичном исполнении вносит множество в глобальную переменную VALUES.
    При последующем исполнении сравнивает VALUES и свежие данные из google sheet.
    В случае изменения данных в google sheet, формирует и возвращает разницу
    между тем, что уже есть в БД, и что есть в google sheet.
    Формирует минимальную очередь на запросы к БД в случае обновления исходных данных.
    :return: tuple like a ( ('delete', {'30|1773045|977|27.05.2022', ...}),
                            ('insert', {'30|654665|654|27.05.6546',...})     )

    """
    queue = tuple()
    global OLD_VALUES
    fresh_values = get_data_from_sheet()

    if fresh_values == OLD_VALUES:
        print(f"{get_time()}[INFO] No changes")
        return None

    else:
        queue += (("delete", OLD_VALUES - fresh_values),)
        queue += (("insert", fresh_values - OLD_VALUES),)
        OLD_VALUES = fresh_values
        return queue


def get_set_values_from_db():
    """
    :return: set values from db like a {'30|1773045|977|27.05.2022',..} or None
    """
    connection = psycopg2.connect(**PARAMS)
    cursor = connection.cursor()
    cursor.execute("SET datestyle TO  dmy;")
    connection.commit()
    sql_string = """ SELECT * FROM Contracts"""
    cursor.execute(sql_string)
    if cursor:
        mod_values = []
        for row in cursor:
            y, m, d = str(row[4]).split("-")
            date_dmy = f"{d}.{m}.{y}"
            row = f"{row[0]}|{row[1]}|{row[2]}|{date_dmy}"
            # print(row)
            mod_values.append(f"{row}")
        return set(mod_values)
    else:
        return None


def get_notification_from_db(today: str) -> str:
    """
    Проверка соблюдения «срока поставки». Принимает текущую дату и возвращает записи просроченных контрактов из БД.
    Checking compliance with the "delivery date".
    Accepts the current date and returns records of overdue contracts from the database.
    :param today: current date
    :return: string values of overdue contracts
    """
    notification = ""
    connection = None
    try:
        connection = psycopg2.connect(**PARAMS)
        cursor = connection.cursor()
        cursor.execute("SET datestyle TO  dmy;")
        connection.commit()
        sql_string = """ SELECT * FROM Contracts WHERE date < %s"""

        cursor.execute(sql_string, (today,))
        for row in cursor:
            # print(row[1])
            notification += f"Срок поставки по заказу {row[1]} прошел!\n"
        return notification
    except (Exception, DB_Error) as error:
        print(f"{get_time()}[NOTIFICATION_ERR] ", error)
    finally:
        if connection:
            cursor.close()
            connection.close()


def send_telegram(notification: str) -> requests:  # sourcery skip: raise-specific-error
    """
    Sends notifications about expired contracts to telegram

    :param notification: string values of overdue contracts
    """
    token = "5596509052:AAHo-BGVpi_e4cfad--61p2Qu_iAMUpeNSY"
    channel_id = "@db_notice"
    url = f"https://api.telegram.org/bot{token}"
    method = f"{url}/sendMessage"

    r = requests.post(method, data={"chat_id": channel_id, "text": notification})
    print(f"{get_time()}[INFO] Отправлено уведомление в телеграмм")

    if r.status_code != 200:
        raise Exception("post_text error")


if __name__ == "__main__":
    main()

