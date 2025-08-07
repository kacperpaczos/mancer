#!/bin/bash
# 🧪 MANCER TESTS - Entry Point
set -euo pipefail

# Kolory
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; C='\033[0;36m'; NC='\033[0m'

show_menu() {
    echo -e "${B}"
    echo "================================================================="
    echo "🧪 MANCER TESTS - Wybierz typ testów"
    echo "================================================================="
    echo -e "${NC}"
    echo "1. Testy jednostkowe lokalnie (venv)"
    echo "2. Testy jednostkowe w Docker"
    echo "3. Pomoc"
    echo "4. Wyjście"
    echo
    echo -n "Wybierz opcję [1-4]: "
}

main() {
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [[ $# -gt 0 ]]; then
        case "$1" in
            "1"|"unit"|"local")
                exec "$SCRIPT_DIR/unittest.sh"
                ;;
            "2"|"docker")
                exec "$SCRIPT_DIR/unittest_docker.sh"
                ;;
            "help"|"h"|"-h"|"--help")
                show_menu
                echo
                echo "Użycie:"
                echo "  $0                  # Interaktywne menu"
                echo "  $0 1|unit|local     # Testy jednostkowe lokalnie"
                echo "  $0 2|docker         # Testy jednostkowe w Docker"
                echo "  $0 help             # Ta pomoc"
                echo
                echo "Bezpośrednie wywołania:"
                echo "  ./scripts/unittest.sh        # Lokalne unit testy"
                echo "  ./scripts/unittest_docker.sh # Docker unit testy"
                exit 0
                ;;
            *)
                echo -e "${R}❌ Nieznana opcja: $1${NC}"
                echo "Użyj '$0 help' aby zobaczyć dostępne opcje."
                exit 1
                ;;
        esac
    fi
    
    # Interaktywne menu
    while true; do
        show_menu
        read -r choice
        echo
        
        case $choice in
            1)
                echo -e "${G}🚀 Uruchamiam testy jednostkowe lokalnie...${NC}"
                exec "$SCRIPT_DIR/unittest.sh"
                ;;
            2)
                echo -e "${G}🐳 Uruchamiam testy jednostkowe w Docker...${NC}"
                exec "$SCRIPT_DIR/unittest_docker.sh"
                ;;
            3)
                show_menu
                echo
                echo "📝 Opis opcji:"
                echo "1. Lokalne - uruchamia testy w środowisku wirtualnym Python (szybkie)"
                echo "2. Docker - uruchamia testy w izolowanych kontenerach (pełna izolacja)"
                echo
                echo "Pliki:"
                echo "- tests/unit/          # Kod testów jednostkowych"
                echo "- scripts/unittest.sh  # Skrypt lokalny"
                echo "- scripts/unittest_docker.sh # Skrypt Docker"
                echo "- tests/docker/        # Konfiguracja Docker"
                echo
                read -p "Naciśnij Enter aby kontynuować..."
                clear
                ;;
            4)
                echo -e "${Y}👋 Do widzenia!${NC}"
                exit 0
                ;;
            *)
                echo -e "${R}❌ Nieprawidłowa opcja. Wybierz 1-4.${NC}"
                read -p "Naciśnij Enter aby spróbować ponownie..."
                clear
                ;;
        esac
    done
}

main "$@"
