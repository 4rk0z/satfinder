#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © arkoz 2021

import logging
from logging import handlers
import os
import sys
import ssl
import socket
import datetime
import ephem
import maidenhead
from math import degrees
import re
import shlex
import argparse


VERBOSE = True


def logprepare():
    path = "logi/"
    if not os.path.exists(path):
        os.makedirs(path)
    with open(path + botnick + '.log', 'a'):
        pass
    logrotate = logging.handlers.RotatingFileHandler(
        filename=path + botnick + '.log',
        mode='a',
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding=None,
        delay=0
    )
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)-25s %(levelname)-8s %(message)s",
        datefmt="%y-%m-%d %H:%M:%S",
        handlers=[logrotate]
    )
    return logging.getLogger(botnick)


def connect(server, channel, botnick, password):
    ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ircsock = ctx.wrap_socket(sock)
    ircsock.connect((server, 6697))
    ircsock.send(bytes("USER {b} {b} {b} {b}\n".format(b=botnick), 'utf-8'))
    ircsock.send(bytes("NICK {b}\n".format(b=botnick), 'utf-8'))
    ircsock.send(bytes("nickserv identify {p}\r\n".format(p=password), 'utf-8'))
    return ircsock


def pong():
    ircsock.send(b"PONG :pingis\n")
    logger.debug("PONG")


def sendmsg(msg, chan):
    ircsock.send(bytes("PRIVMSG {c} :{m}\n".format(c=chan, m=msg), 'utf-8'))
    logger.debug(">>> PRIVMSG {c} :{m}".format(c=chan, m=msg))


def joinchan(chan):
    ircsock.send(bytes("JOIN {ch}\n".format(ch=chan), 'utf-8'))
    logger.debug("JOIN {ch}".format(ch=chan))


def help(chan):
    message = ("składnia - !{b} 'n' qth h el c , " + \
    "gdzie n-nazwa obiektu (np. ISS, NOAA nr), " + \
    "qth - QTHlocator (maidenhead), " + \
    "h - wysokość n.p.m <0-8849>, " + \
    "el. - minimalny kąt elewacji w stopniach <10-90>, " + \
    "c - oczekiwana liczba wyników <1-5> ").format(b=botnick)
    sendmsg(message, chan)


def TLE(satellite):
    tle_sat = []
    with open("tle.txt", 'r') as tle_file:
        tle = tle_file.read()
    tle_file.close()
    tle = tle[:-1].split("\n")
    for tle_line0, tle_line1, tle_line2 in zip(
            tle[0::3], tle[1::3], tle[2::3]):
        if satellite in tle_line0.strip():
            return ephem.readtle(tle_line0, tle_line1, tle_line2)
    return False


def isValid(user_input_data):
    user_input_data = shlex.split(re.sub(r"\"|'|\\|/", "", shlex.quote(user_input_data)))
    user_input_data = ' '.join(user_input_data[:-4]), *user_input_data[-4:]
    if len(user_input_data) != 5:
        return False
    values = {
        0: lambda x: TLE(x),                 # obiekt TLE
        1: lambda x: True,                   # maidenhead ; QTH-lokator
        2: lambda x: 0 <= int(x) <= 8849,    # wysokość (nmp) posadowienia instalacji antenowej
        3: lambda x: 10 <= int(x) <= 90,     # minimalny kąt elewacji
        4: lambda x: 1 <= int(x) <= 5        # oczekiwana liczba wyników do prezentacji
    }
    rules = {
        0: lambda x: bool(re.match(r"^[a-zA-Z0-9\[\]+\- ()]{1,24}$", x)),
        1: lambda x: bool(re.match(r"^[A-R]{2}[0-9]{2}([a-x]{2}([0-9]{2})?)?$", x)),
        2: lambda x: bool(re.match(r"^\d{1,4}$", x)),
        3: lambda x: bool(re.match(r"^\d{1,2}$", x)),
        4: lambda x: bool(re.match(r"^[1-5]$", x)),
    }
    for i in range(5):
        if not (rules[i](user_input_data[i]) and values[i](user_input_data[i])):
            return False
    return user_input_data


def currentPosition(satellite):
    satellite.compute(datetime.datetime.utcnow())
    msg = ("aktualne położenie %s  lat: %f,  lon: %f,  wysokość: %.2f km\r\n" %
        (satellite.name, degrees(satellite.sublat), degrees(satellite.sublong), satellite.elevation / 1000))
    return msg


