import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import datetime
from datetime import timedelta
import re
import configparser
import smtplib, ssl


def load_albums():
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
    return(alist, sheet)


def pick_album(alist):
    print("Picking today's album...")
    # pick random album from the list
    chosen_album = random.choice(alist)
    print("Picked: " + chosen_album)
    return chosen_album


def find_users(chosen_album, sheet):
    print("Finding album in Google Sheets..")
    # split album string into artist, album
    artist_album_list = chosen_album.split(" - ")
    artist = artist_album_list[0]
    album = artist_album_list[1]

    # find matching cells for today's album
    criteria_re = re.compile(album, re.IGNORECASE)
    cell_list = sheet.findall(criteria_re)

    # loop through all matching cells
    # check the artist matches the expected artist for the matching album

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
       
        # add todays pickers to list
        user_list.append(user)

    print("Done")
    return(user_list, cell_list)
    

def write_album_logs(chosen_album, user_list):
    print("Writing album to log file...")
    # write todays album to file
    x = datetime.date.today()
    y = datetime.date.today() + timedelta(days=1)
    f = open("daily_album_log.txt", "a")
    f.write(str(y) + ": " + chosen_album + "\n")
    print("Done: daily_album_log.txt")

    print("Removing today's album from remaining album list...")
    # remove todays album from the list
    alist.remove(chosen_album)

    # overwrite the album file with the new list (minus today's album)
    with open('album_list.txt', 'w') as filehandle:
        filehandle.writelines("%s\n" % album for album in alist)
    print("Done")
    
    # write today's users to file so we can check for repeats tomorrow
    with open('last_user.txt', 'w') as filehandle:
        for item in user_list:
            filehandle.write("%s\n" % item)
    
    # return tomorrow's date for the email
    return(y)


def create_email(chosen_album, user_list, reason_list, album_date):
    print("Create and send email...")

    message = """\
    Subject: Load of Bands - Daily Album for {date}

    Tomorrow's album: {album}
    """.format(date=album_date, album=chosen_album)

    # print the matching user from the same row
    # print the matchin user's reason

    for n in user_list, reason_list:
        message = message + user_list[n]
        message = message + reason_list[n]
    
    message_enc = message.encode(encoding='UTF-8',errors='ignore')
    # print(message)
    return message_enc


def send_email(message_enc):
    # read config file
    config = configparser.ConfigParser()
    config.read('config.env')
    from_email = config.get('CONF','FROM_EMAIL')
    email_pass = config.get('CONF','EMAIL_PASS')
    to_email = config.get('CONF','TO_EMAIL')
    to_email2 = config.get('CONF','TO_EMAIL_2')
    recipients = to_email + ', ' + to_email2

    port = 465  # For SSL

    # Create a secure SSL context
    context = ssl.create_default_context()

    # send email
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(from_email, email_pass)
        server.sendmail(from_email, recipients, message_enc)

    print("Done")
    print("All done")


def check_if_user_was_last(user_list):
    # pick an album from the list file created by the other script
    last_user_file = open("last_user.txt", "r")
    last_user_list = last_user_file.readlines()

    ulist = []
    for i in last_user_list:
        ulist.append(i.rstrip('\n'))

    # check if any matches between today's user_list and yesterday's ulist
    matches = set(user_list) & set(ulist)
    # print(matches)
    if len(matches) != 0:
        # print('Same user was picked yesterday')
        return True
    else:
        return False


def find_user_reasons(sheet, cell_list):
    # this feels risky as we're divorcing the user_list and reason_list
    # be interesting to see if they join consistently especially when there are multiple users
    reason_list=[]
    for i in cell_list:
        row_number = i.row
        reason = sheet.cell(row_number, col_number + 1).value
        reason_list.append(reason)
    return(reason_list)


if __name__ == "__main__":
    # load albums
    alist=load_albums()

    # pick today's album
    chosen_album, sheet=pick_album(alist, sheet)

    # find users who picked toady's album
    user_list, cell_list=find_users(chosen_album, sheet)

    # check if any of the users in the list were up yesterday
    # want to avoid the same user on consecutive days if possible
    # if repeat_user == True they were up yesterday
    repeat_user=check_if_user_was_last(user_list)

    # try to find a new user a max of 2 times
    retries = 2
    if repeat_user==True:
        while retries > 0:
            chosen_album, sheet=pick_album(alist, sheet)
            retries -= 1
    else:
        # continue with today's album and user_list
        pass

    # search sheet for reason fields for todays album
    reason_list=find_user_reasons(cell_list, user_list)

    # write logs with today's album and users
    album_date=write_album_logs(chosen_album, user_list)

    # generate the email message
    email_message=create_email(chosen_album, user_list, reason_list, album_date)

    # send email
    send_email(email_message)
