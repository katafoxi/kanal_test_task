import msvcrt
import os.path

import google.auth
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
    filename = 'project.ini'
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
        if not today and today!=time.strftime("%d-%m-%Y") :
            today = time.strftime("%d-%m-%Y")
            notifications = get_notification_from_db(today)
            send_telegram(notifications)

        time.sleep(10)  # work period
        if msvcrt.kbhit():  # if key push
            k = ord(msvcrt.getch())  # read keycode
            if k == 27:  # if keycode = 'Escape'
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
                id_, order_num, cost_us, delivery_date = row.split('|')
                cost_ru = int(cost_us) * rate

                if mod == 'delete':
                    sql_string = f'DELETE FROM orders WHERE id = %s;'
                    cursor.execute(sql_string, (id_,))
                    print(get_time() + f'[INFO] Delete entry={id_}')

                elif mod == 'insert':
                    sql_string = 'INSERT INTO orders (id, order_num, cost_us, delivery_date, cost_ru)\
                                VALUES (%s, %s, %s, %s, %s)'
                    cursor.execute(sql_string, (id_, order_num, cost_us, delivery_date, cost_ru))
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
        sql_string = """ CREATE TABLE orders(
                            id integer NOT NULL  PRIMARY KEY,
                            order_num integer NOT NULL,
                            cost_us integer NOT NULL,
                            delivery_date date,
                            cost_ru decimal(10,2)); \n"""

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
        sql_string = f""" SELECT * FROM orders WHERE delivery_date < %s"""

        cursor.execute(sql_string,(today,))
        for row in cursor:
            # print(row[1])
            notification+=f'Срок поставки по заказу {row[1]} прошел!\n'
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


if __name__ == '__main__':
    # get_notification_from_db()
    # print(get_data_from_sheet())
    # VALUES = {'31|1581192|1474|17.05.2022', '9|1876515|1335|15.05.2022', '11|1465034|719|12.05.2022', '6|1135907|682|02.05.2022',
    #           '19|1888432|388|11.05.2022',
    #           '33|1844121|770|08.05.2022', '4|1060503|1804|29.05.2022', '30|1773045|977|27.05.2022', '27|1241924|1319|16.05.2022',
    #           '44|1592686|514|23.05.2022',
    #           '5|1617397|423|26.05.2022', '40|1897398|414|01.06.2022', '51|1426726|1997|21.05.2022', '23|1339024|341|12.05.2022',
    #           '50|1426726|1997|20.05.2022',
    #           '21|1938886|1021|03.05.2022', '26|1519872|1349|01.06.2022', '37|1915966|154|04.05.2022', '36|1615303|1242|22.05.2022',
    #           '34|1089979|1392|14.05.2022', '46|1485012|1124|09.05.2022', '10|1835607|1227|05.05.2022', '12|1077923|508|01.06.2022',
    #           '38|1287751|1891|17.05.2022', '14|1682035|1867|09.05.2022', '3|1120833|610|05.05.2022', '42|1168728|658|03.05.2022',
    #           '18|1917698|1322|25.05.2022', '17|1686040|129|01.06.2022', '35|1465628|1808|01.06.2022', '39|1498932|1162|21.05.2022',
    #           '29|1733144|392|22.05.2022', '15|1911795|1585|25.05.2022', '20|1430015|814|28.05.2022', '41|1810448|1668|11.05.2022',
    #           '45|1786437|618|28.05.2022', '24|1832176|1331|06.05.2022', '25|1554847|1755|20.05.2022', '47|1741017|514|16.05.2022',
    #           '1|1249708|675|24.05.2022',
    #           '7|1235370|1330|05.05.2022', '2|1182407|214|13.05.2022', '32|1021563|145|08.05.2022', '13|1968041|1600|21.05.2022',
    #           '22|1968437|1911|20.05.2022',
    #           '16|1028782|1377|19.05.2022', '49|1877503|124|29.05.2022', '28|1208915|168|01.05.2022', '43|1560222|1587|11.05.2022',
    #           '8|1329994|646|12.05.2022', '48|1497493|1198|30.05.2122'}
    # VALUES = get_data_from_sheet()

    # print(get_queue())
    main()
