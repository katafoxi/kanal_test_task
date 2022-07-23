import msvcrt
import os.path

import requests
from pycbrf.toolbox import ExchangeRates
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import psycopg2
from psycopg2 import Error as DB_Error
from configparser import ConfigParser
import time
import sys


def get_config(section):
    filename = '../project.ini'
    parser = ConfigParser()  # create a parser
    parser.read(filename)  # read configurate file
    configurate = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            configurate[param[0]] = param[1]
    else:
        raise Exception('Section{0} is not found in the {1} file.'.format(section, filename))
    return configurate


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
CREDENTIALS = get_config(section='googleAPI')['credentials_json_name']
SPREADSHEET_ID = get_config(section='googleAPI')['spreadsheet_id']
SHEET_RANGE = 'Лист1!A2:E'
PARAMS = get_config(section='postgresql')
VALUES = None


def main():
    today = None
    global VALUES
    print('===================================')
    print('To exit please push Escape/Ctrl+C')
    print('===================================')

    while not get_answer(question='Have you customized the project.ini file'):
        print("Please customize it. I'll wait")
    if not get_answer(question='database already exists?'):
        create_db()
        create_table_db()
    else:
        VALUES = get_data_from_sheet()

    print('Application start\n\n')
    while True:

        queue = get_queue()
        if queue:
            execute_query_to_db(queue)
        if not today and today != time.strftime("%d-%m-%Y"):
            today = time.strftime("%d-%m-%Y")
            notifications = get_notification_from_db(today)
            send_telegram(notifications)

        time.sleep(10)  # work period
        if msvcrt.kbhit():  # if key push
            k = ord(msvcrt.getch())  # read keycode
            if k :  # if keycode = 'Escape'
                print('Application stop. Thanks for using')
                sys.exit()  # complete the program


def get_answer(question):
    while True:
        user_input = input(f'{question}:(y/n) ')
        try:
            if user_input.lower() == 'n':
                return False
            elif user_input.lower() == 'y':
                return True
            else:
                raise ValueError
        except ValueError:
            print('¯\_(ツ)_/¯ incomprehensible answer')


def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def get_time():
    time_to_log = '[' + time.strftime('%H:%M:%S') + '] '
    return time_to_log


def get_data_from_sheet():
    try:
        service = build('sheets', 'v4', credentials=get_creds())

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=SHEET_RANGE).execute()

        values = result.get('values')
        mod_values = []
        if not values:
            print(get_time() + '[ERR] No data found.')
            return
        else:
            for row in values:
                row = "|".join(row)
                # print(row)
                mod_values.append(f'{row}')
            return set(mod_values)
    except HttpError as err:
        print(err)


def execute_query_to_db(queue):
    rate = ExchangeRates()['USD'].value
    for sub_queue in queue:
        mod, collection = sub_queue
        connection = None
        try:
            connection = psycopg2.connect(**PARAMS)
            cursor = connection.cursor()

            for row in collection:
                id_, contract, price_usd, date = row.split('|')
                price_rub = int(price_usd) * rate

                if mod == 'delete':
                    sql_string = f'DELETE FROM Contracts WHERE id = %s;'
                    cursor.execute(sql_string, (id_,))
                    print(get_time() + f'[INFO] Delete entry={id_}')

                elif mod == 'insert':
                    sql_string = 'INSERT INTO Contracts (id, contract, price_usd, price_rub, date)\
                                VALUES (%s, %s, %s, %s, %s)'
                    cursor.execute(sql_string, (id_, contract, price_usd, price_rub, date))
                    print(get_time() + f'[INFO] Insert entry={id_}')

                connection.commit()

        except (Exception, DB_Error) as error:
            print(get_time() + '[ERR] ', error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print(get_time() + '[INFO] Database connection terminated')


def create_db():
    params = get_config(section='postgresql')
    dbname = params.pop('dbname')  # retrieved to be able to create a database
    connection = None
    try:
        connection = psycopg2.connect(**params)
        connection.autocommit = True
        cursor = connection.cursor()
        sql_string = f'CREATE database {dbname};'
        cursor.execute(sql_string)
        print(get_time() + f'[INFO] DB {dbname} created successfully')
    except (Exception, DB_Error) as error:
        print(get_time() + '[CREATE_DB_ERR] ', error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print(get_time() + '[INFO] Database connection terminated')


def create_table_db():
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
        print(get_time() + '[INFO] Table created successfully')
    except (Exception, DB_Error) as error:
        print(get_time() + '[CREATE_TABLE_ERR] ', error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print(get_time() + '[INFO] Database connection terminated')


def get_queue():
    queue = tuple()
    global VALUES
    fresh_values = get_data_from_sheet()

    if not VALUES:
        VALUES = fresh_values
        queue += ('insert', VALUES),
        return queue

    elif fresh_values == VALUES:
        print(get_time() + '[INFO] no changes')
        return None

    else:
        queue += ('delete', VALUES - fresh_values),
        queue += ('insert', fresh_values - VALUES),
        VALUES = fresh_values
        return queue


def get_notification_from_db(today):
    notification = ''
    connection = None
    try:
        connection = psycopg2.connect(**PARAMS)
        cursor = connection.cursor()
        sql_string = f""" SELECT * FROM Contracts WHERE date < %s"""

        cursor.execute(sql_string, (today,))
        for row in cursor:
            # print(row[1])
            notification += f'Срок поставки по заказу {row[1]} прошел!\n'
        return notification
    except (Exception, DB_Error) as error:
        print(get_time() + '[NOTIFICATION_ERR] ', error)
    finally:
        if connection:
            cursor.close()
            connection.close()


def send_telegram(text: str):
    token = "5596509052:AAHo-BGVpi_e4cfad--61p2Qu_iAMUpeNSY"
    url = "https://api.telegram.org/bot"
    channel_id = "@db_notice"
    url += token
    method = url + "/sendMessage"

    r = requests.post(method, data={
        "chat_id": channel_id,
        "text": text
    })

    if r.status_code != 200:
        raise Exception("post_text error")


def get_data_from_db():
    data_for_django = ''
    connection = None
    try:
        connection = psycopg2.connect(**PARAMS)
        cursor = connection.cursor()
        sql_string = f""" SELECT * FROM Contracts"""

        cursor.execute(sql_string)
        for row in cursor:
            date = str(row[4])
            year, month, day = date.split('-')
            date = f'{day}/{month}/{year}'

            # print(f'{day}/{month}/{year}')
            data_for_django += f'{date},"{row[2]}"\n'
        print(data_for_django)
        return data_for_django
    except (Exception, DB_Error) as error:
        print(get_time() + '[BD_ERR] ', error)
    finally:
        if connection:
            cursor.close()
            connection.close()


if __name__ == '__main__':
    main()
    # print(get_config('postgresql'))

