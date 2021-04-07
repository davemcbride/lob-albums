import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import Counter

# use creds to create a client to interact with the Google Drive API
# scope = ['https://spreadsheets.google.com/feeds']
print("Pulling data from Google Sheets...")
scope = ['https://spreadsheets.google.com/feeds' + ' ' +'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_auth.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Load of Bands Album Challenge (Responses Test)").sheet1
print("Done")

print("Processing album list...")
# create a lists of all the artists
artist_list = sheet.col_values(3)
for i in range(6,30,3):
    artist_list = artist_list + sheet.col_values(i)

album_list = sheet.col_values(4)
for i in range(7,31,3):
    album_list = album_list + sheet.col_values(i)

# delete spreadsheet header row
val = 'Artist'
# filter the list to remove header string 'Artist'
artist_list = [i for i in artist_list if i != val]
# filter list to remove header string 'Album Title'
val = 'Album Title'
album_list = [i for i in album_list if i != val]

# error if the artist list and album list are not the same length
if len(artist_list) != len(album_list):
    print("The number of artists and albums do not match")
    print("Artists count: " + str(len(artist_list)))
    print("Albums count: " + str(len(album_list)))
    print(artist_list)
    print(album_list)
    quit()

# combine artist album lists to artist - album
artist_album_list = []
for i in range(len(artist_list)):
    artist_album_list.append(artist_list[i] + " - " +  album_list[i])

# print(artist_album_list)

# lowercase the albums to handle varying case in input
artist_album_list_lower = [each_string.lower() for each_string in artist_album_list]
print("Done")

print("Generating stats...")
# get list of unqiue albums
unique_albums = set(artist_album_list_lower)

# print count of unique albums
print("There were " + str(len(artist_album_list_lower)) + " albums submitted")
print("There were " + str(len(unique_albums)) + " unique albums")
print("Done")

print("Writing album list to disk...")
# write the unique list out to file for later use
with open('album_list.txt', 'w') as filehandle:
    filehandle.writelines("%s\n" % album for album in unique_albums)
print("Done...album_list.txt")

print("Counting unique albums...")
# count the occurrences of each album
print("count occurrences of albums:")
count_albums = Counter(artist_album_list_lower)

for key, value in count_albums.items():
    print(value, ' : ', key)
