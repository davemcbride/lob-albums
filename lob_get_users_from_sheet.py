import gspread
from oauth2client.service_account import ServiceAccountCredentials

def load_sheet():
    print("Connecting to Google Sheets...")
    # use creds to create a client to interact with the Google Drive API
    # scope = ['https://spreadsheets.google.com/feeds']
    scope = ['https://spreadsheets.google.com/feeds' + ' ' +'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_auth.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("LOB_01062021_1208").sheet1
    print("Done")
    return sheet

if __name__ == "__main__":
    # load albums
    sheet=load_sheet()

# get column 2
x = [item for item in sheet.col_values(2) if item]

# print column 2 list
for item in x:
    print(item)