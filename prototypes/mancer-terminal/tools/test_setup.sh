#!/bin/bash

# Mancer Terminal - Test Setup
# Sprawdza czy środowisko jest gotowe do uruchomienia

set -e

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

echo "🧪 Mancer Terminal - Test Setup"
echo "================================"

# Sprawdź katalog
if [[ -f "prototypes/mancer-terminal/main.py" ]]; then
    print_success "Znaleziono main.py"
else
    print_error "main.py nie istnieje - uruchom z katalogu głównego"
    exit 1
fi

# Sprawdź Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python: $PYTHON_VERSION"
else
    print_error "Python3 nie jest dostępny"
    exit 1
fi

# Sprawdź venv
if [[ -d "venv" ]]; then
    print_success "Środowisko wirtualne istnieje"
else
    print_warning "Środowisko wirtualne nie istnieje"
fi

# Sprawdź src/mancer
if [[ -d "src/mancer" ]]; then
    print_success "Katalog src/mancer istnieje"
else
    print_warning "Katalog src/mancer nie istnieje"
fi

# Sprawdź requirements.txt
if [[ -f "prototypes/mancer-terminal/requirements.txt" ]]; then
    print_success "requirements.txt istnieje"
else
    print_error "requirements.txt nie istnieje"
    exit 1
fi

# Sprawdź GUI
if [[ -d "prototypes/mancer-terminal/gui" ]]; then
    print_success "Katalog GUI istnieje"
    
    # Sprawdź główne pliki GUI
    GUI_FILES=("main_window.py" "terminal_widget.py" "session_manager_widget.py" "file_transfer_widget.py" "connection_dialog.py")
    for file in "${GUI_FILES[@]}"; do
        if [[ -f "prototypes/mancer-terminal/gui/$file" ]]; then
            print_success "  ✅ $file"
        else
            print_error "  ❌ $file"
        fi
    done
else
    print_error "Katalog GUI nie istnieje"
    exit 1
fi

echo ""
echo "🔧 Środowisko gotowe do uruchomienia!"
echo "Uruchom: ./prototypes/mancer-terminal/tools/run_terminal.sh"
