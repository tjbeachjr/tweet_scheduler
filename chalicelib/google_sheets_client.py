import gspread
import logging
import os
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', logging.INFO))


class GoogleSheetsClientException(Exception):
    pass


class GoogleSheetsClient:

    def __init__(self, credentials):
        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
        self.gclient = gspread.authorize(credentials)

    def read_from_spreadsheet(self, spreadsheet_key, worksheet_number):
        try:
            spreadsheet = self.gclient.open_by_key(spreadsheet_key)
        except gspread.SpreadsheetNotFound:
            logger.error(f'Unable to open spreadsheet: {spreadsheet_key}')
            raise GoogleSheetsClientException
        worksheet = spreadsheet.get_worksheet(worksheet_number)
        return worksheet.get_all_values()
