import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import datetime
import re

# use creds to create a client to interact with the Google Drive API
# scope = ['https://spreadsheets.google.com/feeds']
scope = ['https://spreadsheets.google.com/feeds' + ' ' +'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_auth.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Load of Bands Album Challenge (Responses Test)").sheet1

# pick an album from the list file created by the other script
albums_master = open("album_list.txt", "r")
albums_list = albums_master.readlines()

# remove newline from the list
alist = []
for i in albums_list:
    alist.append(i.rstrip('\n'))
# print(alist)

# pick random album from the list
todays_album = random.choice(alist)
print("Today's album is: " + todays_album)

# write todays album to file
x = datetime.date.today()
f = open("daily_album_log.txt", "a")
f.write(str(x) + ": " + todays_album + "\n")

# remove todays album from the list
alist.remove(todays_album)

# overwrite the album file with the new list (minus today's album)
with open('album_list.txt', 'w') as filehandle:
    filehandle.writelines("%s\n" % album for album in alist)

# split album string into artist, album
artist_album_list = todays_album.split(" - ")
artist = artist_album_list[0]
album = artist_album_list[1]

# find matching cells for today's album

criteria_re = re.compile(album, re.IGNORECASE)
cell_list = sheet.findall(criteria_re)

# loop through all matching cells
# check the artist matches the expected artist for the matching album
# print the matching user from the same row
# print the matchin user's reason
for i in cell_list:
    row_number = i.row
    col_number = i.col
    # we have the row number that matches the album, user will be at start, artist at column to start, comment in the column to the right
    # check the artist is the adjacent cell matches that from the file (in case there are two albums by same artist or something else went wrong
    artist_sheet = sheet.cell(row_number, col_number - 1).value
    if artist.lower() != artist_sheet.lower():
        print("Artist name is not as expected for this album, are there two artists with the same album name?")
        print("Artist from file: " + artist.lower())
        print("Artist from sheet: " + artist_sheet.lower())
        print("Check Sheet: Row Num: " + str(row_number) + " Col Num: " + str(col_number))
    else:
       user = sheet.cell(row_number, 2).value
       print(user)
       # print user's reason
       reason = sheet.cell(row_number, col_number + 1).value
       print(reason)


