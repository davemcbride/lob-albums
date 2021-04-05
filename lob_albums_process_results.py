import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import Counter

# use creds to create a client to interact with the Google Drive API
# scope = ['https://spreadsheets.google.com/feeds']
scope = ['https://spreadsheets.google.com/feeds' + ' ' +'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_auth.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("top_albums_2_test").sheet1

# Extract and print all of the values
# list_of_hashes = sheet.get_all_records()
# print(list_of_hashes)

# pull the artist - album names into lists
album1_list = sheet.col_values(3)
album2_list = sheet.col_values(5)
album3_list = sheet.col_values(7)

# delete the spreadsheet header row
del album1_list[0]
del album2_list[0]
del album3_list[0]

# combine album lists into one
combined_albums = album1_list + album2_list + album3_list

print("all albums")
print(combined_albums)

print("unique albums")
unique_albums = set(combined_albums)
print(unique_albums)

with open('full_album_list.txt', 'w') as filehandle:
    filehandle.writelines("%s\n" % album for album in unique_albums)

print("count occurrences of albums")
count_albums = Counter(combined_albums)
print(count_albums)

