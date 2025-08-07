#!/bin/bash
# 🧪 MANCER UNIT TESTS - Lokalne testy jednostkowe (venv)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Kolory
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; C='\033[0;36m'; NC='\033[0m'

log() { echo -e "${B}[TEST]${NC} $1"; }
ok() { echo -e "${G}[OK]${NC} $1"; }
fail() { echo -e "${R}[FAIL]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
info() { echo -e "${C}[INFO]${NC} $1"; }

# =============================================================================
# VENV SETUP
# =============================================================================

setup_venv() {
    log "Przygotowuję środowisko wirtualne..."

    # Zawsze usuń stary venv i utwórz nowy
    if [[ -d ".venv" ]]; then
        log "Usuwam stare środowisko wirtualne..."
        rm -rf .venv
    fi

    log "Tworzę nowe środowisko wirtualne..."
    python3 -m venv .venv || {
        fail "Nie można utworzyć środowiska wirtualnego"
        return 1
    }
    
    # Aktywuj venv
    source .venv/bin/activate || {
        fail "Nie można aktywować środowiska wirtualnego"
        return 1
    }
    
    ok "Środowisko wirtualne aktywne: $VIRTUAL_ENV"
    
    # Upgrade pip (cicho)
    python -m pip install --upgrade pip >/dev/null 2>&1 || true

    # Zainstaluj wszystkie wymagane zależności
    log "Instaluję zależności z requirements.txt..."
    pip install -r requirements.txt || {
        fail "Nie można zainstalować zależności"
        return 1
    }
    
    # Zawsze zainstaluj wersję developerską mancera
    log "Instaluję wersję developerską mancera..."

    # Najpierw odinstaluj jeśli istnieje
    pip uninstall mancer -y >/dev/null 2>&1 || true

    # Zainstaluj w trybie edytowalnym
    if pip install -e .; then
        log "Mancer zainstalowany w trybie edytowalnym"
    else
        warn "Nie można zainstalować editable mancera, używam PYTHONPATH"
        export PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"
    fi
    
    # Sprawdź czy mancer jest dostępny
    if python -c "import mancer; print(f'Mancer {mancer.__version__} ready')" 2>/dev/null | grep -q "ready"; then
        ok "Framework mancer dostępny w venv"
    else
        if PYTHONPATH="$PROJECT_ROOT/src" python -c "from mancer.application.shell_runner import ShellRunner" 2>/dev/null; then
            export PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"
            ok "Framework mancer dostępny przez PYTHONPATH"
        else
            fail "Framework mancer nie jest dostępny"
            return 1
        fi
    fi
    
    return 0
}

# =============================================================================
# TESTY JEDNOSTKOWE
# =============================================================================

run_unit_tests() {
    echo -e "${B}"
    echo "================================================================="
    echo "🧪 TESTY JEDNOSTKOWE (LOCAL MODE)"
    echo "================================================================="
    echo -e "${NC}"
    
    setup_venv || return 1
    
    log "Uruchamiam testy jednostkowe lokalnie..."
    echo
    
    # Uruchom testy z PYTHONPATH
    if PYTHONPATH="$PROJECT_ROOT/src" python -m pytest tests/unit/ -v --tb=short; then
        echo
        ok "🎉 Testy jednostkowe przeszły pomyślnie!"
        return 0
    else
        echo
        fail "❌ Testy jednostkowe nie przeszły"
        return 1
    fi
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup() {
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        info "Pozostaję w środowisku wirtualnym dla dalszej pracy..."
        echo "Aby wyjść z venv, użyj: deactivate"
    fi
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
                echo "🧪 MANCER UNIT TESTS - Lokalne testy jednostkowe"
                echo "================================================================="
                echo -e "${NC}"
                echo "Uruchamia testy jednostkowe w środowisku wirtualnym Python."
                echo
                echo "Użycie: $0"
                echo
                echo "Funkcjonalność:"
                echo "- Tworzy/aktywuje .venv"
                echo "- Instaluje pytest"
                echo "- Instaluje framework (pip install -e .)"
                echo "- Fallback na PYTHONPATH=src/"
                echo "- Uruchamia pytest tests/unit/"
                echo
                echo "Zmienne środowiskowe:"
                echo "  FORCE_REINSTALL=true # Wymusi reinstalację mancera"
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
    
    # Uruchom testy jednostkowe
    run_unit_tests
}

# Trap cleanup
trap cleanup EXIT

# Execute main function
main "$@" 