# Import libraries
import threading
from time import strftime
from bs4 import BeautifulSoup
from RTk import GPIO
import sqlite3
from datetime import datetime, timedelta

# setup GPIO PINS
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setwarnings(False)

# Define variables
pollcount = 0
increment = 1
statusPath = "PATH/nginx/html/status.html"
closed = datetime.now()
writeentry = True

# check if database is built and build SQL connection to sqlite database
con = sqlite3.connect("Database location")
cur = con.cursor()
cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' and name='" + datetime.now().strftime("%m/%d/%Y") +
            "_time_log';")
if cur.fetchone()[0] == 0:
    cur.execute("CREATE TABLE '" + datetime.now().strftime("%m/%d/%Y") + "_time_log' (in_time, out_time);")
con.commit()
con.close()


def checkstatus():
    # call f() again in pollTime seconds
    threading.Timer(increment, checkstatus).start()
    global pollcount
    global closed
    global writeentry
    # input_state = GPIO.input(17)
    if not GPIO.input(17):
        # Bathroom is closed
        updatehtml("Bathroom", 1)
        pollcount += increment
        closed = datetime.now()
        writeentry = True
    else:
        # Bathroom is open
        updatehtml("Bathroom", 0)
        if writeentry:
            writeentry = False
            contime = sqlite3.connect("PathtoDB")
            curtime = contime.cursor()
            curtime.execute("INSERT INTO '" + datetime.now().strftime("%m/%d/%Y") + "_time_log' (in_time, out_time) VALUES "
                    "('" + (closed + timedelta(0, pollcount*-1)).strftime("%H:%M:%S") + "','" + closed.strftime("%H:%M:%S")
                    + "')")
            contime.commit()
            contime.close()
        pollcount = 0


def updatehtml(bathroom, status):
    global pollcount
    with open(statusPath, "r+") as f:
        data = f.read()
        soup = BeautifulSoup(data, features="html.parser")
        div = soup.find('div', {'class': bathroom})
        divstate = soup.find('div', {'class': 'state'})
        divcount = soup.find('div', {'class': 'closedseconds'})
        divcount.string = str(pollcount)
        divstate.string = str(status)

        if status == 0:
            div['style'] = "background-color: #33CC33; font-size:xx-large;"
            div.string = bathroom + " is open as of " + strftime("%H:%M:%S %Y-%m-%d")

        if status == 1:
            if pollcount >= 600:
                div['style'] = "background-color: #FF0000; font-size:xx-large;"
                div.string = bathroom + " has been closed for " + str(pollcount) + " seconds."
            else:
                div['style'] = "background-color: #FFFF00; font-size:xx-large;"
                div.string = bathroom + " is closed as of " + strftime("%H:%M:%S %Y-%m-%d")

        html = soup.prettify("utf-8")
        with open(statusPath, "wb") as file:
            file.write(html)


# Set off timers
checkstatus()
