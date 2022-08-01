# import msvcrt
import os.path
import sys
import time
from configparser import ConfigParser

import psycopg2
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from psycopg2 import Error as DB_Error
from pycbrf.toolbox import ExchangeRates
from os.path import exists

CONFIG_FILE="./project.ini"


def get_config(section: str) -> dict:    # sourcery skip: raise-specific-error
    """
    Получает данные из файла roject.ini
    :param section:
    :return: словарь '[имя_параметра]':'[значение]'
    """
    config_file = "./project.ini"
    if not exists(config_file):
        raise Exception(
            "Отсутствует ini файл"
        )
    parser = ConfigParser()  # create a parser
    parser.read(config_file)  # read configurate file
    if not parser.has_section(section):
        raise Exception(
            "Section {0} is not found in the {1} file.".format(section, config_file)
        )
    params = parser.items(section)
    return {param[0]: param[1] for param in params}


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
CREDENTIALS = get_config(section="googleAPI")["credentials_json_name"]
SPREADSHEET_ID = get_config(section="googleAPI")["spreadsheet_id"]
SHEET_RANGE = "Лист1!A2:E"
PARAMS = get_config(section="postgresql")
WORK_PERIOD = 10
VALUES = None


def main():
    today = None
    global VALUES
    print("===================================")
    print("To exit please push Escape/Ctrl+C")
    print("===================================")

    while not get_answer(question="Have you customized the project.ini file"):
        print("Please customize it. I'll wait")

    if get_answer(question='database based on Docker?'):
        if not get_answer(question='table already exists?'):
            create_table_db()
        else:
            VALUES = get_data_from_sheet()
    else:
        if not get_answer(question="database already exists?"):
            create_db()
            create_table_db()
        else:
            # если повторный старт с созданной и наполненной БД и не измененным google sheet, то
            VALUES = get_data_from_sheet()

    print("Application start\n\n")
    while True:

        if queue := get_queue():
            execute_query_to_db(queue)
        if not today and today != time.strftime("%d-%m-%Y"):
            today = time.strftime("%d-%m-%Y")
            notifications = get_notification_from_db(today)
            send_telegram(notifications)

        time.sleep(WORK_PERIOD)  # work period
        # if msvcrt.kbhit():  # if key push
        #     k = ord(msvcrt.getch())  # read keycode
        #     if k:  # if keycode = 'Escape'
        #         print("Application stop. Thanks for using")
        #         sys.exit()  # complete the program


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


def get_creds():
    """

    :return: credential object to connect google api
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_time() -> str:
    """

    :return: date as a string [hour:minute:second]
    """
    return "[" + time.strftime("%H:%M:%S") + "] "


def get_data_from_sheet():
    """
    Get data from sheet.

    :rtype: set
    :return: values from google sheet set {'30|1773045|977|27.05.2022', '19|1888432|388|11.05.2022',...}
    """
    try:
        service = build("sheets", "v4", credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE)
            .execute()
        )

        if values := result.get("values"):
            mod_values = []
            for row in values:
                row = "|".join(row)
                # print(row)
                mod_values.append(f"{row}")
            return set(mod_values)
        else:
            print(f"{get_time()}[ERR] No data found.")
            return
    except HttpError as err:
        print(err)


def execute_query_to_db(queue: tuple) -> None:
    """
    формирует и исполняет запросы к БД на основе режима входных данных.
    generates and executes queries to the database based on the input data mode.

    :param queue: tuple like a ( ('delete', {'30|1773045|977|27.05.2022', ...}),
                            ('insert', {'30|654665|654|27.05.6546',...})     )
    """
    rate = ExchangeRates()["USD"].value
    for sub_queue in queue:
        mod, collection = sub_queue
        connection = None
        try:
            connection = psycopg2.connect(**PARAMS)
            cursor = connection.cursor()

            cursor.execute("SET datestyle TO  dmy;")
            connection.commit()

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
                    cursor.execute(
                        sql_string, (id_, contract, price_usd, price_rub, date)
                    )
                    print(f"{get_time()}[INFO] Insert entry={id_}")

                connection.commit()

        except (Exception, DB_Error) as error:
            print(f"{get_time()}[ERR] ", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print(f"{get_time()}[INFO] Database connection terminated")


def create_db() -> None:
    """
    Create PostgreSQL database
    """
    params = get_config(section="postgresql")
    dbname = params.pop("dbname")  # retrieved to be able to create a database
    connection = None
    try:
        connection = psycopg2.connect(**params)
        connection.autocommit = True
        cursor = connection.cursor()
        sql_string = f"CREATE database {dbname};"
        cursor.execute(sql_string)
        print(f"{get_time()}[INFO] DB {dbname} created successfully")
    except (Exception, DB_Error) as error:
        print(f"{get_time()}[CREATE_DB_ERR] ", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print(f"{get_time()}[INFO] Database connection terminated")


def create_table_db() -> None:
    """
    Create table in database
    """
    connection = None
    try:
        connection = psycopg2.connect(**PARAMS)
        cursor = connection.cursor()
        sql_string = """ CREATE TABLE Contracts(
                            id integer NOT NULL  PRIMARY KEY,
                            contract integer NOT NULL,
                            price_usd integer NOT NULL,
                            price_rub decimal(10,2),
                            date date);"""

        cursor.execute(sql_string)
        connection.commit()
        cursor.execute("SET datestyle TO  dmy;")
        connection.commit()
        print(f"{get_time()}[INFO] Table created successfully")
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
    При последующем исполнии сравнивает VALUES и свежие данные из google sheet.
    В случае изменения данных в google sheet, формирует и возвращает разницу
    между тем, что уже есть в БД, и что есть в google sheet.
    Формирует минимальную очередь на запросы к БД в случае обновления исходных данных.
    :return: tuple like a ( ('delete', {'30|1773045|977|27.05.2022', ...}),
                            ('insert', {'30|654665|654|27.05.6546',...})     )

    """
    queue = tuple()
    global VALUES
    fresh_values = get_data_from_sheet()

    if not VALUES:
        VALUES = fresh_values
        queue += (("insert", VALUES),)
        return queue

    elif fresh_values == VALUES:
        print(f"{get_time()}[INFO] no changes")
        return None

    else:
        queue += (("delete", VALUES - fresh_values),)
        queue += (("insert", fresh_values - VALUES),)
        VALUES = fresh_values
        return queue


def get_notification_from_db(today: str) -> str:
    """
    Проверка соблюдения «срока поставки». Принимает текущую дату и возращает записи просроченных контрактов из БД.
    Checking compliance with the "delivery date". Accepts the current date and returns records of overdue contracts from the database.
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


def send_telegram(text: str) -> requests:    # sourcery skip: raise-specific-error
    """
    Sends notifications about expired contracts to telegram

    :param text: string values of overdue contracts
    """
    token = "5596509052:AAHo-BGVpi_e4cfad--61p2Qu_iAMUpeNSY"
    channel_id = "@db_notice"
    url = f"https://api.telegram.org/bot{token}"
    method = f"{url}/sendMessage"

    r = requests.post(method, data={"chat_id": channel_id, "text": text})

    if r.status_code != 200:
        raise Exception("post_text error")


if __name__ == "__main__":
    main()
