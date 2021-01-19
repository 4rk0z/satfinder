utwórz środowisko virtualne python3 (venv) i aktwuj je.
skopiuj pliki *.py projektu
zainstaluj brakujące moduły python przy użyciu pip3
dodaj TLEdownloader.py do crontab (przykładowe użycie w pliku crontab), pamiętaj o zmodyfikowaniu ścieżek by wskazywały na Twoje virtualne środowisko
uruchom TLEdownloder.py po raz pierwszy i upewnij się, że plik(i) TLE zostały pobrane (cron_errorlog.txt oraz np. logi/satfinder.log)
przykładowe wpisy w logach świadczą o poprawnym pobraniu plików TLE:
21-01-19 16:32:43 urllib3.connectionpool    DEBUG    Starting new HTTP connection (1): www.celestrak.com:80
21-01-19 16:32:43 urllib3.connectionpool    DEBUG    http://www.celestrak.com:80 "GET /NORAD/elements/stations.txt HTTP/1.1" 200 4389
21-01-19 16:32:43 urllib3.connectionpool    DEBUG    Starting new HTTP connection (1): www.celestrak.com:80
21-01-19 16:32:44 urllib3.connectionpool    DEBUG    http://www.celestrak.com:80 "GET /NORAD/elements/noaa.txt HTTP/1.1" 200 1466
skonfiguruj parametry (serwer,kanał, nazwa bota itd..) w pliku satfinder.py i uruchom go
