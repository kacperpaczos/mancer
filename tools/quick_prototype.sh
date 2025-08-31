#!/bin/bash

# Szybki Start Prototypów - skrypt do szybkiego uruchamiania prototypów frameworka Mancer

set -e

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funkcje pomocnicze
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Sprawdź czy jesteśmy w odpowiednim katalogu
check_workspace() {
    if [[ ! -d "src/mancer" ]]; then
        print_error "Uruchom skrypt z głównego katalogu projektu Mancer"
        exit 1
    fi
}

# Funkcja pomocy
show_help() {
    echo "🚀 SZYBKI START PROTOTYPÓW FRAMEWORKA MANCER"
    echo "=============================================="
    echo ""
    echo "Użycie: $0 [OPCJE] [NAZWA_PROTOTYPU]"
    echo ""
    echo "OPCJE:"
    echo "  -h, --help          Pokaż tę pomoc"
    echo "  -l, --list          Lista dostępnych prototypów"
    echo "  -c, --create        Utwórz nowy prototyp"
    echo "  -r, --run           Uruchom prototyp"
    echo "  -t, --test          Uruchom testy strategii"
    echo "  -s, --status        Status prototypów"
    echo ""
    echo "PRZYKŁADY:"
    echo "  $0 -l                    # Lista prototypów"
    echo "  $0 -c my-app 'Opis'     # Utwórz prototyp 'my-app'"
    echo "  $0 -r my-app            # Uruchom prototyp 'my-app'"
    echo "  $0 -t                   # Uruchom testy strategii"
    echo "  $0 -s                   # Status wszystkich prototypów"
    echo ""
}

# Lista prototypów
list_prototypes() {
    print_info "Lista dostępnych prototypów:"
    echo ""
    
    if [[ -d "prototypes" ]]; then
        for dir in prototypes/*/; do
            if [[ -d "$dir" ]]; then
                name=$(basename "$dir")
                if [[ -f "$dir/README.md" ]]; then
                    # Wyciągnij opis z README
                    description=$(grep -A1 "## Opis" "$dir/README.md" | tail -n1 | sed 's/^[[:space:]]*//')
                    if [[ -z "$description" ]]; then
                        description="Brak opisu"
                    fi
                else
                    description="Brak README"
                fi
                echo "  • $name: $description"
            fi
        done
    else
        print_warning "Katalog prototypes nie istnieje"
    fi
    echo ""
}

# Utwórz prototyp
create_prototype() {
    local name="$1"
    local description="$2"
    
    if [[ -z "$name" ]]; then
        print_error "Podaj nazwę prototypu"
        exit 1
    fi
    
    if [[ -z "$description" ]]; then
        print_error "Podaj opis prototypu"
        exit 1
    fi
    
    print_info "Tworzenie prototypu: $name"
    
    if [[ -d "prototypes/$name" ]]; then
        print_warning "Prototyp $name już istnieje"
        read -p "Czy chcesz go nadpisać? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Anulowano tworzenie prototypu"
            exit 0
        fi
        rm -rf "prototypes/$name"
    fi
    
    # Sprawdź czy szablon istnieje
    if [[ ! -d "prototypes/template" ]]; then
        print_error "Szablon prototypu nie istnieje. Uruchom najpierw testy strategii."
        exit 1
    fi
    
    # Skopiuj szablon
    cp -r "prototypes/template" "prototypes/$name"
    
    # Zaktualizuj pliki
    sed -i "s/Nazwa Prototypu/$name/g" "prototypes/$name/README.md"
    sed -i "s/Krótki opis tego, co robi prototyp/$description/g" "prototypes/$name/README.md"
    sed -i "s/prototype-template/prototype-$name/g" "prototypes/$name/pyproject.toml"
    sed -i "s/Szablon prototypu/$description/g" "prototypes/$name/pyproject.toml"
    
    print_success "Prototyp $name został utworzony"
    print_info "Ścieżka: prototypes/$name"
    print_info "Następne kroki:"
    print_info "  1. cd prototypes/$name"
    print_info "  2. Edytuj main.py"
    print_info "  3. Uruchom: $0 -r $name"
}

# Uruchom prototyp
run_prototype() {
    local name="$1"
    
    if [[ -z "$name" ]]; then
        print_error "Podaj nazwę prototypu do uruchomienia"
        exit 1
    fi
    
    if [[ ! -d "prototypes/$name" ]]; then
        print_error "Prototyp $name nie istnieje"
        exit 1
    fi
    
    if [[ ! -f "prototypes/$name/main.py" ]]; then
        print_error "Prototyp $name nie ma pliku main.py"
        exit 1
    fi
    
    print_info "Uruchamianie prototypu: $name"
    
    # Ustaw PYTHONPATH
    export PYTHONPATH="src:$PYTHONPATH"
    
    # Przejdź do katalogu prototypu i uruchom
    cd "prototypes/$name"
    
    print_info "Katalog roboczy: $(pwd)"
    print_info "PYTHONPATH: $PYTHONPATH"
    echo ""
    
    # Uruchom prototyp
    python main.py
    
    # Wróć do głównego katalogu
    cd ../..
}

# Testy strategii
run_tests() {
    print_info "Uruchamianie testów strategii prototypów..."
    
    if [[ -f "tools/test_prototype_strategy.py" ]]; then
        python tools/test_prototype_strategy.py
    else
        print_error "Plik testowy nie istnieje"
        exit 1
    fi
}

# Status prototypów
show_status() {
    print_info "Status prototypów frameworka Mancer:"
    echo ""
    
    # Sprawdź framework
    if [[ -d "src/mancer" ]]; then
        print_success "Framework: src/mancer (dostępny)"
    else
        print_error "Framework: src/mancer (brak)"
    fi
    
    # Sprawdź szablon
    if [[ -d "prototypes/template" ]]; then
        print_success "Szablon: prototypes/template (dostępny)"
    else
        print_error "Szablon: prototypes/template (brak)"
    fi
    
    # Sprawdź menedżer
    if [[ -f "tools/prototype_manager.py" ]]; then
        print_success "Menedżer: tools/prototype_manager.py (dostępny)"
    else
        print_error "Menedżer: tools/prototype_manager.py (brak)"
    fi
    
    echo ""
    
    # Lista prototypów z statusem
    if [[ -d "prototypes" ]]; then
        print_info "Prototypy:"
        for dir in prototypes/*/; do
            if [[ -d "$dir" ]]; then
                name=$(basename "$dir")
                if [[ "$name" == "template" ]]; then
                    echo "  • $name: [SZABLON]"
                else
                    if [[ -f "$dir/main.py" ]]; then
                        echo "  • $name: [GOTOWY]"
                    else
                        echo "  • $name: [NIEKOMPLETNY]"
                    fi
                fi
            fi
        done
    else
        print_warning "Brak katalogu prototypes"
    fi
    
    echo ""
}

# Główna logika
main() {
    check_workspace
    
    case "${1:-}" in
        -h|--help)
            show_help
            ;;
        -l|--list)
            list_prototypes
            ;;
        -c|--create)
            create_prototype "$2" "$3"
            ;;
        -r|--run)
            run_prototype "$2"
            ;;
        -t|--test)
            run_tests
            ;;
        -s|--status)
            show_status
            ;;
        "")
            show_help
            ;;
        *)
            print_error "Nieznana opcja: $1"
            show_help
            exit 1
            ;;
    esac
}

# Uruchom główną funkcję
main "$@"
