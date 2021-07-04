## lob-albums

Process a Google Sheet that has been populated by Google Forms.  
The sheet contains lists of albums added by users with a comment about each album.  
Pick a random album each day including the comments from the users who chose it. 
Email the artist, album, users who chose and their comments every day.

**Needs auth file from Google Drive API which shouldn't be added to Github unless I've made a booboo**

### lob_albums_process_results.py 
 - script intended to run once, or a few times only when all submissions are in
 - outputs the unique albums to disk (full_album_list.txt) which will be used later to find albums for each day
 - script will also output the unique albums 
 - **at this point spelling mistakes or formatting issues should be identified and fixed manually**
 - **all punctuation etc should be identical for given artists and albums**

### lob_albums_daily_album.py
 - should be scheduled to run daily (cronjob on raspberry pi probably)
 - data is held in a Google spreadsheet populated by users via Google Forms
 - a count is maintained of number of times each user has been selected
 - the users who share the lowest count each day are eligible to be chosen today
 - random choice of those users each run
 - find a random album for the user from the sheet
 - remove the album from the working copy of the sheet
 - sometimes more than one user will pick the same album so search the sheet to find them
 - find the comments each user added for the albums
 - send an email with today's album 
 
### Additional files
Files with config and credentials that are required but not hosted on github:

 - google_api_auth.json - Google Sheets/Drive API access downloaded from Google APIs
 - config.env - email account config
 - user_counts.csv - initial copy of the stored counts per user populated from exporting data from the Google Sheet
