import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import datetime
from datetime import timedelta
import re
import configparser
import smtplib, ssl

print("Connecting to Google Sheets...")
# use creds to create a client to interact with the Google Drive API
# scope = ['https://spreadsheets.google.com/feeds']
scope = ['https://spreadsheets.google.com/feeds' + ' ' +'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_auth.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Load of Bands Album Challenge (Responses Test)").sheet1
print("Done")

print("Opening album list from filesystem...")
# pick an album from the list file created by the other script
albums_master = open("album_list.txt", "r")
albums_list = albums_master.readlines()
print("Done")

# remove newline from the list
alist = []
for i in albums_list:
    alist.append(i.rstrip('\n'))
# print(alist)

print("Picking today's album...")
# pick random album from the list
todays_album = random.choice(alist)
print("Done: " + todays_album)

print("Writing album to log file...")
# write todays album to file
x = datetime.date.today()
y = datetime.date.today() + timedelta(days=1)
f = open("daily_album_log.txt", "a")
f.write(str(y) + ": " + todays_album + "\n")
print("Done: daily_album_log.txt")

print("Removing today's album from remaining album list...")
# remove todays album from the list
alist.remove(todays_album)

# overwrite the album file with the new list (minus today's album)
with open('album_list.txt', 'w') as filehandle:
    filehandle.writelines("%s\n" % album for album in alist)
print("Done")

print("Finding album in Google Sheets..")
# split album string into artist, album
artist_album_list = todays_album.split(" - ")
artist = artist_album_list[0]
album = artist_album_list[1]

# find matching cells for today's album
criteria_re = re.compile(album, re.IGNORECASE)
cell_list = sheet.findall(criteria_re)

# loop through all matching cells
# check the artist matches the expected artist for the matching album

# initialise start of email message
message = """\
Subject: Load of Bands - Daily Album {date}

Today's album: {album}
""".format(date=y, album=todays_album)

# print the matching user from the same row
# print the matchin user's reason

# initialise user list
user_list = []

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
       reason = sheet.cell(row_number, col_number + 1).value
       
       # add todays pickers to list
       user_list.append("\n")
       user_list.append(user + "\n")
       user_list.append(reason)
       user_list.append('\n------\n')
print("Done")

print("Create and send email...")
# join the users and reasons
todays_users = "".join(user_list)
# print(todays_users)

message = message + todays_users
message_enc = message.encode(encoding='UTF-8',errors='ignore')
# print(message)

# email
# read config file
config = configparser.ConfigParser()
config.read('config.env')
from_email = config.get('CONF','FROM_EMAIL')
email_pass = config.get('CONF','EMAIL_PASS')
to_email = [(config.get('CONF','TO_EMAIL'), (config.get('CONF','TO_EMAIL_2')))]

port = 465  # For SSL

# Create a secure SSL context
context = ssl.create_default_context()

# send email
with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
    server.login(from_email, email_pass)
    server.sendmail(from_email, to_email, message_enc)

print("Done")
print("All done")
