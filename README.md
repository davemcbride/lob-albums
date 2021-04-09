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
 - input1 should be the spreadsheet - can be read from google sheets or offline copy
 - input2 is the list of unique albums
 - script should pick an album from the uniq list
 - find the album for today in the sheet
 - pick the username(s) from the same row, pick the comment(s) in the adjacent cell
 - remove the album from the list and save remaining albums to disk
 - email the day's pick with names and comments
 
### Additional files
Files with config and credentials that are required but not hosted on github:

 - google_api_auth.json - Google Sheets/Drive API access downloaded from Google APIs
 - config.env - email account config
