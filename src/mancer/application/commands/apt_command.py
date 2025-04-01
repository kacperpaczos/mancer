from typing import Optional, List, cast, Dict, Any
from .base_command import BaseCommand, T
import time
import os
import json
from datetime import datetime

class AptCommand(BaseCommand):
    """Klasa do obsługi komend apt"""
    
    # Plik do przechowywania stanu apt
    APT_STATE_FILE = os.path.expanduser("~/.mancer/apt_state.json")
    
    def __init__(self):
        super().__init__("apt")
        self._ensure_state_dir()
        self._state = self._load_state()
    
    def _ensure_state_dir(self) -> None:
        """Upewnia się, że katalog stanu istnieje"""
        state_dir = os.path.dirname(self.APT_STATE_FILE)
        if not os.path.exists(state_dir):
            try:
                os.makedirs(state_dir, exist_ok=True)
            except:
                pass  # Ignorujemy błędy - użyjemy pamięci tymczasowej jeśli nie możemy zapisać na dysku
    
    def _load_state(self) -> Dict[str, Any]:
        """Ładuje stan apt z pliku"""
        if os.path.exists(self.APT_STATE_FILE):
            try:
                with open(self.APT_STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return self._get_default_state()
        return self._get_default_state()
    
    def _save_state(self) -> None:
        """Zapisuje stan apt do pliku"""
        try:
            with open(self.APT_STATE_FILE, 'w') as f:
                json.dump(self._state, f, indent=2)
        except:
            pass  # Ignorujemy błędy zapisu
    
    def _get_default_state(self) -> Dict[str, Any]:
        """Zwraca domyślny stan apt"""
        return {
            "last_update": None,  # Czas ostatniej aktualizacji (apt update)
            "installed_packages": {},  # Pakiety zainstalowane przez ten framework
            "auto_update_interval": 86400,  # Domyślny interwał aktualizacji - 1 dzień
            "is_updated": False  # Czy apt było aktualizowane
        }
    
    def _update_state(self, key: str, value: Any) -> None:
        """Aktualizuje stan apt"""
        self._state[key] = value
        self._save_state()
    
    def _update_installed_package(self, package: str, version: str) -> None:
        """Aktualizuje informacje o zainstalowanym pakiecie"""
        self._state["installed_packages"][package] = {
            "version": version,
            "install_time": datetime.now().isoformat()
        }
        self._save_state()
    
    def with_sudo(self, password: Optional[str] = None) -> 'AptCommand':
        """
        Dodaje sudo do komendy.
        
        Args:
            password: Hasło do sudo (opcjonalnie)
            
        Returns:
            self: Instancja komendy (do łańcuchowania metod)
        """
        if password:
            return cast(AptCommand, self.with_param("sudo_password", password))
        return cast(AptCommand, self.with_option("sudo"))
    
    def install(self, package: str) -> 'AptCommand':
        """Instaluje pakiet"""
        return cast(AptCommand, self.with_param("command", "install").with_param("package", package).with_option("y"))
    
    def remove(self, package: str) -> 'AptCommand':
        """Usuwa pakiet"""
        return cast(AptCommand, self.with_param("command", "remove").with_param("package", package).with_option("y"))
    
    def purge(self, package: str) -> 'AptCommand':
        """Usuwa pakiet wraz z plikami konfiguracyjnymi"""
        return cast(AptCommand, self.with_param("command", "purge").with_param("package", package).with_option("y"))
    
    def update(self) -> 'AptCommand':
        """Aktualizuje listę dostępnych pakietów"""
        # Dodajemy informację o aktualizacji stanu
        return cast(AptCommand, self.with_param("command", "update").with_param("update_state", True))
    
    def upgrade(self) -> 'AptCommand':
        """Aktualizuje zainstalowane pakiety"""
        return cast(AptCommand, self.with_param("command", "upgrade").with_option("y"))
    
    def search(self, query: str) -> 'AptCommand':
        """Wyszukuje pakiety"""
        return cast(AptCommand, self.with_param("command", "search").with_param("query", query))
    
    def show(self, package: str) -> 'AptCommand':
        """Pokazuje szczegółowe informacje o pakiecie"""
        return cast(AptCommand, self.with_param("command", "show").with_param("package", package))
    
    def clean(self) -> 'AptCommand':
        """Czyści cache apt"""
        return cast(AptCommand, self.with_param("command", "clean"))
    
    def autoremove(self) -> 'AptCommand':
        """Usuwa nieużywane pakiety"""
        return cast(AptCommand, self.with_param("command", "autoremove").with_option("y"))
    
    def is_installed(self, package: str) -> 'AptCommand':
        """Sprawdza czy pakiet jest zainstalowany"""
        return cast(AptCommand, self.with_param("command", "list").with_param("package", f"^{package}$").with_option("installed"))
    
    def isInstalled(self, package: str) -> 'AptCommand':
        """
        Sprawdza czy pakiet jest zainstalowany (zwraca boolean).
        Metoda odporna na język używany w systemie i różne nazwy binarek.
        
        Args:
            package: Nazwa pakietu
            
        Returns:
            AptCommand: Komenda do sprawdzania, czy pakiet jest zainstalowany
        """
        # Użyjemy dpkg-query, które sprawdza bezpośrednio bazę danych pakietów
        # Szukamy dokładnie stanu 'install ok installed', który jest stały w dpkg
        cmd = f"""
        # Sprawdź dokładną nazwę pakietu dla bezpieczeństwa
        if dpkg-query -W -f='${{{{Status}}}}' {package} 2>/dev/null | grep -q 'install ok installed'; then
            echo 'TRUE'
        else
            # Spróbuj też szukać z wildcards, gdy nazwa może być częścią większego pakietu
            if dpkg -l | grep -q "^ii.*{package}"; then
                echo 'TRUE'
            else
                # Sprawdź czy pakiet istnieje, ale pod inną nazwą
                # Na przykład pakiet 'chrony' ma polecenia 'chronyd' i 'chronyc'
                if command -v {package} >/dev/null 2>&1; then
                    # Pakiet (lub polecenie) istnieje w systemie
                    echo 'TRUE'
                elif command -v {package}d >/dev/null 2>&1 || command -v {package}c >/dev/null 2>&1; then
                    # Sprawdź typowe sufiksy (daemon, client)
                    echo 'TRUE (jako {package}d lub {package}c)'
                else
                    # Sprawdź czy pakiet jest dostępny w apt
                    PKG_INFO=$(apt-cache show {package} 2>/dev/null)
                    if [ $? -eq 0 ]; then
                        echo 'FALSE (dostępny, ale nie zainstalowany)'
                    else
                        echo 'FALSE (niedostępny)'
                    fi
                fi
            fi
        fi
        """
        return cast(AptCommand, self.with_param("command", "is-installed-bool")
                             .with_param("package", package)
                             .with_param("custom_cmd", cmd))
    
    def getLastUpdateTime(self) -> 'AptCommand':
        """
        Pobiera czas ostatniej aktualizacji apt.
        
        Returns:
            AptCommand: Komenda zwracająca czas ostatniej aktualizacji
        """
        # Zwróć zapisany stan lub sprawdź plik znacznika apt
        cmd = f"""
        # Sprawdź plik stanu frameworka
        if [ -f "{self.APT_STATE_FILE}" ]; then
            LAST_UPDATE=$(cat "{self.APT_STATE_FILE}" | grep -o '"last_update": "[^"]*"' | cut -d'"' -f4)
            if [ -n "$LAST_UPDATE" ] && [ "$LAST_UPDATE" != "null" ]; then
                echo "$LAST_UPDATE"
                exit 0
            fi
        fi
        
        # Sprawdź faktyczny czas ostatniej aktualizacji z plików apt
        if [ -f /var/lib/apt/periodic/update-success-stamp ]; then
            stat -c %Y /var/lib/apt/periodic/update-success-stamp
        elif [ -f /var/cache/apt/pkgcache.bin ]; then
            stat -c %Y /var/cache/apt/pkgcache.bin
        else
            echo "nieznany"
        fi
        """
        return cast(AptCommand, self.with_param("command", "get-last-update")
                             .with_param("custom_cmd", cmd))
    
    def needsUpdate(self, max_age_seconds: int = 86400) -> 'AptCommand':
        """
        Sprawdza czy apt wymaga aktualizacji (na podstawie wieku ostatniej aktualizacji).
        
        Args:
            max_age_seconds: Maksymalny wiek aktualizacji w sekundach (domyślnie 1 dzień)
            
        Returns:
            AptCommand: Komenda zwracająca TRUE/FALSE czy apt wymaga aktualizacji
        """
        cmd = f"""
        # Sprawdź plik stanu frameworka
        if [ -f "{self.APT_STATE_FILE}" ]; then
            IS_UPDATED=$(cat "{self.APT_STATE_FILE}" | grep -o '"is_updated": [^,}}]*' | cut -d' ' -f2)
            LAST_UPDATE=$(cat "{self.APT_STATE_FILE}" | grep -o '"last_update": "[^"]*"' | cut -d'"' -f4)
            if [ "$IS_UPDATED" = "true" ]; then
                echo "FALSE (zaktualizowano w ramach tej sesji)"
                exit 0
            fi
            if [ -n "$LAST_UPDATE" ] && [ "$LAST_UPDATE" != "null" ]; then
                # Sprawdź czy aktualizacja jest wystarczająco świeża
                NOW=$(date +%s)
                UPDATE_TIME=$(date -d "$LAST_UPDATE" +%s 2>/dev/null || echo 0)
                if [ $UPDATE_TIME -ne 0 ]; then
                    AGE=$((NOW - UPDATE_TIME))
                    if [ $AGE -lt {max_age_seconds} ]; then
                        echo "FALSE (zaktualizowano $LAST_UPDATE)"
                        exit 0
                    else
                        echo "TRUE (ostatnia aktualizacja: $LAST_UPDATE, wiek: $AGE s)"
                        exit 0
                    fi
                fi
            fi
        fi
        
        # Sprawdź faktyczny czas ostatniej aktualizacji
        if [ -f /var/lib/apt/periodic/update-success-stamp ]; then
            NOW=$(date +%s)
            UPDATE_TIME=$(stat -c %Y /var/lib/apt/periodic/update-success-stamp)
            AGE=$((NOW - UPDATE_TIME))
            if [ $AGE -lt {max_age_seconds} ]; then
                echo "FALSE (zaktualizowano $(date -d @$UPDATE_TIME '+%Y-%m-%d %H:%M:%S'))"
            else
                echo "TRUE (ostatnia aktualizacja: $(date -d @$UPDATE_TIME '+%Y-%m-%d %H:%M:%S'), wiek: $AGE s)"
            fi
        else
            echo "TRUE (brak informacji o aktualizacji)"
        fi
        """
        return cast(AptCommand, self.with_param("command", "needs-update")
                             .with_param("custom_cmd", cmd))
    
    def updateIfNeeded(self, max_age_seconds: int = 86400) -> 'AptCommand':
        """
        Aktualizuje apt tylko jeśli minął określony czas od ostatniej aktualizacji.
        
        Args:
            max_age_seconds: Maksymalny wiek aktualizacji w sekundach (domyślnie 1 dzień)
            
        Returns:
            AptCommand: Komenda aktualizująca apt jeśli potrzeba
        """
        # Pobierz komendę sprawdzającą potrzebę aktualizacji
        needs_update_cmd = self.needsUpdate(max_age_seconds)._params.get("custom_cmd", "")
        
        # Utwórz komendę aktualizującą
        cmd_template = """
        # Sprawdź czy aktualizacja jest potrzebna
        needs_update_output=$(
{needs_update_cmd}
        )
        
        if echo "$needs_update_output" | grep -q "^TRUE"; then
            echo "Aktualizacja potrzebna. $needs_update_output"
            apt update
            exit_code=$?
            if [ $exit_code -eq 0 ]; then
                echo "Aktualizacja zakończona pomyślnie."
                # Aktualizacja pliku stanu
                mkdir -p "$(dirname "{apt_state_file}")" 2>/dev/null
                if [ -f "{apt_state_file}" ]; then
                    # Aktualizuj istniejący plik
                    TMP_FILE=$(mktemp)
                    sed_cmd1='s/"last_update": "[^"]*"/"last_update": "'$(date -Iseconds)'"/'
                    sed_cmd2='s/"is_updated": [^,}]*/"is_updated": true/'
                    cat "{apt_state_file}" | sed "$sed_cmd1" | sed "$sed_cmd2" > $TMP_FILE
                    mv $TMP_FILE "{apt_state_file}"
                else
                    # Utwórz nowy plik
                    echo '{{"last_update": "'$(date -Iseconds)'", "installed_packages": {{}}, "auto_update_interval": {max_age_seconds}, "is_updated": true}}' > "{apt_state_file}"
                fi
                exit 0
            else
                echo "Błąd podczas aktualizacji."
                exit $exit_code
            fi
        else
            echo "Aktualizacja niepotrzebna. $needs_update_output"
            exit 0
        fi
        """
        
        # Użyj format zamiast f-stringa
        cmd = cmd_template.format(
            needs_update_cmd=needs_update_cmd,
            apt_state_file=self.APT_STATE_FILE,
            max_age_seconds=max_age_seconds
        )
        return cast(AptCommand, self.with_param("command", "update-if-needed")
                             .with_param("custom_cmd", cmd))
    
    def dist_upgrade(self) -> 'AptCommand':
        """Aktualizuje dystrybucję"""
        return cast(AptCommand, self.with_param("command", "dist-upgrade").with_option("y"))
    
    def no_install_recommends(self) -> 'AptCommand':
        """Nie instaluje pakietów rekomendowanych"""
        return cast(AptCommand, self.with_option("no-install-recommends"))
    
    def no_install_suggests(self) -> 'AptCommand':
        """Nie instaluje pakietów sugerowanych"""
        return cast(AptCommand, self.with_option("no-install-suggests"))
    
    def force_yes(self) -> 'AptCommand':
        """Wymusza instalację bez pytania o potwierdzenie"""
        return cast(AptCommand, self.with_option("force-yes"))
    
    # Nowe metody do sprawdzania stanu apt i obsługi blokad
    
    def check_if_locked(self) -> 'AptCommand':
        """
        Sprawdza czy apt jest zablokowany przez inny proces.
        Zwraca wynik w postaci wyjścia polecenia lsof sprawdzającego blokadę.
        """
        cmd = "lsof /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock"
        return cast(AptCommand, self.with_param("command", "check-lock").with_param("custom_cmd", cmd))
    
    def wait_if_locked(self, max_attempts: int = 60, sleep_time: int = 5) -> 'AptCommand':
        """
        Czeka, jeśli apt jest zablokowany przez inny proces.
        
        Args:
            max_attempts: Maksymalna liczba prób (domyślnie 60)
            sleep_time: Czas oczekiwania między próbami w sekundach (domyślnie 5)
            
        Returns:
            AptCommand: Komenda, która będzie czekać, aż apt nie będzie zablokowany
        """
        return cast(AptCommand, self.with_param("command", "wait-lock")
                              .with_param("max_attempts", max_attempts)
                              .with_param("sleep_time", sleep_time))
    
    def refresh_if_locked(self, max_attempts: int = 10, sleep_time: int = 3, timeout: int = 10) -> 'AptCommand':
        """
        Sprawdza czy apt jest zablokowany, odświeżając informację co określoną liczbę sekund.
        
        Args:
            max_attempts: Maksymalna liczba prób (domyślnie 10)
            sleep_time: Czas oczekiwania między próbami w sekundach (domyślnie 3)
            timeout: Maksymalny czas wykonania całego polecenia w sekundach (domyślnie 10)
            
        Returns:
            AptCommand: Komenda, która sprawdza blokadę apt z odświeżaniem ekranu
        """
        cmd_template = """
        max_attempts={max_attempts}
        sleep_time={sleep_time}
        timeout={timeout}
        attempt=1
        
        # Funkcja do wypisywania informacji z nadpisaniem poprzedniej linii
        print_refresh() {{
            # Najpierw usuń poprzednią linię (przesuń kursor do początku linii i wyczyść ją)
            echo -en "\\r\\033[K"
            # Wypisz nową informację
            echo -n "$1"
        }}

        # Utwórz funkcję, która wykona sprawdzanie z timeoutem
        check_lock_with_timeout() {{
            # Uruchom komendę lsof w tle z timeoutem
            ( lsof /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock >/dev/null 2>&1 ) & pid=$!
            
            # Czekaj na zakończenie procesu, maksymalnie {timeout} sekund
            ( sleep $timeout && kill -9 $pid 2>/dev/null ) & watcher=$!
            wait $pid 2>/dev/null 
            lock_status=$?
            
            # Zatrzymaj proces watchera (jeśli jeszcze działa)
            kill -9 $watcher 2>/dev/null || true
            
            # Jeśli proces lsof zakończył się kodem 0, to apt jest zablokowany
            return $lock_status
        }}

        # Ustaw timer na cały proces
        SECONDS=0

        while [ $attempt -le $max_attempts ] && [ $SECONDS -lt $timeout ]; do
            # Sprawdź czy apt jest zablokowany z timeoutem
            if check_lock_with_timeout; then
                # Odśwież informację na ekranie
                print_refresh "Apt jest zablokowany. Próba $attempt/$max_attempts. Odświeżam za $sleep_time sekundy... (czas: ${{SECONDS}}s)"
                
                # Czekaj przez sleep_time, ale nie dłużej niż pozostały timeout
                remaining_time=$(( timeout - SECONDS ))
                sleep_now=$(( sleep_time < remaining_time ? sleep_time : remaining_time ))
                
                if [ $sleep_now -le 0 ]; then
                    # Jeśli upłynął timeout, zakończymy pętlę w następnej iteracji
                    sleep 0.1
                else
                    sleep $sleep_now
                fi
                
                attempt=$((attempt+1))
            else
                print_refresh "Apt nie jest zablokowany. Kontynuuję... (czas: ${{SECONDS}}s)"
                echo  # Dodaj pustą linię na końcu
                exit 0
            fi
        done
        
        # Sprawdź dlaczego zakończyliśmy pętlę
        if [ $SECONDS -ge $timeout ]; then
            print_refresh "Upłynął timeout ($timeout sekund). Kontynuuję..."
            echo  # Dodaj pustą linię na końcu
            exit 0
        else
            print_refresh "Osiągnięto maksymalną liczbę prób ($max_attempts). Apt nadal zablokowany."
            echo  # Dodaj pustą linię na końcu
            exit 1
        fi
        """
        
        cmd = cmd_template.format(
            max_attempts=max_attempts,
            sleep_time=sleep_time,
            timeout=timeout
        )
        
        return cast(AptCommand, self.with_param("command", "refresh-if-locked")
                             .with_param("custom_cmd", cmd))
    
    def get_updates_count(self) -> 'AptCommand':
        """
        Pobiera liczbę dostępnych aktualizacji.
        """
        cmd = "apt list --upgradable | grep -c upgradable || echo 0"
        return cast(AptCommand, self.with_param("command", "updates-count").with_param("custom_cmd", cmd))
    
    def get_package_version(self, package: str) -> 'AptCommand':
        """
        Pobiera wersję zainstalowanego pakietu.
        
        Args:
            package: Nazwa pakietu
            
        Returns:
            AptCommand: Komenda do pobrania wersji pakietu
        """
        cmd = f"""
        # Najpierw sprawdź czy pakiet jest zainstalowany
        if dpkg-query -W -f='${{{{Status}}}}' {package} 2>/dev/null | grep -q 'install ok installed'; then
            # Jeśli jest zainstalowany, pobierz wersję
            dpkg-query -W -f='${{{{Version}}}}' {package} 2>/dev/null
        else
            # Spróbuj też szukać z wildcards, gdy nazwa może być częścią większego pakietu
            PKG=$(dpkg -l | grep "^ii.*{package}" | head -n 1 | awk '{{{{print $2}}}}')
            if [ -n "$PKG" ]; then
                VERSION=$(dpkg-query -W -f='${{{{Version}}}}' $PKG 2>/dev/null)
                echo "$VERSION (pakiet: $PKG)"
            else
                # Sprawdź czy pakiet ma inną nazwę
                if command -v {package}d >/dev/null 2>&1; then
                    # Sprawdź, do jakiego pakietu należy binarka
                    PKG=$(dpkg -S $(which {package}d) 2>/dev/null | cut -d: -f1)
                    if [ -n "$PKG" ]; then
                        VERSION=$(dpkg-query -W -f='${{{{Version}}}}' $PKG 2>/dev/null)
                        echo "$VERSION (pakiet: $PKG, binarka: {package}d)"
                    else
                        echo "nie zainstalowany (binarka {package}d istnieje, ale pakiet nieznany)"
                    fi
                elif command -v {package}c >/dev/null 2>&1; then
                    # Sprawdź, do jakiego pakietu należy binarka
                    PKG=$(dpkg -S $(which {package}c) 2>/dev/null | cut -d: -f1)
                    if [ -n "$PKG" ]; then
                        VERSION=$(dpkg-query -W -f='${{{{Version}}}}' $PKG 2>/dev/null)
                        echo "$VERSION (pakiet: $PKG, binarka: {package}c)"
                    else
                        echo "nie zainstalowany (binarka {package}c istnieje, ale pakiet nieznany)"
                    fi
                else
                    echo "nie zainstalowany"
                fi
            fi
        fi
        """
        return cast(AptCommand, self.with_param("command", "package-version")
                              .with_param("package", package)
                              .with_param("custom_cmd", cmd))
    
    def get_repository_status(self) -> 'AptCommand':
        """
        Pobiera status repozytoriów apt (włączone/wyłączone).
        """
        cmd = "grep -v '^#' /etc/apt/sources.list /etc/apt/sources.list.d/*.list 2>/dev/null | sort"
        return cast(AptCommand, self.with_param("command", "repo-status").with_param("custom_cmd", cmd))
    
    def list_installed_packages(self) -> 'AptCommand':
        """
        Pobiera listę zainstalowanych pakietów.
        """
        return cast(AptCommand, self.with_param("command", "list").with_option("installed"))
    
    def list_upgradable_packages(self) -> 'AptCommand':
        """
        Pobiera listę pakietów, które można zaktualizować.
        """
        return cast(AptCommand, self.with_param("command", "list").with_option("upgradable"))
    
    def full_upgrade(self) -> 'AptCommand':
        """
        Wykonuje pełną aktualizację systemu (update + upgrade + autoremove).
        To bardziej bezpieczna wersja dist-upgrade.
        """
        return cast(AptCommand, self.with_param("command", "full-upgrade").with_option("y"))
    
    def download_only(self) -> 'AptCommand':
        """
        Tylko pobiera pakiety, bez instalacji.
        """
        return cast(AptCommand, self.with_option("download-only"))
    
    def get_commands_for_package(self, package: str) -> 'AptCommand':
        """
        Pobiera listę poleceń dostarczanych przez pakiet.
        
        Args:
            package: Nazwa pakietu
            
        Returns:
            AptCommand: Komenda do pobrania listy poleceń
        """
        cmd = f"""
        # Sprawdź czy pakiet jest zainstalowany
        if ! dpkg -l {package} 2>/dev/null | grep -q '^ii'; then
            echo "Pakiet {package} nie jest zainstalowany"
            exit 1
        fi
        
        # Pobierz listę plików w pakiecie
        echo "Polecenia dostarczone przez pakiet {package}:"
        
        # Lista plików w ścieżkach binarnych
        dpkg -L {package} | grep -E '/s?bin/' | sort | while read cmd; do
            if [ -x "$cmd" ] && [ -f "$cmd" ]; then
                echo "$(basename "$cmd")"
            fi
        done
        
        # Lista plików w usr/bin
        dpkg -L {package} | grep -E '/usr/s?bin/' | sort | while read cmd; do
            if [ -x "$cmd" ] && [ -f "$cmd" ]; then
                echo "$(basename "$cmd")"
            fi
        done
        """
        return cast(AptCommand, self.with_param("command", "get-commands")
                             .with_param("package", package)
                             .with_param("custom_cmd", cmd))
    
    def build_command(self) -> str:
        """
        Buduje pełną komendę z parametrami.
        
        Returns:
            str: Pełna komenda gotowa do wykonania
        """
        # Obsługa specjalnych komend
        if "command" in self._params:
            # Sprawdzanie blokady
            if self._params["command"] == "check-lock" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Czekanie na zwolnienie blokady
            elif self._params["command"] == "wait-lock":
                max_attempts = self._params.get("max_attempts", 60)
                sleep_time = self._params.get("sleep_time", 5)
                
                # Tworzymy skrypt, który będzie czekać na zwolnienie blokady
                cmd = f"""
                max_attempts={max_attempts}
                sleep_time={sleep_time}
                attempt=1

                while lsof /var/lib/dpkg/lock /var/lib/apt/lists/lock /var/cache/apt/archives/lock >/dev/null 2>&1; do
                    echo "Apt jest zablokowany. Próba $attempt/$max_attempts. Czekam {sleep_time}s..."
                    if [ $attempt -ge $max_attempts ]; then
                        echo "Osiągnięto maksymalną liczbę prób. Apt nadal zablokowany."
                        exit 1
                    fi
                    sleep {sleep_time}
                    attempt=$((attempt+1))
                done
                
                echo "Apt jest odblokowany."
                exit 0
                """
                # Uruchamiamy skrypt w bashu
                return f"bash -c '{cmd}'"
            
            # Odświeżanie informacji o blokadzie
            elif self._params["command"] == "refresh-if-locked" and "custom_cmd" in self._params:
                # Uruchamiamy skrypt w bashu
                return f"bash -c '{self._params['custom_cmd']}'"
            
            # Pobieranie liczby aktualizacji
            elif self._params["command"] == "updates-count" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Pobieranie wersji pakietu
            elif self._params["command"] == "package-version" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Sprawdzanie czy pakiet jest zainstalowany (boolean)
            elif self._params["command"] == "is-installed-bool" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Pobieranie statusu repozytoriów
            elif self._params["command"] == "repo-status" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Pobieranie czasu ostatniej aktualizacji
            elif self._params["command"] == "get-last-update" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Sprawdzanie czy potrzebna jest aktualizacja
            elif self._params["command"] == "needs-update" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Aktualizacja jeśli potrzebna
            elif self._params["command"] == "update-if-needed" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Pobieranie poleceń z pakietu
            elif self._params["command"] == "get-commands" and "custom_cmd" in self._params:
                return self._params["custom_cmd"]
                
            # Pełna aktualizacja
            elif self._params["command"] == "full-upgrade":
                cmd = "apt update && apt upgrade -y && apt autoremove -y"
                if "download-only" in self._options:
                    cmd = "apt update && apt upgrade -y --download-only && apt autoremove -y"
                
                # Aktualizacja stanu - zapisujemy czas aktualizacji
                cmd_template = """
                # Aktualizacja pliku stanu
                mkdir -p "$(dirname "{apt_state_file}")" 2>/dev/null
                if [ -f "{apt_state_file}" ]; then
                    # Aktualizuj istniejący plik
                    TMP_FILE=$(mktemp)
                    sed_cmd1='s/"last_update": "[^"]*"/"last_update": "'"$(date -Iseconds)"'"/'
                    sed_cmd2='s/"is_updated": [^,}]*/"is_updated": true/'
                    cat "{apt_state_file}" | sed "$sed_cmd1" | sed "$sed_cmd2" > $TMP_FILE
                    mv $TMP_FILE "{apt_state_file}"
                else
                    # Utwórz nowy plik
                    echo '{{"last_update": "'"$(date -Iseconds)"'", "installed_packages": {{}}, "auto_update_interval": 86400, "is_updated": true}}' > "{apt_state_file}"
                fi
                """
                cmd += cmd_template.format(apt_state_file=self.APT_STATE_FILE)
                return cmd
                
            # Jeśli komenda to list --installed, zamień na specjalną składnię dla apt list
            elif self._params["command"] == "list" and "package" in self._params:
                command = f"apt list --installed | grep -i {self._params['package']}"
                
            # Aktualizacja apt
            elif self._params["command"] == "update":
                command = super().build_command()
                
                # Jeśli mamy aktualizować stan, dodajemy kod do aktualizacji pliku stanu
                if "update_state" in self._params and self._params["update_state"]:
                    update_template = """
                    # Aktualizacja pliku stanu po sukcesie
                    if [ $? -eq 0 ]; then
                        mkdir -p "$(dirname "{apt_state_file}")" 2>/dev/null
                        if [ -f "{apt_state_file}" ]; then
                            # Aktualizuj istniejący plik
                            TMP_FILE=$(mktemp)
                            sed_cmd1='s/"last_update": "[^"]*"/"last_update": "'"$(date -Iseconds)"'"/'
                            sed_cmd2='s/"is_updated": [^,}]*/"is_updated": true/'
                            cat "{apt_state_file}" | sed "$sed_cmd1" | sed "$sed_cmd2" > $TMP_FILE
                            mv $TMP_FILE "{apt_state_file}"
                        else
                            # Utwórz nowy plik
                            echo '{{"last_update": "'"$(date -Iseconds)"'", "installed_packages": {{}}, "auto_update_interval": 86400, "is_updated": true}}' > "{apt_state_file}"
                        fi
                    fi
                    """
                    command += update_template.format(apt_state_file=self.APT_STATE_FILE)
                
            # Instalacja pakietu
            elif self._params["command"] == "install" and "package" in self._params:
                package = self._params["package"]
                command = super().build_command()
                
                # Dodajemy sprawdzenie, czy instalacja się powiodła i zapisanie informacji o pakiecie
                install_template = """
                # Zapisanie informacji o pakiecie po sukcesie
                if [ $? -eq 0 ]; then
                    # Sprawdź czy pakiet został zainstalowany
                    if dpkg-query -W -f='${{{{Status}}}}' {package} 2>/dev/null | grep -q 'install ok installed'; then
                        VERSION=$(dpkg-query -W -f='${{{{Version}}}}' {package} 2>/dev/null)
                        
                        # Aktualizuj plik stanu
                        mkdir -p "$(dirname "{apt_state_file}")" 2>/dev/null
                        if [ -f "{apt_state_file}" ]; then
                            # Pusta sekcja
                            sed_cmd='s/"installed_packages": {{}}/"installed_packages": {{"{package}": {{"version": "'$VERSION'", "install_time": "'$(date -Iseconds)'"}}}}/g'
                            cat "{apt_state_file}" | sed "$sed_cmd" > $TMP_FILE
                            mv $TMP_FILE "{apt_state_file}"
                        else
                            # Niepusta sekcja
                            sed_cmd='s/"installed_packages": {{/"installed_packages": {{"{package}": {{"version": "'$VERSION'", "install_time": "'$(date -Iseconds)'"}}, /g'
                            cat "{apt_state_file}" | sed "$sed_cmd" > $TMP_FILE
                            mv $TMP_FILE "{apt_state_file}"
                        fi
                        
                        echo "Pakiet {package} został zainstalowany w wersji $VERSION."
                        
                        # Informacje o poleceniach pakietu
                        echo "Polecenia dostarczone przez pakiet {package}:"
                        # Lista plików w ścieżkach binarnych
                        for bin_path in /bin /sbin /usr/bin /usr/sbin; do
                            if dpkg -L {package} 2>/dev/null | grep -q "^$bin_path/"; then
                                dpkg -L {package} | grep "^$bin_path/" | while read cmd; do
                                    if [ -x "$cmd" ] && [ -f "$cmd" ]; then
                                        echo "- $(basename "$cmd")"
                                    fi
                                done
                            fi
                        done
                    else
                        echo "Mimo kodu sukcesu apt, pakiet {package} nie został zainstalowany."
                    fi
                fi
                """
                command += install_template.format(apt_state_file=self.APT_STATE_FILE, package=package)
            
            # Obsługa zwykłych komend apt
            else:
                command = super().build_command()
        else:
            command = super().build_command()
        
        # Dodaj sudo jeśli wymagane
        if "sudo_password" in self._params:
            password = self._params["sudo_password"]
            command = f"echo '{password}' | sudo -S {command}"
        elif "sudo" in self._options:
            command = f"sudo {command}"
        
        return command 