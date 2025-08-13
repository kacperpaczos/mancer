#!/bin/bash
# 🧪 MANCER TESTS - Uruchamianie testów lokalnie lub w Docker
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Kolory
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; C='\033[0;36m'; NC='\033[0m'

log() { echo -e "${B}[INFO]${NC} $1"; }
ok() { echo -e "${G}[OK]${NC} $1"; }
fail() { echo -e "${R}[FAIL]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }

# =============================================================================
# FUNKCJE POMOCNICZE
# =============================================================================

show_help() {
    echo -e "${B}"
    echo "================================================================="
    echo "🧪 MANCER TESTS - Uruchamianie testów"
    echo "================================================================="
    echo -e "${NC}"
    echo "Uruchamia testy jednostkowe lokalnie lub w kontenerze Docker."
    echo
    echo "Użycie:"
    echo "  $0 local          # Uruchom testy lokalnie"
    echo "  $0 docker         # Uruchom testy w Docker"
    echo "  $0 help           # Pokaż tę pomoc"
    echo
    echo "Przykłady:"
    echo "  $0 local          # Szybkie testy lokalne"
    echo "  $0 docker         # Testy w izolowanym środowisku"
    echo
}

check_requirements_local() {
    log "Sprawdzam wymagania lokalne..."
    
    # Sprawdź Python
    if ! command -v python3 &> /dev/null; then
        fail "Python 3 nie jest zainstalowany!"
        return 1
    fi
    
    # Sprawdź czy jesteśmy w venv
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        warn "Nie jesteś w środowisku wirtualnym"
        if [[ -d ".venv" ]]; then
            log "Aktywuję .venv..."
            source .venv/bin/activate
        else
            warn "Brak .venv - testy mogą nie działać poprawnie"
        fi
    fi
    
    # Sprawdź pytest
    if ! python3 -c "import pytest" &>/dev/null; then
        log "Instaluję pytest..."
        pip install pytest pytest-cov
    fi
    
    ok "Wymagania lokalne spełnione"
}

check_requirements_docker() {
    log "Sprawdzam wymagania Docker..."

    # Sprawdź Docker
    if ! command -v docker &> /dev/null; then
        fail "Docker nie jest zainstalowany!"
        echo "Zainstaluj Docker: https://docs.docker.com/get-docker/"
        return 1
    fi

    # Sprawdź czy Docker działa (bez sudo)
    if ! docker info &> /dev/null 2>&1; then
        fail "Docker nie działa!"
        echo "Uruchom Docker Desktop lub systemowy Docker daemon"
        echo "Dla Docker Desktop: uruchom aplikację Docker Desktop"
        echo "Dla systemowego Docker: sudo systemctl start docker"
        return 1
    fi

    export DOCKER_CMD="docker"
    ok "Docker jest dostępny"
}

# =============================================================================
# TESTY LOKALNE
# =============================================================================

run_tests_local() {
    echo -e "${G}"
    echo "================================================================="
    echo "🏠 TESTY LOKALNE"
    echo "================================================================="
    echo -e "${NC}"
    
    check_requirements_local || return 1
    
    log "Uruchamiam testy jednostkowe lokalnie..."
    echo
    
    # Uruchom testy
    if python3 -m pytest tests/unit/ -v --cov=src/mancer --cov-report=term-missing --cov-report=html; then
        echo
        ok "🎉 Testy lokalne przeszły pomyślnie!"
        info "Raport HTML: htmlcov/index.html"
        return 0
    else
        echo
        fail "❌ Testy lokalne nie przeszły"
        return 1
    fi
}

# =============================================================================
# TESTY DOCKER
# =============================================================================

create_dockerfile() {
    log "Tworzę Dockerfile dla testów..."
    
    cat > Dockerfile.test << 'EOF'
FROM python:3.10-slim

# Zainstaluj podstawowe narzędzia
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj requirements i zainstaluj zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pytest pytest-cov

# Skopiuj kod źródłowy
COPY . .

# Ustaw PYTHONPATH tak, aby moduł 'mancer' był importowalny
ENV PYTHONPATH=/app/src

# Uruchom testy
CMD ["python", "-m", "pytest", "tests/unit/", "-v", "--cov=src/mancer", "--cov-report=term-missing"]
EOF
    
    ok "Dockerfile.test utworzony"
}

run_tests_docker() {
    echo -e "${B}"
    echo "================================================================="
    echo "🐳 TESTY DOCKER"
    echo "================================================================="
    echo -e "${NC}"
    
    check_requirements_docker || return 1
    create_dockerfile || return 1
    
    log "Buduję obraz Docker..."
    if ! $DOCKER_CMD build -f Dockerfile.test -t mancer-tests:latest .; then
        fail "Nie można zbudować obrazu Docker"
        return 1
    fi
    
    log "Uruchamiam testy w kontenerze Docker..."
    echo
    
    # Uruchom testy w kontenerze
    if $DOCKER_CMD run --rm mancer-tests:latest; then
        echo
        ok "🎉 Testy Docker przeszły pomyślnie!"
        return 0
    else
        echo
        fail "❌ Testy Docker nie przeszły"
        return 1
    fi
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup() {
    # Usuń Dockerfile.test jeśli istnieje
    rm -f Dockerfile.test
    
    # Usuń obraz Docker jeśli istnieje
    if [[ -n "${DOCKER_CMD:-}" ]]; then
        $DOCKER_CMD rmi mancer-tests:latest 2>/dev/null || true
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    case "${1:-help}" in
        "local"|"l")
            run_tests_local
            ;;
        "docker"|"d")
            run_tests_docker
            ;;
        "help"|"h"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            fail "Nieznana opcja: $1"
            echo "Użyj '$0 help' aby zobaczyć dostępne opcje."
            exit 1
            ;;
    esac
}

# Trap cleanup
trap cleanup EXIT

# Execute main function
main "$@"
