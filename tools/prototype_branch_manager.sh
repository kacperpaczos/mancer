#!/bin/bash

# Menedżer Gałęzi Prototypów - zarządza gałęziami Git dla prototypów frameworka Mancer

set -e

# Kolory dla output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Sprawdź czy jesteśmy w repozytorium Git
check_git_repo() {
    if [[ ! -d ".git" ]]; then
        print_error "Nie jesteś w repozytorium Git"
        exit 1
    fi
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
    echo "🚀 MENEDŻER GAŁĘZI PROTOTYPÓW FRAMEWORKA MANCER"
    echo "================================================="
    echo ""
    echo "Użycie: $0 [OPCJE] [NAZWA_GAŁĘZI]"
    echo ""
    echo "OPCJE:"
    echo "  -h, --help          Pokaż tę pomoc"
    echo "  -s, --status        Status gałęzi prototypów"
    echo "  -c, --create        Utwórz nową gałąź prototypów"
    echo "  -p, --push          Wypchnij gałąź prototypów na remote"
    echo "  -u, --update        Zaktualizuj gałąź prototypów z remote"
    echo "  -m, --merge         Merguj udane funkcjonalności do main"
    echo "  -d, --delete        Usuń gałąź prototypów (lokalnie)"
    echo "  -l, --list          Lista wszystkich gałęzi"
    echo "  -b, --backup        Backup gałęzi prototypów"
    echo ""
    echo "PRZYKŁADY:"
    echo "  $0 -s                    # Status gałęzi prototypów"
    echo "  $0 -c feature-name       # Utwórz gałąź feature-name"
    echo "  $0 -p                    # Wypchnij zmiany na remote"
    echo "  $0 -u                    # Zaktualizuj z remote"
    echo "  $0 -m                    # Merguj do main"
    echo "  $0 -d feature-name       # Usuń gałąź feature-name"
    echo ""
}

# Status gałęzi prototypów
show_status() {
    print_header "Status gałęzi prototypów"
    echo ""
    
    # Aktualna gałąź
    current_branch=$(git branch --show-current)
    print_info "Aktualna gałąź: $current_branch"
    
    # Sprawdź czy jesteśmy na gałęzi prototypów
    if [[ "$current_branch" == "main" ]]; then
        print_warning "Jesteś na gałęzi main - przełącz na gałąź prototypów"
        echo ""
        print_info "Dostępne gałęzie prototypów:"
        git branch | grep -v "main" | grep -v "master" | sed 's/^  /  • /'
    else
        print_success "Jesteś na gałęzi prototypów: $current_branch"
        
        # Status względem remote
        if git rev-parse --verify "origin/$current_branch" >/dev/null 2>&1; then
            local_commit=$(git rev-parse HEAD)
            remote_commit=$(git rev-parse "origin/$current_branch")
            
            if [[ "$local_commit" == "$remote_commit" ]]; then
                print_success "Gałąź jest zsynchronizowana z remote"
            else
                ahead=$(git rev-list --count "origin/$current_branch..HEAD")
                behind=$(git rev-list --count "HEAD..origin/$current_branch")
                
                if [[ $ahead -gt 0 ]]; then
                    print_warning "Lokalna gałąź jest $ahead commitów przed remote"
                fi
                if [[ $behind -gt 0 ]]; then
                    print_warning "Lokalna gałąź jest $behind commitów za remote"
                fi
            fi
        else
            print_warning "Gałąź nie istnieje na remote"
        fi
        
        # Status plików
        echo ""
        print_info "Status plików:"
        git status --short
    fi
    
    echo ""
}

# Lista wszystkich gałęzi
list_branches() {
    print_header "Lista wszystkich gałęzi"
    echo ""
    
    print_info "Gałęzie lokalne:"
    git branch --format="  %(HEAD) %(color:green)%(refname:short)%(color:reset) - %(subject)"
    
    echo ""
    print_info "Gałęzie remote:"
    git branch -r --format="  %(refname:short) - %(subject)"
    
    echo ""
    print_info "Legenda:"
    echo "  * - aktualna gałąź"
    echo "  origin/ - gałęzie na remote"
    echo ""
}