def calculate(satellite, QTH_locator, geocentric_height_above_sea_level, min_elev_angle_zenith, how_many_results):
    hard_limit = 300
    observer = ephem.Observer()
    lat, lon = maidenhead.to_location(QTH_locator)
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = geocentric_height_above_sea_level
    observer.date = datetime.datetime.utcnow()
    msg = (("efemerydy %s dla QTH lokatora %s przy zadanym minimalnym kącie elewacji w zenicie wynoszącym %d°. \r\n" +
            "Format danych:  wschód { zenit } zachód     Legenda:  az. - azymut, el. - kąt elewacji, odl. - minimalna odległość\r\n") %
            (satellite.name, QTH_locator, min_elev_angle_zenith))
    for k in range(how_many_results):
        searching = True
        i = 0
        while searching:
            i += 1
            info = observer.next_pass(satellite)
            if round(degrees(info[3])) >= min_elev_angle_zenith:
                searching = False
            else:
                observer.date = info[2]
                if i > hard_limit:
                    if msg:
                        msg += ("... to wszystko co znalazłem w ograniczonym czasie. Sprawdziłem %d najbliższych przelotów\r\n" %
                                 hard_limit)
                    else:
                        msg = ("Nie znaleziono przelotu %s z podanym minimalnym kątem elewacji wynoszącym %d°.\r\n" %
                                (satellite.name, min_elev_angle_zenith))
                    return msg
        rising_azimuth = round(degrees(info[1]))
        setting_azimuth = round(degrees(info[5]))
        zenith_azimuth = round((rising_azimuth - setting_azimuth) / 2 + setting_azimuth)
        elev_angle = round(degrees(info[3]))
        observer.date = info[2]
        satellite.compute(observer)
        min_dist_from_observer_to_satellite = round(satellite.range / 1000)
        msg += ("%20s, az.: %3s° {%20s, az.: %3s°, el.: %2s°, odl.:%5s km} %20s, az.: %3s°\r\n" %
            (info[0], rising_azimuth, info[2], zenith_azimuth, elev_angle, min_dist_from_observer_to_satellite, info[4], setting_azimuth))
    return msg


def main():
    logger.debug("START")
    joinchan(channel)
    while True:
        ircmsg = ""
        ircmsg = ircsock.recv(2048)
        ircmsg = ircmsg.decode("utf-8").strip('\n\r')
        if VERBOSE:
            print(datetime.datetime.utcnow().strftime("%y-%m-%d %H:%M:%S "), repr(ircmsg), "\n")
        if ircmsg.find("PING :") != -1:
            pong()
        if ircmsg.find("PRIVMSG") != -1:
            name = ircmsg.split('!', 1)[0][1:]
            schan = ircmsg.split('PRIVMSG', 1)[1].split(':', 1)[0].strip()
            message = ircmsg.split('PRIVMSG', 1)[1].split(':', 1)[1]
            if message.strip() == '!' + botnick:
                message = '!' + botnick + ' help'
            if message[:2 + len(botnick)] == '!' + botnick + ' ':
                logger.info("<<< " + repr(ircmsg))
                message = " ".join(message[2 + len(botnick):].split())
                if schan == botnick:
                    schan = name
                if message.strip() == 'help':
                    help(schan)
                elif message.strip() == 'die':
                    if name == "rumpelsztyk" or name == "arkoz":
                        sendmsg("ok...zdycham... x(", schan)
                        sendmsg("DIED!", name)
                        ircsock.send(bytes("PART " + channel + "\r\n", 'utf-8'))
                        logger.debug("DIE!")
                        sys.exit()
                    else:
                        message = "Nie masz uprawnień " + name + ". Muszę zgłosić ten incydent!"
                        sendmsg(message, schan)
                else:
                    dane = message.strip()
                    dane = isValid(dane)
                    if dane:
                        try:
                            messages = calculate(TLE(dane[0]), dane[1], int(dane[2]), int(dane[3]), int(dane[4]))
                            messages = messages.split('\r\n')
                            for message in messages:
                                if message:
                                    sendmsg(message, schan)
                        except ValueError:
                            message = "Satelita zdaje się (zawsze) pozostawać poniżej Twojego horyzontu."
                            sendmsg(message, schan)
                        except:
                            message = "Upsss… Coś poszło nie tak!"
                            sendmsg(message, schan)
                    else:
                        message = "Nie rozpoznałem polecenia. Spróbuj !" + \
                            botnick + " help, aby otrzymać pomoc."
                        sendmsg(message, schan)


#                       print(currentPosition(TLE(dane[0])))   ## TODO


server = "chat.freenode.net"
channel = "#gynvaelstream"
botnick = "satfinder"
password = "chcielibyśta"


logger = logprepare()
ircsock = connect(server, channel, botnick, password)
main()
