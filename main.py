import datetime
import requests
from ics import Calendar, Event
import os

def loadData():                     #gibt Mensa Daten als JSON zurück
    url = "https://swp.webspeiseplan.de/index.php?token=55ed21609e26bbf68ba2b19390bf7961&model=menu&location=9601&languagetype=1&_=1699285225232"
    header = {"Referer": "https://swp.webspeiseplan.de/menu"}
    return requests.get(url=url, headers=header).json()

def formatPrice(price):
    price = str(price)
    length = len(price)
    if length == 1:
        price += ".00"
    if length == 3:
        price += "0"

    return price

def formatData(mittagessen):
    angebote = {}
    data_json = loadData()

    if mittagessen:
        essens_zeit = "1. Mittagessen"
    else :
        essens_zeit = "2. Abendessen"



    essen_data_zeit = data_json["content"]

    i = 0
    datum = ""
    angebot = ""
    for essen_data_zeit_einewoche in essen_data_zeit:
        if essen_data_zeit_einewoche["speiseplanAdvanced"]["titel"] == essens_zeit:
            essen_der_Woche = essen_data_zeit_einewoche["speiseplanGerichtData"]
            for gericht_data in essen_der_Woche:
                gericht = gericht_data["speiseplanAdvancedGericht"]
                gericht_Datum = str(gericht["datum"])[slice(10)]

                if gericht_Datum != datum:
                    angebote[datum] = angebot
                    print(datum, angebot)
                    angebot = ""

                    datum = gericht_Datum
                    i = 0

                if i>0:
                    angebot += "Angebot " + str(i) + " (" + formatPrice(gericht_data["zusatzinformationen"]["mitarbeiterpreisDecimal2"]) +"€):\n" + str(gericht["gerichtname"]).replace("\n", "") + "\n"
                i += 1

        angebote[datum] = angebot

    return angebote

def createCalender(angebote):
    current_date = datetime.date.today()
    current_date_time = datetime.datetime.today()
    date = current_date

    cal = Calendar()

    for i in range(1, 14):
        if str(date) in angebote:
            event = Event()
            event.name = "Mensa"
            event.begin = str(date) + "T113000Z"
            event.end = str(date) + "T123000Z"
            event.created = current_date_time
            event.description = angebote[str(date)]
            cal.events.add(event)
        date = current_date + datetime.timedelta(days=i)

    return cal


path = "/var/www/html/mensa.ics"
path = "mensa.ics"

# Kalender erstellen und .ics-Datei einlesen
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as file:
        old_calendar = Calendar(file.read())
else:
    old_calendar = Calendar()

new_calendar = createCalender(formatData(True))

for new_event in new_calendar.events:
    ist_nicht_drin = True
    for old_event in old_calendar.events:
       if new_event.begin == old_event.begin:
            ist_nicht_drin = False
    if ist_nicht_drin:
        old_calendar.events.add(new_event)




#calendar = old_calendar + new_calendar
#calendar.events = list(set(calendar.events))

# Speichere den Kalender in einer Datei
with open(path, 'w') as datei:
    datei.writelines(old_calendar)