# Utwórz nową gałąź prototypów
create_prototype_branch() {
    local branch_name="$1"
    
    if [[ -z "$branch_name" ]]; then
        print_error "Podaj nazwę gałęzi prototypów"
        exit 1
    fi
    
    # Sprawdź czy gałąź już istnieje
    if git rev-parse --verify "$branch_name" >/dev/null 2>&1; then
        print_warning "Gałąź $branch_name już istnieje"
        read -p "Czy chcesz się na nią przełączyć? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git checkout "$branch_name"
            print_success "Przełączono na gałąź $branch_name"
        fi
        return
    fi
    
    # Sprawdź czy jesteśmy na main
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]]; then
        print_warning "Jesteś na gałęzi $current_branch, nie na main"
        read -p "Czy chcesz przełączyć się na main i utworzyć nową gałąź? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Anulowano tworzenie gałęzi"
            return
        fi
        git checkout main
    fi
    
    # Utwórz nową gałąź
    git checkout -b "$branch_name"
    print_success "Utworzono i przełączono na gałąź $branch_name"
    
    # Skopiuj pliki prototypów jeśli nie istnieją
    if [[ ! -d "prototypes/template" ]]; then
        print_info "Kopiowanie plików prototypów..."
        mkdir -p prototypes
        cp -r ../prototypes/template prototypes/ 2>/dev/null || print_warning "Nie można skopiować szablonu"
    fi
    
    print_info "Następne kroki:"
    print_info "  1. Rozwijaj prototypy na tej gałęzi"
    print_info "  2. Commit zmiany: git add . && git commit -m 'Opis zmian'"
    print_info "  3. Wypchnij na remote: $0 -p"
}

# Wypchnij gałąź prototypów na remote
push_prototype_branch() {
    current_branch=$(git branch --show-current)
    
    if [[ "$current_branch" == "main" ]]; then
        print_error "Jesteś na gałęzi main - przełącz na gałąź prototypów"
        exit 1
    fi
    
    print_info "Wypychanie gałęzi $current_branch na remote..."
    
    # Sprawdź czy są niezacommitowane zmiany
    if [[ -n "$(git status --porcelain)" ]]; then
        print_warning "Masz niezacommitowane zmiany"
        git status --short
        echo ""
        read -p "Czy chcesz je zacommitować teraz? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Wiadomość commita: " commit_message
            if [[ -n "$commit_message" ]]; then
                git add .
                git commit -m "$commit_message"
            else
                print_error "Brak wiadomości commita"
                return
            fi
        else
            print_info "Anulowano wypychanie"
            return
        fi
    fi
    
    # Wypchnij na remote
    if git push -u origin "$current_branch"; then
        print_success "Gałąź $current_branch została wypchnięta na remote"
    else
        print_error "Błąd wypychania gałęzi"
        exit 1
    fi
}

# Zaktualizuj gałąź prototypów z remote
update_prototype_branch() {
    current_branch=$(git branch --show-current)
    
    if [[ "$current_branch" == "main" ]]; then
        print_error "Jesteś na gałęzi main - przełącz na gałąź prototypów"
        exit 1
    fi
    
    print_info "Aktualizowanie gałęzi $current_branch z remote..."
    
    # Sprawdź czy gałąź istnieje na remote
    if ! git rev-parse --verify "origin/$current_branch" >/dev/null 2>&1; then
        print_warning "Gałąź $current_branch nie istnieje na remote"
        return
    fi
    
    # Pobierz zmiany z remote
    git fetch origin
    
    # Sprawdź czy są zmiany do pobrania
    local_commit=$(git rev-parse HEAD)
    remote_commit=$(git rev-parse "origin/$current_branch")
    
    if [[ "$local_commit" == "$remote_commit" ]]; then
        print_success "Gałąź jest już aktualna"
        return
    fi
    
    # Sprawdź czy są lokalne zmiany
    if [[ -n "$(git status --porcelain)" ]]; then
        print_warning "Masz lokalne zmiany - stashuj je przed aktualizacją"
        read -p "Czy chcesz je stashować? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash push -m "Stash przed aktualizacją z remote"
            stashed=true
        else
            print_info "Anulowano aktualizację"
            return
        fi
    fi
    
    # Aktualizuj gałąź
    if git pull origin "$current_branch"; then
        print_success "Gałąź $current_branch została zaktualizowana"
        
        # Przywróć stash jeśli był
        if [[ "$stashed" == "true" ]]; then
            print_info "Przywracanie stash..."
            git stash pop
        fi
    else
        print_error "Błąd aktualizacji gałęzi"
        exit 1
    fi
}

# Merguj udane funkcjonalności do main
merge_to_main() {
    current_branch=$(git branch --show-current)
    
    if [[ "$current_branch" == "main" ]]; then
        print_error "Jesteś już na gałęzi main"
        exit 1
    fi
    
    print_info "Mergowanie funkcjonalności z gałęzi $current_branch do main..."
    
    # Sprawdź czy są niezacommitowane zmiany
    if [[ -n "$(git status --porcelain)" ]]; then
        print_error "Masz niezacommitowane zmiany - commit je przed mergowaniem"
        git status --short
        exit 1
    fi
    
    # Przełącz na main
    git checkout main
    
    # Pobierz najnowsze zmiany z main
    git pull origin main
    
    # Merguj gałąź prototypów
    if git merge "$current_branch"; then
        print_success "Funkcjonalności zostały pomyślnie zmergowane do main"
        
        # Wypchnij zmiany na remote
        read -p "Czy chcesz wypchnąć zmiany na remote? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git push origin main
            print_success "Zmiany zostały wypchnięte na remote"
        fi
        
        # Usuń gałąź prototypów
        read -p "Czy chcesz usunąć gałąź $current_branch? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git branch -d "$current_branch"
            print_success "Gałąź $current_branch została usunięta lokalnie"
            
            # Usuń z remote
            read -p "Czy chcesz usunąć gałąź z remote? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git push origin --delete "$current_branch"
                print_success "Gałąź $current_branch została usunięta z remote"
            fi
        fi
    else
        print_error "Błąd mergowania - rozwiąż konflikty i dokończ merge"
        print_info "Po rozwiązaniu konfliktów: git add . && git commit"
        exit 1
    fi
}

