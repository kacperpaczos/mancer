#!/bin/bash
# Skrypt do uruchamiania testów automatycznych Mancer w Docker

# Kolory
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🐳 Uruchamianie testów automatycznych Mancer Docker${NC}"
echo "================================================="

# Sprawdź wymagania
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker nie jest zainstalowany!${NC}"
    exit 1
fi

if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest nie jest zainstalowany. Instalowanie...${NC}"
    pip install pytest pytest-docker-compose pytest-xdist paramiko
fi

# Przejdź do katalogu głównego projektu
cd "$(dirname "$0")/../.."

# Upewnij się, że środowisko Docker jest czyste
echo -e "${YELLOW}🧹 Czyszczenie środowiska Docker...${NC}"
cd development/docker_test
sudo ./cleanup.sh 2>/dev/null || true

# Skopiuj plik środowiskowy
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Tworzenie pliku .env...${NC}"
    cp env.develop.test .env
fi

# Uruchom testy
echo -e "${GREEN}🧪 Uruchamianie testów integracyjnych...${NC}"
cd ../..

# Uruchom pytest z odpowiednimi parametrami
pytest tests/integration/ \
    --docker-compose=development/docker_test/docker-compose.yml \
    --docker-compose-no-build \
    -v \
    --tb=short \
    --junit-xml=test_results.xml \
    --cov=src/mancer \
    --cov-report=html:htmlcov \
    --cov-report=term-missing

TEST_EXIT_CODE=$?

# Sprawdź wyniki
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Wszystkie testy przeszły pomyślnie!${NC}"
    echo -e "${GREEN}📊 Raport coverage dostępny w: htmlcov/index.html${NC}"
else
    echo -e "${RED}❌ Niektóre testy nie przeszły. Kod wyjścia: $TEST_EXIT_CODE${NC}"
fi

# Opcjonalne czyszczenie po testach
read -p "Czy chcesz wyczyścić środowisko Docker po testach? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 Czyszczenie po testach...${NC}"
    cd development/docker_test
    sudo ./cleanup.sh
fi

echo -e "${GREEN}🏁 Testy zakończone${NC}"
exit $TEST_EXIT_CODE 