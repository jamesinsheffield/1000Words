"""
Run locally using:
$ python populatePSQL.py
Run on Heroku using:
$ heroku run python populatePSQL.py
This will populate the database table with initial data contained within the words.csv file.
***NB***: Running this script will first clear the table, including any modifications that have been
made to the data via the web app.
"""

from app import db
from app import Words
import csv

def yes_or_no(question):
    reply = str(input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("You did not enter one of 'y' or 'n'. Assumed 'n'.")

ans = yes_or_no("***WARNING***: Running this script will populate the database table with initial \
data contained within the words.csv file. IT WILL FIRST CLEAR THE TABLE, including any \
modifications that have been made to the data via the web app. Proceed?")

if(ans):
    #Delete current data (in reverse order of foreign key relationships):
    print("Deleting current data")
    Words.query.delete()
    db.session.commit()

    #Copy new data (in normal order):
    print("Copying new data")
    with open('words.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            db_row=Words(*row)
            db.session.add(db_row)
            db.session.commit()

    print("***SUCCESS***")