# Usuń gałąź prototypów
delete_prototype_branch() {
    local branch_name="$1"
    
    if [[ -z "$branch_name" ]]; then
        print_error "Podaj nazwę gałęzi do usunięcia"
        exit 1
    fi
    
    # Sprawdź czy gałąź istnieje
    if ! git rev-parse --verify "$branch_name" >/dev/null 2>&1; then
        print_error "Gałąź $branch_name nie istnieje"
        exit 1
    fi
    
    # Sprawdź czy nie jesteśmy na tej gałęzi
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" == "$branch_name" ]]; then
        print_error "Nie możesz usunąć aktualnej gałęzi - przełącz na inną"
        exit 1
    fi
    
    # Potwierdź usunięcie
    print_warning "Usunięcie gałęzi $branch_name spowoduje utratę wszystkich lokalnych zmian!"
    read -p "Czy na pewno chcesz usunąć gałąź $branch_name? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Anulowano usuwanie gałęzi"
        return
    fi
    
    # Usuń gałąź
    if git branch -D "$branch_name"; then
        print_success "Gałąź $branch_name została usunięta lokalnie"
        
        # Usuń z remote jeśli istnieje
        if git rev-parse --verify "origin/$branch_name" >/dev/null 2>&1; then
            read -p "Czy chcesz usunąć gałąź z remote? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git push origin --delete "$branch_name"
                print_success "Gałąź $branch_name została usunięta z remote"
            fi
        fi
    else
        print_error "Błąd usuwania gałęzi"
        exit 1
    fi
}

# Backup gałęzi prototypów
backup_prototype_branches() {
    print_header "Backup gałęzi prototypów"
    echo ""
    
    # Utwórz katalog backup
    backup_dir="backup_prototypes_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    print_info "Tworzenie backup w katalogu: $back_dir"
    
    # Lista gałęzi prototypów (wszystkie oprócz main/master)
    prototype_branches=$(git branch | grep -v "main" | grep -v "master" | sed 's/^[[:space:]]*//')
    
    if [[ -z "$prototype_branches" ]]; then
        print_warning "Brak gałęzi prototypów do backup"
        return
    fi
    
    # Backup każdej gałęzi
    for branch in $prototype_branches; do
        print_info "Backup gałęzi: $branch"
        
        # Utwórz katalog dla gałęzi
        branch_dir="$backup_dir/$branch"
        mkdir -p "$branch_dir"
        
        # Zapisz informacje o gałęzi
        git show-branch "$branch" > "$branch_dir/branch_info.txt" 2>/dev/null || true
        git log --oneline "$branch" > "$branch_dir/commit_history.txt" 2>/dev/null || true
        
        # Zapisz diff względem main
        git diff main.."$branch" > "$branch_dir/diff_vs_main.patch" 2>/dev/null || true
        
        print_success "  ✓ Backup gałęzi $branch ukończony"
    done
    
    # Utwórz plik README z informacjami
    cat > "$backup_dir/README.md" << EOF
# Backup Gałęzi Prototypów

Data: $(date)
Gałąź bazowa: main

## Zawartość backup

$(for branch in $prototype_branches; do echo "- $branch"; done)

## Jak przywrócić

1. Przejdź do katalogu backup
2. Sprawdź pliki diff_vs_main.patch
3. Zastosuj zmiany: git apply diff_vs_main.patch
4. Utwórz nową gałąź: git checkout -b nazwa_gałęzi

## Uwagi

- Backup zawiera tylko diff względem main
- Nie zawiera pełnej historii commitów
- Przywracanie może wymagać ręcznej interwencji
EOF
    
    print_success "Backup ukończony w katalogu: $backup_dir"
    print_info "Zawartość:"
    ls -la "$backup_dir"
}

# Główna logika
main() {
    check_git_repo
    check_workspace
    
    case "${1:-}" in
        -h|--help)
            show_help
            ;;
        -s|--status)
            show_status
            ;;
        -l|--list)
            list_branches
            ;;
        -c|--create)
            create_prototype_branch "$2"
            ;;
        -p|--push)
            push_prototype_branch
            ;;
        -u|--update)
            update_prototype_branch
            ;;
        -m|--merge)
            merge_to_main
            ;;
        -d|--delete)
            delete_prototype_branch "$2"
            ;;
        -b|--backup)
            backup_prototype_branches
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
