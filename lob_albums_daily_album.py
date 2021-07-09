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
    scope = ['https://spreadsheets.google.com/feeds' + ' ' + 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_api_auth.json', scope)
    client = gspread.authorize(creds)

    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("LOB_0207221_Rel2").sheet1
    # sheet = client.open("LOB_01062021_1208_TEST").sheet1
    return sheet


def find_all_users(album, sheet):
    logging.debug("---Checking for additional users for today's album---")
    # some users have picked the same album so we need to find everyone who picked today's album
    # find matching cells for today's album
    criteria_re = re.compile(album, re.IGNORECASE)
    cell_list = sheet.findall(criteria_re)
    logging.debug("All matched album cells:{}".format(' '.join(map(str, cell_list))))

    # loop through all matching cells
    # initialise user_reason list
    user_reason_list = []

    # initialise list for just users
    user_only_list = []

    for i in cell_list:
        row_number = i.row
        col_number = i.col
        # sometimes the album name will be same as artist (e.g. vampire weekend, which screws this up)
        # pass the album column numbers in as a list to check the match against

        album_column_list = [4, 7, 10, 13, 16, 19, 22, 25, 28, 31]

        logging.debug("Column number: " + str(col_number))

        if col_number in album_column_list:
            user = sheet.cell(row_number, 2).value
            reason = sheet.cell(row_number, col_number + 1).value
            # handle if no reason was submitted
            if reason is None:
                reason = '---No reason provided---'
        else:
            pass
            logging.info("The album name matched a non-album cell but this should be ignored...hopefully")
            user = 'not_a_real_user'
            reason = 'not_a_real_reason'
        # add today's pickers to list with their reason cell
        user_reason_list.append("\n")
        user_reason_list.append(user + "\n")
        user_reason_list.append(reason)
        user_reason_list.append('\n------\n')
        logging.debug("User reason list:")
        logging.debug(user_reason_list)

        # also add just the user to the list
        user_only_list.append(user)
        logging.debug("User only list:")
        logging.debug(user_only_list)

    # this seems like a bad way to do this byt hey ho
    # remove the dummy string not_a_real_user
    clean_list = []
    for i in user_reason_list:
        if 'not_a_real' in i:
            pass
        else:
            clean_list.append(i)

    # do the same for the user_only_list
    clean_user_only_list = []
    for i in user_only_list:
        if 'not_a_real' in i:
            pass
        else:
            clean_user_only_list.append(i)

    logging.debug("All matched users and reasons. Dummy users removed:{}".format(' '.join(map(str, clean_list))))

    # if list is empty
    # join the user_reason_list to make...something
    try:
        todays_user_messages = "".join(clean_list)
    except:
        todays_user_messages = "ERROR: Something went wrong trying to get comments"

    logging.debug("Joined user and reason list: " + todays_user_messages)

    # return the users + reasons and all cells for today's album
    return (todays_user_messages, cell_list, clean_user_only_list)


def create_email(today_artist, today_album, todays_user_messages, album_date):

    logging.info("---Creating email---")

    message = """\
    Subject: Load of Bands - Daily Album for {date}


    Tomorrow's album: {artist} - {album}
    """.format(date=album_date, album=today_album, artist=today_artist)

    message = message + todays_user_messages
    logging.debug("Pre-encoding email: " + message)

    # encode for some reason I have forgotten. bad chars or something
    message_enc = message.encode(encoding='UTF-8', errors='ignore')

    return message_enc


def send_email(message_enc):
    # read config file
    config = configparser.ConfigParser()
    config.read('config.env')
    from_email = config.get('CONF', 'FROM_EMAIL')
    email_pass = config.get('CONF', 'EMAIL_PASS')
    to_email = config.get('CONF', 'TO_EMAIL')
    to_email2 = config.get('CONF', 'TO_EMAIL_2')
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


def pick_user():
    logging.debug("---Pick user---")
    logging.debug("Finding user for today...")
    in_file = 'user_counts.csv'
    users_counts = {}

    # read csv to dict
    with open(in_file, mode='r') as inp:
        reader = csv.reader(inp)
        users_counts = {rows[0]: rows[1] for rows in reader}
    inp.close()

    # print dict line by line
    logging.debug("Input user dict:")
    logging.debug(users_counts)

    # sort dict by value
    sorted_users = dict(sorted(users_counts.items(), key=lambda item: item[1]))

    logging.debug("Sorted input user dict")
    logging.debug(sorted_users)

    # get first value (lowest count) in sorted dict
    values_view = sorted_users.values()
    value_iterator = iter(values_view)
    lowest_count_string = next(value_iterator)
    logging.info("Lowest count string:")
    logging.info(lowest_count_string)

    # get all keys with lowest count value
    lowest_users = [k for k, v in sorted_users.items() if v == lowest_count_string]
    logging.info("Users with lowest count today:")
    logging.info(lowest_users)

    today_user = random.choice(lowest_users)
    logging.info("Today's user")
    logging.info(today_user)

    return (today_user)


def pick_album_for_user(today_user, sheet):
    logging.info("---Finding album for today's user---")
    # find user row

    logging.info("Trying to connect to Google: ")
    cell = sheet.find(today_user)
    logging.debug("Looking for user: " + today_user)
    logging.debug("Found user at R%sC%s" % (cell.row, cell.col))
    row_num = cell.row

    # today's artist - can't be blank
    attempts = 1
    max_attempts = 12
    today_artist = ""

    # generate a list of the album fields
    artist_fields = []
    for i in range(3, 33, 3):
        artist_fields.append(i)

    while not today_artist:
        # pick random artist cell
        this_artist_col = random.choice(artist_fields)
        logging.debug("Random column number is: " + str(this_artist_col))

        # remove the choice from the list so we don't try again
        artist_fields.remove(this_artist_col)

        print("Connecting to Google attempting to find artist: " + str(attempts) + "/" + str(max_attempts))
        print("Random column number: " + str(this_artist_col))
        today_artist = sheet.cell(row_num, this_artist_col).value
        # rate limit requests sent to Google or we'll get banned if something goes wrong
        time.sleep(3)
        attempts += 1
        if attempts > max_attempts:
            logging.error("Unable to find artist cell in sheet")
            quit()

    logging.debug("Today's artist is: " + today_artist)

    # album is adjacent to artist column
    album_column = this_artist_col + 1
    today_album = sheet.cell(row_num, album_column).value
    logging.debug("Today's album is: " + today_album)

    return (today_artist, today_album)


def delete_today_from_sheet(sheet, cell_list):
    logging.info("---Clear the cells for today's album---")
    logging.debug("All matched users and reasons. Dummy users removed:{}".format(' '.join(map(str, cell_list))))

    album_column_list = [4, 7, 10, 13, 16, 19, 22, 25, 28, 31]

    for i in cell_list:
        row_number = i.row   
        album_col_number = i.col

        # pass the album match cell list through valid album columns to prevent accidental delete of cells as the artist matches the album name
        if album_col_number in album_column_list:   
            artist_col_number = i.col - 1
            reason_col_number = i.col + 1
            # clear the found album
            logging.debug("Deleting album cell: " + str(row_number) + "," + str(album_col_number))
            sheet.update_cell(row_number, album_col_number, '')
            logging.debug("Deleting artist cell: " + str(row_number) + "," + str(artist_col_number))
            sheet.update_cell(row_number, artist_col_number, '')
            logging.debug("Deleting reason cell: " + str(row_number) + "," + str(reason_col_number))
            sheet.update_cell(row_number, reason_col_number, '')


def increment_user_count(user_list):
    logging.debug("---Incrementing user counts---")

    # pass in a list of users whose count should be incremeneted
    logging.debug("Users to be incrememnted:")
    logging.debug(user_list)

    # open the csv file
    in_file = 'user_counts.csv'
    users_counts = {}

    # read csv to dict
    with open(in_file, mode='r') as inp:
        reader = csv.reader(inp)
        users_counts = {rows[0]: rows[1] for rows in reader}
    inp.close()

    for u in user_list:
        # get the users current count
        old_count = users_counts.get(u)
        old_count_int = int(old_count)
        new_count_int = old_count_int + 1
        new_count = str(new_count_int)
        # update the dictionary with count
        users_counts[u] = new_count
        logging.debug(u + " - old count: " + old_count + " new count: " + new_count)

    # write csv to disk
    out_file = open("user_counts.csv", "w")

    writer = csv.writer(out_file)
    for key, value in users_counts.items():
        writer.writerow([key, value])
    out_file.close()
    logging.info("Wrote CSV file")


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s')

    x = datetime.date.today()
    y = datetime.date.today() + timedelta(days=1)
    logging.info("-----------------------")
    logging.info("Script running on: " + str(x) + "for: " + str(y))

    album_date = y

    # load spreadsheet
    sheet = load_sheet()

    # pick user from list
    today_user = pick_user()

    # pick album from that user
    today_artist, today_album = pick_album_for_user(today_user, sheet)

    # check for other users with that album
    todays_user_messages, cell_list, user_only_list = find_all_users(today_album, sheet)

    # incremement additional users
    increment_user_count(user_only_list)

    # delete the album from the sheet so we don't get it again
    delete_today_from_sheet(sheet, cell_list)

    # create email
    encoded_message = create_email(today_artist, today_album, todays_user_messages, album_date)

    # send email
    send_email(encoded_message)
