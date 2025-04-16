#!/bin/bash

# Skrypt uruchamiający testy dla frameworka Mancer
set -e

# Definiowanie ścieżek
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"
TESTS_DIR="$PROJECT_ROOT/tests"

# Kolory dla komunikatów
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funkcja do wyświetlania komunikatów
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Sprawdzenie, czy w środowisku wirtualnym
check_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        warn "Nie wykryto aktywnego środowiska wirtualnego."
        if [ -d "$VENV_DIR" ]; then
            log "Aktywuję środowisko wirtualne: $VENV_DIR"
            source "$VENV_DIR/bin/activate"
        else
            error "Środowisko wirtualne nie istnieje. Uruchom najpierw tools/setup_dev.sh"
        fi
    fi
}

# Uruchomienie testów jednostkowych
run_unit_tests() {
    log "Uruchamianie testów jednostkowych..."
    python -m pytest "$TESTS_DIR/unit" -v
}

# Uruchomienie testów integracyjnych
run_integration_tests() {
    log "Uruchamianie testów integracyjnych..."
    python -m pytest "$TESTS_DIR/integration" -v -m "not privileged"
}

# Uruchomienie testów wymagających uprawnień roota
run_privileged_tests() {
    if [ "$(id -u)" -eq 0 ]; then
        log "Uruchamianie testów wymagających uprawnień roota..."
        python -m pytest "$TESTS_DIR" -v -m "privileged"
    else
        warn "Testy wymagające uprawnień roota zostały pominięte. Uruchom skrypt z sudo, aby je wykonać."
    fi
}

# Uruchomienie wszystkich testów z pomiarem pokrycia
run_tests_with_coverage() {
    log "Uruchamianie wszystkich testów z pomiarem pokrycia kodu..."
    python -m pytest "$TESTS_DIR" -v --cov=src/mancer --cov-report=term --cov-report=html
    log "Raport pokrycia kodu został zapisany w katalogu: $PROJECT_ROOT/htmlcov"
    log "Otwórz $PROJECT_ROOT/htmlcov/index.html w przeglądarce, aby zobaczyć szczegóły."
}

# Funkcja wyświetlająca pomoc
show_help() {
    echo "Użycie: $0 [opcja]"
    echo "Opcje:"
    echo "  -a, --all              Uruchom wszystkie testy (domyślne)"
    echo "  -u, --unit             Uruchom tylko testy jednostkowe"
    echo "  -i, --integration      Uruchom tylko testy integracyjne"
    echo "  -p, --privileged       Uruchom tylko testy wymagające uprawnień roota"
    echo "  -c, --coverage         Uruchom testy z pomiarem pokrycia kodu"
    echo "  -h, --help             Wyświetl tę pomoc"
}

# Główna funkcja
main() {
    cd "$PROJECT_ROOT"
    check_venv
    
    # Sprawdzenie argumentów
    case "$1" in
        -a|--all)
            run_unit_tests
            run_integration_tests
            run_privileged_tests
            ;;
        -u|--unit)
            run_unit_tests
            ;;
        -i|--integration)
            run_integration_tests
            ;;
        -p|--privileged)
            run_privileged_tests
            ;;
        -c|--coverage)
            run_tests_with_coverage
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            # Domyślnie uruchom wszystkie testy
            run_unit_tests
            run_integration_tests
            run_privileged_tests
            ;;
    esac
    
    log "Testy zakończone!"
}

# Uruchomienie głównej funkcji
main "$@" 