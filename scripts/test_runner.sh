#!/bin/bash
# 🧪 MANCER TEST RUNNER - Prosty skrypt do uruchamiania testów
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Kolory
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; NC='\033[0m'

log() { echo -e "${B}[INFO]${NC} $1"; }
ok() { echo -e "${G}[OK]${NC} $1"; }
fail() { echo -e "${R}[FAIL]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }

show_help() {
    echo -e "${B}"
    echo "================================================================="
    echo "🧪 MANCER TEST RUNNER"
    echo "================================================================="
    echo -e "${NC}"
    echo "Prosty skrypt do uruchamiania testów jednostkowych."
    echo
    echo "Użycie:"
    echo "  $0                    # Uruchom testy lokalnie"
    echo "  $0 local              # Uruchom testy lokalnie"
    echo "  $0 docker             # Uruchom testy w Docker (jeśli dostępny)"
    echo "  $0 help               # Pokaż tę pomoc"
    echo
}

check_python() {
    log "Sprawdzam środowisko Python..."
    
    if ! command -v python3 &> /dev/null; then
        fail "Python 3 nie jest zainstalowany!"
        return 1
    fi
    
    # Aktywuj venv jeśli istnieje
    if [[ -d ".venv" && -z "${VIRTUAL_ENV:-}" ]]; then
        log "Aktywuję środowisko wirtualne .venv..."
        source .venv/bin/activate
    fi
    
    # Sprawdź pytest
    if ! python3 -c "import pytest" &>/dev/null; then
        log "Instaluję pytest..."
        pip install pytest pytest-cov
    fi
    
    ok "Środowisko Python gotowe"
}

run_tests_local() {
    echo -e "${G}"
    echo "================================================================="
    echo "🏠 TESTY JEDNOSTKOWE - LOKALNIE"
    echo "================================================================="
    echo -e "${NC}"
    
    check_python || return 1
    
    log "Uruchamiam testy jednostkowe..."
    echo
    
    # Uruchom testy z pokryciem
    if python3 -m pytest tests/unit/ \
        -v \
        --cov=src/mancer \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --tb=short; then
        echo
        ok "🎉 Wszystkie testy przeszły pomyślnie!"
        log "Raport HTML: htmlcov/index.html"
        return 0
    else
        echo
        fail "❌ Niektóre testy nie przeszły"
        return 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        return 1
    fi
    
    if ! docker info &> /dev/null 2>&1; then
        return 1
    fi
    
    return 0
}

run_tests_docker() {
    echo -e "${B}"
    echo "================================================================="
    echo "🐳 TESTY JEDNOSTKOWE - DOCKER"
    echo "================================================================="
    echo -e "${NC}"
    
    if ! check_docker; then
        warn "Docker nie jest dostępny - uruchamiam testy lokalnie"
        run_tests_local
        return $?
    fi
    
    log "Docker jest dostępny - tworzę kontener testowy..."
    
    # Utwórz prosty Dockerfile
    cat > Dockerfile.test << 'EOF'
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && pip install pytest pytest-cov

COPY . .
ENV PYTHONPATH=/app

CMD ["python", "-m", "pytest", "tests/unit/", "-v", "--cov=src/mancer", "--cov-report=term-missing"]
EOF
    
    log "Buduję obraz testowy..."
    if ! docker build -f Dockerfile.test -t mancer-test . --quiet; then
        fail "Nie można zbudować obrazu Docker"
        rm -f Dockerfile.test
        return 1
    fi
    
    log "Uruchamiam testy w kontenerze..."
    echo
    
    if docker run --rm mancer-test; then
        echo
        ok "🎉 Testy Docker przeszły pomyślnie!"
        docker rmi mancer-test &>/dev/null || true
        rm -f Dockerfile.test
        return 0
    else
        echo
        fail "❌ Testy Docker nie przeszły"
        docker rmi mancer-test &>/dev/null || true
        rm -f Dockerfile.test
        return 1
    fi
}

main() {
    case "${1:-local}" in
        "local"|"l"|"")
            run_tests_local
            ;;
        "docker"|"d")
            run_tests_docker
            ;;
        "help"|"h"|"-h"|"--help")
            show_help
            ;;
        *)
            fail "Nieznana opcja: $1"
            show_help
            exit 1
            ;;
    esac
}

# Cleanup na wyjściu
trap 'rm -f Dockerfile.test' EXIT

main "$@"
