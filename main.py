import datetime
import requests
import os
from ics import Calendar, Event


def loadData():                     #gibt Mensa Daten als JSON zurück
    url = "https://swp.webspeiseplan.de/index.php?token=55ed21609e26bbf68ba2b19390bf7961&model=menu&location=9601&languagetype=1&_=1699285225232"
    header = {"Referer": "https://swp.webspeiseplan.de/menu"}
    return requests.get(url=url, headers=header).json()

def formatPrice(price):             #formatiert den Preis in schön
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

def edit_event(event, angebot):
    current_date_time = datetime.datetime.today()

    event.last_modified = current_date_time
    event.description = angebot

    return event
def create_event(date, current_date_time, angebot):
    event = Event()
    event.name = "Mensa"
    event.begin = str(date) + "T113000Z"
    event.end = str(date) + "T123000Z"
    event.last_modified = current_date_time
    event.created = current_date_time
    event.description = angebot
    return event
def edit_calendar(angebote, path):
    with open(path, 'r') as ics_file:
        cal = Calendar(ics_file.read())

    for event in cal.events:        #überarbeiten, da der längst vergangene Events durchgeht, machen wie beim createn
        date_event = str(event.begin)[slice(10)]
        if str(date_event) in angebote:
            edit_event(event, angebote[date_event])

    #neue Events


def create_calender(angebote, path):
    if os.path.exists(path):
        current_date = datetime.date.today()
        current_date_time = datetime.datetime.today()
        date = current_date

        cal = Calendar()

        for i in range(14):
            if str(date) in angebote:
                cal.events.add(create_event(date, current_date_time,angebote[str(date)]))
            date = current_date + datetime.timedelta(days=i)

        return cal
    else:
        return edit_calendar(angebote, path)




wurst = open("halloNeu.txt", "w")
wurst.write(str(formatData(True)))
wurst.close()

#path = "/var/www/html/mensa.ics"
#essens_angebot = formatData(1)
#calendar = create_calender(essens_angebot, path)
#calendar.events.upate(create_calender(formatData(2)).events)
# Speichere den Kalender in einer Datei
#with open(path, 'w') as datei:
#    datei.writelines(calendar)