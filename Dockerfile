# Vyberieme oficiálny obraz Pythonu ako základ
FROM python:3.9-slim

# Nastavíme pracovný adresár v kontajneri
WORKDIR /usr/src/app

# Kopírujeme len potrebné súbory do kontajnera
# Ak máme súbory potrebné na spustenie kódu, napríklad testovacie skripty, pridáme ich sem
# COPY . .

# Predvolený príkaz pri štarte kontajnera môže byť ponechaný prázdný alebo môže byť nastavený na spustenie interaktívnej shell
CMD [ "bash" ]


# Inštalácia pytest
RUN pip install pytest

# Kopírujeme testovacie skripty do kontajnera
COPY test_directory/ /tests/


    