#!/bin/bash

# Kolory do formatowania
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Uruchamianie aplikacji...${NC}"

# Sprawdź czy Python jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 nie jest zainstalowany!${NC}"
    exit 1
fi

# Sprawdź czy python3-venv jest zainstalowany
if ! dpkg -l | grep -q python3-venv; then
    echo -e "${GREEN}Instalowanie python3-venv...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip
fi

# Stwórz i aktywuj środowisko wirtualne jeśli nie istnieje
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Tworzenie środowiska wirtualnego...${NC}"
    python3 -m venv venv
fi

# Aktywuj środowisko wirtualne
source venv/bin/activate

# Aktualizuj pip w środowisku wirtualnym
python3 -m pip install --upgrade pip

# Zainstaluj wymagane pakiety
echo -e "${GREEN}Instalowanie wymaganych pakietów...${NC}"
pip install -r requirements.txt

# Utwórz wymagane katalogi i pliki
echo -e "${GREEN}Tworzenie struktury katalogów...${NC}"
mkdir -p serwery _cache_/serwery profiles

# Wyczyść ekran przed uruchomieniem aplikacji
clear

# Uruchom aplikację
echo -e "${GREEN}Uruchamianie aplikacji...${NC}"
python3 main.py 