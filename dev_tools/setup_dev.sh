#!/bin/bash

# Skrypt przygotowujący środowisko developerskie dla frameworka Mancer
set -e

echo "==========================================="
echo "Przygotowywanie środowiska developerskiego"
echo "==========================================="

# Definiowanie ścieżek
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"
CONFIG_DIR="$PROJECT_ROOT/src/mancer/config"

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

# Sprawdzenie wymaganych narzędzi
check_requirements() {
    log "Sprawdzanie wymaganych narzędzi..."
    
    if ! command -v python3 &> /dev/null; then
        error "Python 3 nie jest zainstalowany. Proszę zainstalować Python 3.8 lub nowszy."
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log "Znaleziono Python w wersji $PYTHON_VERSION"
    
    if [[ $(echo "$PYTHON_VERSION < 3.8" | bc) -eq 1 ]]; then
        error "Wymagana jest wersja Python 3.8 lub nowsza. Proszę zaktualizować Python."
    fi
    
    # Sprawdź, czy pip jest zainstalowany
    if ! command -v pip3 &> /dev/null; then
        warn "pip3 nie jest zainstalowany. Próbuję zainstalować..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y python3-pip
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-pip
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3-pip
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm python-pip
        else
            error "Nie można automatycznie zainstalować pip3. Proszę zainstalować ręcznie."
        fi
    fi
}

# Tworzenie wirtualnego środowiska
create_venv() {
    log "Tworzenie wirtualnego środowiska..."
    
    if [ -d "$VENV_DIR" ]; then
        warn "Wirtualne środowisko już istnieje w: $VENV_DIR"
        read -p "Czy chcesz je usunąć i utworzyć nowe? (t/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Tt]$ ]]; then
            log "Usuwanie istniejącego wirtualnego środowiska..."
            rm -rf "$VENV_DIR"
        else
            log "Używanie istniejącego wirtualnego środowiska."
            return
        fi
    fi
    
    python3 -m venv "$VENV_DIR"
    log "Utworzono wirtualne środowisko w: $VENV_DIR"
}

# Instalacja zależności
install_dependencies() {
    log "Instalacja zależności..."
    
    # Aktywacja wirtualnego środowiska
    source "$VENV_DIR/bin/activate"
    
    # Aktualizacja pip
    log "Aktualizacja pip..."
    pip install --upgrade pip
    
    # Instalacja zależności developerskich
    log "Instalacja zależności developerskich..."
    pip install pytest pytest-cov pylint mypy black isort pyyaml
    
    # Instalacja zależności projektu
    log "Instalacja zależności projektu..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
    
    # Instalacja projektu w trybie edycji
    log "Instalacja projektu w trybie edycji..."
    pip install -e "$PROJECT_ROOT"
}

# Tworzenie struktury katalogów konfiguracyjnych
setup_config_dirs() {
    log "Tworzenie struktury katalogów konfiguracyjnych..."
    
    # Tworzenie katalogu konfiguracyjnego w ~/.mancer
    USER_CONFIG_DIR="$HOME/.mancer"
    mkdir -p "$USER_CONFIG_DIR"
    
    # Tworzenie katalogów konfiguracyjnych w projekcie
    mkdir -p "$CONFIG_DIR"
    
    # Kopiowanie plików konfiguracyjnych, jeśli nie istnieją
    if [ ! -f "$USER_CONFIG_DIR/tool_versions.yaml" ] && [ -f "$CONFIG_DIR/tool_versions.yaml" ]; then
        cp "$CONFIG_DIR/tool_versions.yaml" "$USER_CONFIG_DIR/"
        log "Skopiowano plik konfiguracyjny tool_versions.yaml do $USER_CONFIG_DIR/"
    fi
    
    if [ ! -f "$USER_CONFIG_DIR/settings.yaml" ] && [ -f "$CONFIG_DIR/settings.yaml" ]; then
        cp "$CONFIG_DIR/settings.yaml" "$USER_CONFIG_DIR/"
        log "Skopiowano plik konfiguracyjny settings.yaml do $USER_CONFIG_DIR/"
    fi
}

# Wykonywanie git hook'ów (opcjonalnie)
setup_git_hooks() {
    if [ -d "$PROJECT_ROOT/.git" ]; then
        log "Konfigurowanie git hook'ów..."
        
        # Tworzenie katalogu dla hook'ów
        mkdir -p "$PROJECT_ROOT/.git/hooks"
        
        # Tworzenie pre-commit hook'a
        cat > "$PROJECT_ROOT/.git/hooks/pre-commit" << EOF
#!/bin/bash
# Pre-commit hook dla frameworka Mancer

# Uruchomienie formatowania kodu
source "$VENV_DIR/bin/activate"
black "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests"
isort "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests"

# Uruchomienie testów
python -m pytest "$PROJECT_ROOT/tests" -v
EOF
        
        # Nadanie uprawnień wykonawczych
        chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit"
        log "Skonfigurowano git hook pre-commit"
    else
        warn "Nie znaleziono repozytorium Git. Pomijam konfigurację git hook'ów."
    fi
}

# Główna funkcja
main() {
    cd "$PROJECT_ROOT"
    
    check_requirements
    create_venv
    install_dependencies
    setup_config_dirs
    setup_git_hooks
    
    log "Środowisko developerskie zostało przygotowane pomyślnie!"
    log "Aby aktywować wirtualne środowisko, użyj polecenia:"
    echo -e "${GREEN}    source $VENV_DIR/bin/activate${NC}"
    
    # Aktywacja wirtualnego środowiska w bieżącej sesji
    source "$VENV_DIR/bin/activate"
}

# Uruchomienie głównej funkcji
main 