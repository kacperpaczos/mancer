#!/bin/bash

# Kolory do formatowania
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Czyszczenie środowiska...${NC}"

# Usuń środowisko wirtualne
if [ -d "venv" ]; then
    echo -e "${GREEN}Usuwanie środowiska wirtualnego...${NC}"
    rm -rf venv
fi

# Usuń pliki cache Pythona
echo -e "${GREEN}Usuwanie plików cache...${NC}"
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Usuń katalogi z danymi
echo -e "${GREEN}Usuwanie wszystkich danych...${NC}"
rm -rf serwery/
rm -rf _cache_/
rm -rf profiles/*.json

echo -e "${GREEN}Czyszczenie zakończone${NC}" 