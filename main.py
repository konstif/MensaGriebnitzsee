import datetime
import requests
from ics import Calendar, Event


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

def formatData(woche):
    angebote = {}
    data_json = loadData()
    essen_der_Woche = data_json["content"][woche]["speiseplanGerichtData"] #erste Zahl 0: Abendessen Woche 1, 1: Mittag Woche 1, 2: Abendessen Woche 2, 3: Mittag Woche 2

    i = 0
    datum = ""
    angebot = ""
    for gericht_data in essen_der_Woche:
        gericht = gericht_data["speiseplanAdvancedGericht"]
        gericht_Datum = str(gericht["datum"])[slice(10)]

        if gericht_Datum != datum:
            angebote[datum] = angebot
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

    for i in range(14):
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

calendar = createCalender(formatData(1))
calendar.events.update(createCalender(formatData(2)).events)
# Speichere den Kalender in einer Datei
with open("/var/www/html/mensa.ics", 'w') as datei:
    datei.writelines(calendar)