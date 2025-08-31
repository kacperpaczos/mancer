#!/bin/bash

# Mancer Terminal - Skrypt uruchamiający
# Uruchamia Mancer Terminal w środowisku wirtualnym z deweloperskim Mancerem

set -e  # Zatrzymaj na błędzie

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcje pomocnicze
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Sprawdź czy jesteśmy w odpowiednim katalogu
check_directory() {
    if [[ ! -f "prototypes/mancer-terminal/main.py" ]]; then
        print_error "Skrypt musi być uruchomiony z katalogu głównego projektu Mancer"
        print_info "Przejdź do katalogu głównego i uruchom ponownie"
        exit 1
    fi
}

# Sprawdź czy Python jest dostępny
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 nie jest zainstalowany lub nie jest dostępny w PATH"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    REQUIRED_VERSION="3.8"
    
    if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
        print_error "Wymagany Python 3.8+, dostępny: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Znaleziono Python $PYTHON_VERSION"
}

# Sprawdź czy venv istnieje
check_venv() {
    if [[ ! -d "venv" ]]; then
        print_warning "Środowisko wirtualne nie istnieje. Tworzę nowe..."
        create_venv
    else
        print_success "Znaleziono istniejące środowisko wirtualne"
    fi
}

# Utwórz nowe środowisko wirtualne
create_venv() {
    print_info "Tworzę nowe środowisko wirtualne..."
    python3 -m venv venv
    print_success "Środowisko wirtualne utworzone"
}

# Aktywuj środowisko wirtualne
activate_venv() {
    print_info "Aktywuję środowisko wirtualne..."
    source venv/bin/activate
    
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_error "Nie udało się aktywować środowiska wirtualnego"
        exit 1
    fi
    
    print_success "Środowisko wirtualne aktywowane: $VIRTUAL_ENV"
}

# Zainstaluj/aktualizuj pip
upgrade_pip() {
    print_info "Aktualizuję pip..."
    pip install --upgrade pip
    print_success "pip zaktualizowany"
}

# Zainstaluj Mancer w trybie deweloperskim
install_mancer_dev() {
    print_info "Instaluję Mancer w trybie deweloperskim..."
    
    if [[ -f "setup.py" ]] || [[ -f "pyproject.toml" ]]; then
        print_info "Instaluję z katalogu głównego..."
        pip install -e .
        print_success "Mancer zainstalowany w trybie deweloperskim"
    else
        print_warning "Pliki setup.py/pyproject.toml nie istnieją, pomijam instalację Mancer"
    fi
}

# Zainstaluj zależności Mancer Terminal
install_terminal_deps() {
    print_info "Instaluję zależności Mancer Terminal..."
    
    cd prototypes/mancer-terminal
    
    if [[ -f "requirements.txt" ]]; then
        print_info "Instaluję zależności z requirements.txt..."
        pip install -r requirements.txt
        print_success "Zależności Mancer Terminal zainstalowane"
    else
        print_warning "Plik requirements.txt nie istnieje"
    fi
    
    # Wróć do katalogu głównego
    cd ../..
}

# Sprawdź czy PyQt6 jest zainstalowane
check_pyqt6() {
    print_info "Sprawdzam instalację PyQt6..."
    
    if python3 -c "import PyQt6" 2>/dev/null; then
        print_success "PyQt6 jest zainstalowane"
    else
        print_error "PyQt6 nie jest zainstalowane"
        print_info "Instaluję PyQt6..."
        pip install PyQt6
        print_success "PyQt6 zainstalowane"
    fi
}

# Sprawdź czy Mancer jest dostępny
check_mancer() {
    print_info "Sprawdzam dostępność Mancer..."
    
    if python3 -c "import mancer" 2>/dev/null; then
        print_success "Mancer jest dostępny"
    else
        print_warning "Mancer nie jest dostępny - niektóre funkcje mogą nie działać"
    fi
}

# Uruchom test GUI
run_gui_test() {
    print_info "Uruchamiam test GUI..."
    
    cd prototypes/mancer-terminal
    
    if [[ -f "test_gui.py" ]]; then
        print_info "Uruchamiam test_gui.py..."
        python3 test_gui.py
        
        if [[ $? -eq 0 ]]; then
            print_success "Test GUI zakończony pomyślnie"
        else
            print_warning "Test GUI wykazał problemy"
        fi
    else
        print_warning "Plik test_gui.py nie istnieje"
    fi
    
    # Wróć do katalogu głównego
    cd ../..
}

# Uruchom Mancer Terminal GUI
run_terminal() {
    print_info "Uruchamiam Mancer Terminal GUI..."
    
    cd prototypes/mancer-terminal
    
    if [[ -f "main.py" ]]; then
        print_info "Uruchamiam GUI (main.py)..."
        python3 main.py
    else
        print_error "Plik main.py nie istnieje"
        exit 1
    fi
}

# Główna funkcja
main() {
    echo "🚀 Mancer Terminal - Skrypt uruchamiający"
    echo "=========================================="
    
    # Sprawdzenia wstępne
    check_directory
    check_python
    check_venv
    
    # Aktywuj venv
    activate_venv
    
    # Instalacja i aktualizacja
    upgrade_pip
    install_mancer_dev
    install_terminal_deps
    check_pyqt6
    check_mancer
    
    echo ""
    echo "🔧 Środowisko gotowe!"
    echo "=========================================="
    
    # Opcjonalny test GUI
    if [[ "$1" == "--test" ]]; then
        run_gui_test
        echo ""
    fi
    
    # Uruchom Mancer Terminal GUI
    print_info "Mancer Terminal to emulator terminala - uruchamiam GUI..."
    run_terminal
}

# Obsługa argumentów
case "${1:-}" in
    --help|-h)
        echo "Użycie: $0 [OPCJE]"
        echo ""
        echo "Mancer Terminal - SSH Terminal Emulator (GUI)"
        echo ""
        echo "Opcje:"
        echo "  --test     Uruchom test GUI przed uruchomieniem emulatora"
        echo "  --help     Pokaż tę pomoc"
        echo ""
        echo "Przykład:"
        echo "  $0 --test  # Uruchom test GUI, a następnie emulator terminala"
        echo "  $0         # Uruchom emulator terminala (GUI)"
        exit 0
        ;;
    --test)
        main "$@"
        ;;
    "")
        main "$@"
        ;;
    *)
        print_error "Nieznana opcja: $1"
        print_info "Użyj --help aby zobaczyć dostępne opcje"
        exit 1
        ;;
esac
