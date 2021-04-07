import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import datetime

# test
'''
# use creds to create a client to interact with the Google Drive API
# scope = ['https://spreadsheets.google.com/feeds']
scope = ['https://spreadsheets.google.com/feeds' + ' ' +'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_auth.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("top_albums_2_test").sheet1
'''

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


