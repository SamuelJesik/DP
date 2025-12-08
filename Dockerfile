# Vyberieme oficiálny obraz Pythonu ako základ
FROM python:3.9-slim

# --- NOVÉ: Inštalácia kompilátorov pre C++ a Javu ---
# apt-get update: stiahne zoznam balíčkov
# install -y g++: nainštaluje C++ kompilátor
# install -y default-jdk: nainštaluje Java kompilátor a runtime
# rm -rf ...: vyčistí cache, aby bol image menší
RUN apt-get update && apt-get install -y \
    g++ \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Nastavíme pracovný adresár v kontajneri
WORKDIR /usr/src/app

# Inštalácia pytest (pre Python testy)
RUN pip install pytest

# Kopírujeme testovacie skripty do kontajnera
COPY test_directory/ /tests/

# Predvolený príkaz pri štarte kontajnera
CMD [ "bash" ]