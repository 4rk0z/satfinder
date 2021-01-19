#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © arkoz 2021

import os
import sys
import requests
import logging
from logging import handlers


botnick = "satfinder"


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



def downloadTLE():
      url = "http://www.celestrak.com/NORAD/elements/stations.txt"
      r = requests.get(url)
      if r.status_code == 200:
          tle = r.text
          with open("tle.txt", 'w') as tle_file:
              tle_file.write(tle)
          tle_file.close()
          url = "http://www.celestrak.com/NORAD/elements/noaa.txt"
          r = requests.get(url)
          if r.status_code == 200:
              tle = r.text
              with open("tle.txt", 'a') as tle_file:
                  tle_file.write(tle)
              tle_file.close()

logger = logprepare()
downloadTLE()
sys.exit(0)
