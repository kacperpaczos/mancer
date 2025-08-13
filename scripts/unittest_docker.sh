#!/bin/bash
# 🐳 MANCER UNIT TESTS - Testy jednostkowe w Docker (bez pytest-docker)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Kolory
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; C='\033[0;36m'; NC='\033[0m'

log() { echo -e "${B}[DOCKER]${NC} $1"; }
ok() { echo -e "${G}[OK]${NC} $1"; }
fail() { echo -e "${R}[FAIL]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
info() { echo -e "${C}[INFO]${NC} $1"; }

# =============================================================================
# DOCKER ENVIRONMENT SETUP
# =============================================================================

check_docker() {
    log "Sprawdzam dostępność Docker..."

    # Sprawdź czy Docker jest zainstalowany
    if ! command -v docker &> /dev/null; then
        fail "Docker nie jest zainstalowany!"
        echo "Zainstaluj Docker: https://docs.docker.com/get-docker/"
        return 1
    fi

    # Sprawdź czy Docker działa (może wymagać sudo)
    if ! docker info &> /dev/null; then
        warn "Docker wymaga uprawnień sudo"
        if ! sudo docker info &> /dev/null; then
            fail "Nie można połączyć się z Docker daemon"
            echo "Sprawdź czy Docker jest uruchomiony: sudo systemctl start docker"
            return 1
        fi
        export DOCKER_SUDO="sudo"
    else
        export DOCKER_SUDO=""
    fi

    ok "Docker jest dostępny"
    return 0
}

create_test_dockerfile() {
    log "Tworzenie Dockerfile dla testów..."

    cat > Dockerfile.test << 'EOF'
FROM python:3.10-slim

# Zainstaluj wymagane pakiety systemowe
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj pliki projektu
COPY . .

# Zainstaluj zależności Python
RUN pip install --no-cache-dir -r requirements.txt

# Zainstaluj dodatkowe zależności testowe
RUN pip install --no-cache-dir pytest pytest-cov pytest-xdist

# Ustaw PYTHONPATH
ENV PYTHONPATH=/app

# Domyślna komenda
CMD ["python", "-m", "pytest", "tests/unit/", "-v", "--cov=src/mancer", "--cov-report=term-missing"]
EOF

    ok "Dockerfile.test utworzony"
}

build_test_image() {
    log "Budowanie obrazu Docker dla testów..."

    # Usuń stary obraz jeśli istnieje
    $DOCKER_SUDO docker rmi mancer-unittest:latest 2>/dev/null || true

    # Zbuduj nowy obraz
    $DOCKER_SUDO docker build -f Dockerfile.test -t mancer-unittest:latest . || {
        fail "Nie można zbudować obrazu Docker"
        return 1
    }

    ok "Obraz Docker zbudowany: mancer-unittest:latest"
    return 0
}

cleanup_docker_environment() {
    log "Czyszczenie środowiska Docker..."

    # Usuń kontener testowy jeśli istnieje
    $DOCKER_SUDO docker rm -f mancer-unittest-container 2>/dev/null || true

    # Usuń Dockerfile.test
    rm -f Dockerfile.test

    ok "Środowisko Docker wyczyszczone"
}

# =============================================================================
# PYTEST DOCKER SETUP
# =============================================================================

setup_pytest_docker() {
    log "Przygotowuję pytest dla Docker..."
    
    # Zainstaluj pytest-docker-compose jeśli nie ma
    if ! python3 -c "import pytest_docker_compose" &>/dev/null; then
        log "Instaluję pytest-docker-compose..."
        pip3 install pytest-docker-compose pytest-xdist || {
            fail "Nie można zainstalować pytest-docker-compose"
            return 1
        }
    fi
    
    ok "pytest-docker-compose gotowy"
    return 0
}

# =============================================================================
# TESTY JEDNOSTKOWE W DOCKER
# =============================================================================

run_unit_tests_docker() {
    echo -e "${B}"
    echo "================================================================="
    echo "🐳 TESTY JEDNOSTKOWE (DOCKER MODE)"
    echo "================================================================="
    echo -e "${NC}"
    
    check_docker || return 1
    setup_docker_environment || return 1
    setup_pytest_docker || return 1
    
    log "Uruchamiam testy jednostkowe w Docker..."
    echo
    
    # Uruchom testy przez Docker
    if python3 -m pytest tests/unit/ \
        --docker-compose=tests/docker/docker-compose.yml \
        --docker-compose-no-build \
        -v --tb=short; then
        echo
        ok "🎉 Testy jednostkowe (Docker) przeszły pomyślnie!"
        return 0
    else
        echo
        fail "❌ Testy jednostkowe (Docker) nie przeszły"
        return 1
    fi
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup() {
    cleanup_docker_environment
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    if [[ $# -gt 0 ]]; then
        case "$1" in
            "help"|"h"|"-h"|"--help")
                echo -e "${B}"
                echo "================================================================="
                echo "🐳 MANCER UNIT TESTS - Testy jednostkowe w Docker"
                echo "================================================================="
                echo -e "${NC}"
                echo "Uruchamia testy jednostkowe w izolowanych kontenerach Docker."
                echo
                echo "Użycie: $0"
                echo
                echo "Funkcjonalność:"
                echo "- Sprawdza dostępność Docker (może wymagać sudo)"
                echo "- Czyści środowisko Docker"
                echo "- Uruchamia kontenery z tests/docker/docker-compose.yml"
                echo "- Instaluje pytest-docker-compose"
                echo "- Uruchamia pytest tests/unit/ w kontenerach"
                echo "- Automatycznie czyści środowisko po testach"
                echo
                echo "Wymagania:"
                echo "- Docker i Docker Compose"
                echo "- Python 3 z pip"
                echo "- Uprawnienia do Docker (może wymagać sudo)"
                echo
                echo "Pliki Docker:"
                echo "- tests/docker/docker-compose.yml  # Konfiguracja kontenerów"
                echo "- tests/docker/env.develop.test    # Template środowiska"
                echo "- tests/docker/cleanup.sh          # Skrypt czyszczenia"
                echo
                exit 0
                ;;
            *)
                echo -e "${R}❌ Nieznana opcja: $1${NC}"
                echo "Użyj '$0 help' aby zobaczyć pomoc."
                exit 1
                ;;
        esac
    fi
    
    # Uruchom testy jednostkowe w Docker
    run_unit_tests_docker
}

# Trap cleanup
trap cleanup EXIT

# Execute main function
main "$@" 