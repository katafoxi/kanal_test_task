import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


from utills import get_config, get_time

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
CREDENTIALS = get_config(section="googleAPI")["credentials_json_name"]
SPREADSHEET_ID = get_config(section="googleAPI")["spreadsheet_id"]
SHEET_RANGE = "Лист1!A2:E"


def get_creds():
    """

    :return: credential object to connect google api
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("secret/token.json"):
        creds = Credentials.from_authorized_user_file("secret/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("secret/token.json", "w") as token:
            token.write(creds.to_json())
    return creds


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
