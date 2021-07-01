import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import datetime
from datetime import timedelta
import re
import configparser
import smtplib, ssl
import logging
import csv
import time


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


def find_users(album, sheet):

    # find matching cells for today's album
    criteria_re = re.compile(album, re.IGNORECASE)
    cell_list = sheet.findall(criteria_re)

    # loop through all matching cells
    # check the artist matches the expected artist for the matching album

    # initialise user list
    user_list = []

    for i in cell_list:
        row_number = i.row
        user = sheet.cell(row_number, 2).value
       
        # add todays pickers to list
        user_list.append(user)

    logging.debug("All matched users:{}".format(' '.join(map(str, user_list))))

    return(user_list, cell_list)
    

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


def find_user_reasons(sheet, cell_list):
    # this feels risky as we're divorcing the user_list and reason_list
    # be interesting to see if they join consistently especially when there are multiple users

    logging.debug("cells... {}".format(' '.join(map(str, cell_list))))

    reason_list=[]
    for i in cell_list:
        row_number = i.row
        col_number = i.col
        reason = sheet.cell(row_number, col_number + 1).value
        reason_list.append(reason)
        logging.debug("Reasons... {}".format(' '.join(map(str, reason_list))))
    return(reason_list)


def pick_user():
    logging.debug("Finding user for today...")
    in_file='user_counts.csv'
    users_counts={}

    # read csv to dict
    with open(in_file, mode='r') as inp:
        reader = csv.reader(inp)
        users_counts = {rows[0]:rows[1] for rows in reader}
    inp.close()

    # print dict line by line
    logging.debug("Input user dict:")
    logging.debug([print(key,':',value) for key, value in users_counts.items()])

    # sort dict by value
    sorted_users=dict(sorted(users_counts.items(), key=lambda item: item[1]))

    logging.debug("Sorted input user dict")
    logging.debug([print(key,':',value) for key, value in sorted_users.items()])

    # get first value (lowest count) in sorted dict
    values_view = sorted_users.values()
    value_iterator = iter(values_view)
    lowest_count_string = next(value_iterator)
    logging.info("Lowest count string:")
    logging.info(lowest_count_string)

    # get all keys with lowest count value
    lowest_users=[k for k,v in sorted_users.items() if v == lowest_count_string]
    logging.info("Users with lowest count today:")
    logging.info(lowest_users)

    today_user=random.choice(lowest_users)
    logging.info("Today's user")
    logging.info(today_user)

    # increment today_users count 
    lowest_count_int=int(lowest_count_string)
    new_count=lowest_count_int + 1
    logging.info("New, incrememented count:")
    logging.info(new_count)
    new_count_string=str(new_count)

    # update the dictonary with count
    users_counts[today_user] = new_count_string
    logging.debug("Today's user incrememented:")
    logging.debug(users_counts)

    # write csv to disk
    out_file = open("user_counts.csv", "w")

    writer = csv.writer(out_file)
    for key, value in users_counts.items():
        writer.writerow([key, value])
    out_file.close()
    logging.info("Wrote CSV file")

    return(today_user)


def pick_album_for_user(today_user, sheet):
    logging.info("Finding album from user list")
    # find user row

    logging.info("Trying to connect to Google: ")
    cell = sheet.find(today_user)
    logging.debug("Looking for user: " +today_user)
    logging.debug("Found user at R%sC%s" % (cell.row, cell.col))
    row_num = cell.row

    # pick random artist cell
    rand_artist_col_num=random.randrange(3,30,3)
    logging.debug("Random column number is: " + str(rand_artist_col_num))

    # today's artist - can't be blank
    today_artist = ""
    while not today_artist:
        attempts = 1
        print("Attempt: " + attempts)
        today_artist = sheet.cell(row_num, rand_artist_col_num).value
        # rate limit requests sent to Google or we'll get banned
        time.sleep(5)
        attempts +=1
        if attempts > 10:
            logging.error("Unable to find artist cell in sheet")
            quit()

    logging.debug("Today's arist is: " +today_artist)
    album_column = rand_artist_col_num + 1
    today_album = sheet.cell(row_num, album_column).value
    logging.debug("Today's album is: " +today_album)

    return(today_artist, today_album)


def delete_today_from_sheet(sheet, cell_list):
    for i in cell_list:
        row_number = i.row
        album_col_number = i.col
        artist_col_number = i.col - 1
        reason_col_number = i.col + 1
        # clear the found album
        logging.debug("Deleting album cell: " +str(row_number) +","+str(album_col_number))
        sheet.update_cell(row_number, album_col_number, '')
        logging.debug("Deleting artist cell: " +str(row_number) +","+str(artist_col_number))
        sheet.update_cell(row_number, artist_col_number, '')
        logging.debug("Deleting reason cell: " +str(row_number) +","+str(reason_col_number))
        sheet.update_cell(row_number, reason_col_number, '')


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

    today = datetime.date.today()
    logging.info("-----------------------")
    logging.info("Script running on: ")
    logging.info(today.strftime("%b %d %Y"))

    tomorrow = today + datetime.timedelta(days=1)
    album_date =(tomorrow.strftime("%b %d %Y"))
    
    # load speadsheet
    sheet=load_sheet()
    
    # pick user from list
    today_user=pick_user()
    print(today_user)

    # pick album from that user
    today_artist, today_album=pick_album_for_user(today_user, sheet)

    # check for other users with that album
    # the output cell_list is a list of coordinates of matached albums
    user_list, cell_list=find_users(today_album, sheet)
    reason_list=find_user_reasons(sheet, cell_list)

    # delete the album from the sheet
    delete_today_from_sheet(sheet, cell_list)

    # join users and reason lists
    for f,b in zip(user_list, reason_list):
        logging.debug("Today's user/reasons")
        logging.debug(f + " -- ", b)
    
    


    # create email
    today_artist, today_album=pick_album_for_user(today_user, sheet)
    encoded_message = create_email(today_artist, today_album, user_list, reason_list, album_date)

    # send email



    '''
    # pick today's album
    chosen_album=pick_album(alist)

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
        pass chosen_album=pick_album

    # search sheet for reason fields for todays album
    reason_list=find_user_reasons(cell_list, user_list)

    # write logs with today's album and users
    album_date=write_album_logs(chosen_album, user_list)

    # generate the email message
    email_message=create_email(chosen_album, user_list, reason_list, album_date)
    
    print(email_message)

    # send email
    send_email(email_message)
    '''
