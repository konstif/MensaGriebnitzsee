import os
import requests
import datetime
import json
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


def getAttribut(ein_gericht, attribut_key):                             #bekommt den attribut_key und ein Gericht
    string_ohne_anfang = attribut_key.replace(attribut_key[:3], '').replace("]", '')

    match attribut_key[:2]:
        case "%n":
            preis = ein_gericht["zusatzinformationen"]["mitarbeiterpreisDecimal2"]
            match preis:
                case 2.15:
                    return "1" + attribut_key[2:]
                case 2.65:
                    return "2" + attribut_key[2:]
                case 3.15:
                    return "3" + attribut_key[2:]
                case 4.15:
                    return "4" + attribut_key[2:]
                case _:
                    return "5" + attribut_key[2:]
        case "%s":
            return ein_gericht["speiseplanAdvancedGericht"][string_ohne_anfang]
        case "%z":
            return ein_gericht["zusatzinformationen"][string_ohne_anfang]
        case "%c":
            return ein_gericht["zusatzinformationen"]["sustainability"]["co2"][string_ohne_anfang]

    if string_ohne_anfang in ein_gericht:
        return ein_gericht[string_ohne_anfang]
    else:
        return attribut_key.replace("%", "&")

def ersetzeVariabeln(msg, gericht):                                     #ersetzt Variabeln durch die konkreten Werte
    """
    test
    :param msg:
    :param gericht:
    :return:
    """
    if gericht["zusatzinformationen"]["mitarbeiterpreisDecimal2"] == 0:
        return ""

    while "%" in msg:
        key = msg[msg.index("%"):msg.index("]")+1] #erhalten ersten key
        msg = msg.replace(key, str(getAttribut(gericht, key)))
    return msg.replace("\r", "")

def erstelleWoche(msg, wochenplan, wochen_angebot):                                     #erstellt eine Liste mit allen Essensangeboten mit dem Datum als Key
    angebotWoche = wochen_angebot
    for gericht in wochenplan:
        datum = str(gericht["speiseplanAdvancedGericht"]["datum"])[slice(10)]  #liefert das Datum  ohne Uhrzeit
        if datum in angebotWoche:
            angebotWoche[datum] += ersetzeVariabeln(msg, gericht)
        else:
            angebotWoche[datum] = ersetzeVariabeln(msg, gericht)
    return angebotWoche

def createEvent(key, beschreibung, startzeit, endzeit):
    event = Event()
    event.name = "Mensa"
    event.begin = key + startzeit
    event.end = key + endzeit
    event.created = datetime.datetime.today()
    event.description = beschreibung
    return event
def createCalender(configCalender, abendessen, mittagessen):
    cal = Calendar()
    #Wochentage werden noch nicht aussortiert
    if configCalender["mittag_start"] is not None and configCalender["mittag_ende"] is not None:
        for key in mittagessen:
            cal.events.add(createEvent(key, mittagessen[key], configCalender["mittag_start"], configCalender["mittag_ende"]))

    if configCalender["abend_start"] is not None and configCalender["abend_ende"] is not None:
        for key in abendessen:
            cal.events.add(createEvent(key, abendessen[key], configCalender["abend_start"], configCalender["abend_ende"]))

    return cal

def getEssensplan(mittag, config_json):
    datajson = loadData()["content"]

    if not mittag:
        essens_zeit = "Mittag"
    else :
        essens_zeit = "Abend"

    essensplan = {}
    for wochenessen in datajson:
        if str(wochenessen["speiseplanAdvanced"]["titel"]).__contains__(essens_zeit):
            essensplan = erstelleWoche(config_json["Beschreibungstext"], wochenessen["speiseplanGerichtData"], essensplan)

    return essensplan


startpfad = "/var/www/konsti.store/mensa/"
pfad_jsons = startpfad + "config_files"
pfad_kalender = startpfad + "kalender"

config_jsons = os.listdir(pfad_jsons)
for config_json_name in config_jsons:
    with open(pfad_jsons + "/" + config_json_name, 'r') as datei:
        config_json = json.load(datei)

    mittag = getEssensplan(True, config_json)
    abend = getEssensplan(False, config_json)

    cal = createCalender(config_json, mittag, abend)
    with open(pfad_kalender + "/" + str(config_json_name)[:-5] + ".ics", 'w') as datei:
        datei.writelines(cal)