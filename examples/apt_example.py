from mancer.application.shell_runner import ShellRunner
from mancer.application.commands.apt_command import AptCommand
from mancer.application.commands.systemctl_command import SystemctlCommand
import time
import getpass
from typing import Optional

def check_and_install_chronyd(runner: ShellRunner, sudo_password: Optional[str] = None) -> bool:
    """
    Sprawdza czy chronyd jest zainstalowany i instaluje go jeśli nie jest.
    
    Args:
        runner: Instancja ShellRunner
        sudo_password: Hasło do sudo (opcjonalnie)
        
    Returns:
        bool: True jeśli chronyd jest zainstalowany, False w przeciwnym razie
    """
    # Definiujemy nazwę polecenia (daemon) i pakietu który może je zawierać
    DAEMON_NAME = "chronyd"
    PACKAGE_NAME = "chrony"  # Pakiet, który prawdopodobnie zawiera daemon chronyd
    
    print(f"Sprawdzanie czy polecenie {DAEMON_NAME} jest dostępne w systemie...")
    
    # Sprawdź czy apt wymaga aktualizacji
    apt = AptCommand().with_sudo(sudo_password)
    print("Sprawdzanie, czy apt wymaga aktualizacji...")
    result = runner.execute(apt.needsUpdate())
    if result.success:
        needs_update = result.raw_output.strip().startswith("TRUE")
        print(f"Status aktualizacji apt: {result.raw_output.strip()}")
        
        if needs_update:
            print("Wykonywanie aktualizacji apt...")
            update_result = runner.execute(apt.update())
            if not update_result.success:
                print(f"Błąd podczas aktualizacji apt: {update_result.error_message}")
    
    # Sprawdź czy apt jest zablokowany i poczekaj jeśli tak
    print("Sprawdzanie, czy apt jest zablokowany...")
    
    # Używamy dedykowanej metody z AptCommand do odświeżania informacji o blokadzie
    print("") # Dodaj pustą linię przed wyświetlaniem informacji o statusie
    result = runner.execute_live(apt.refresh_if_locked(max_attempts=10, sleep_time=3, timeout=10))
    if not result.success:
        print("Apt jest zablokowany przez inny proces. Nie można kontynuować.")
        return False
    
    # Najpierw sprawdźmy czy polecenie chronyd jest dostępne w systemie
    print(f"Sprawdzanie czy polecenie {DAEMON_NAME} jest dostępne...")
    command_check = runner.execute(ShellRunner.create_bash_command(f"command -v {DAEMON_NAME} >/dev/null 2>&1 && echo 'TRUE' || echo 'FALSE'"))
    
    if command_check.success and command_check.raw_output.strip() == "TRUE":
        print(f"Polecenie {DAEMON_NAME} jest dostępne w systemie!")
        
        # Sprawdźmy, do jakiego pakietu należy to polecenie
        package_check = runner.execute(ShellRunner.create_bash_command(f"dpkg -S $(which {DAEMON_NAME}) 2>/dev/null | cut -d: -f1"))
        if package_check.success and package_check.raw_output.strip():
            actual_package = package_check.raw_output.strip()
            print(f"Polecenie {DAEMON_NAME} pochodzi z pakietu: {actual_package}")
            
            # Pobierzmy wersję pakietu
            ver_result = runner.execute(apt.get_package_version(actual_package))
            if ver_result.success:
                print(f"Zainstalowana wersja: {ver_result.raw_output.strip()}")
            
            return True
    
    # Sprawdź czy pakiet, który powinien zawierać chronyd, jest dostępny w repozytoriach
    print(f"Polecenie {DAEMON_NAME} nie jest dostępne. Sprawdzam dostępność pakietu {PACKAGE_NAME}...")
    package_available = runner.execute(ShellRunner.create_bash_command(f"apt-cache show {PACKAGE_NAME} >/dev/null 2>&1 && echo 'TRUE' || echo 'FALSE'"))
    
    if package_available.success and package_available.raw_output.strip() == "FALSE":
        print(f"Pakiet {PACKAGE_NAME} nie istnieje w repozytoriach. Nie można zainstalować polecenia {DAEMON_NAME}.")
        return False
    
    print(f"Pakiet {PACKAGE_NAME} jest dostępny. Rozpoczynam instalację...")
    
    # Instaluj pakiet
    print(f"Instalacja pakietu {PACKAGE_NAME}...")
    # Upewnij się, że używamy sudo
    if not sudo_password and "sudo" not in apt._options:
        print("UWAGA: Instalacja pakietu wymaga uprawnień sudo!")
    
    result = runner.execute(apt.install(PACKAGE_NAME))
    
    if result.success:
        # Sprawdźmy czy pakiet faktycznie został zainstalowany
        verify_result = runner.execute(apt.isInstalled(PACKAGE_NAME))
        if verify_result.success and verify_result.raw_output.strip().startswith("TRUE"):
            print(f"Pakiet {PACKAGE_NAME} został pomyślnie zainstalowany!")
            
            # Sprawdźmy czy polecenie chronyd jest teraz dostępne
            command_check = runner.execute(ShellRunner.create_bash_command(f"command -v {DAEMON_NAME} >/dev/null 2>&1 && echo 'TRUE' || echo 'FALSE'"))
            if command_check.success and command_check.raw_output.strip() == "TRUE":
                print(f"Polecenie {DAEMON_NAME} jest teraz dostępne w systemie!")
            else:
                print(f"Uwaga: Pakiet {PACKAGE_NAME} został zainstalowany, ale polecenie {DAEMON_NAME} nadal nie jest dostępne.")
                print("Może być potrzebna dodatkowa konfiguracja lub inny pakiet.")
            
            # Pobierz zainstalowaną wersję
            ver_result = runner.execute(apt.get_package_version(PACKAGE_NAME))
            if ver_result.success:
                print(f"Zainstalowana wersja: {ver_result.raw_output.strip()}")
            
            # Pobierz listę poleceń dostarczanych przez pakiet
            cmd_result = runner.execute(apt.get_commands_for_package(PACKAGE_NAME))
            if cmd_result.success:
                print(f"Polecenia dostarczane przez pakiet:")
                for line in cmd_result.raw_output.strip().split("\n")[1:]:  # Pomiń pierwszy wiersz z nagłówkiem
                    if line.strip():
                        print(f"  - {line.strip()}")
            
            return True
        else:
            print(f"Mimo że komenda instalacji zwróciła sukces, pakiet {PACKAGE_NAME} nie został zainstalowany.")
            print("Prawdopodobnie wystąpił problem z uprawnieniami lub konfiguracją apt.")
            return False
    else:
        print(f"Wystąpił błąd podczas instalacji pakietu {PACKAGE_NAME}!")
        if "E: Unable to locate package" in result.raw_output:
            print(f"Pakiet {PACKAGE_NAME} nie istnieje w repozytoriach. Nie można zainstalować polecenia {DAEMON_NAME}.")
        else:
            print(f"Błąd: {result.error_message}")
        return False

def main():
    # Inicjalizacja runnera
    runner = ShellRunner(
        backend_type="bash",
        enable_cache=True,
        cache_max_size=100,
        enable_live_output=True  # Włączamy wyświetlanie wyjścia w czasie rzeczywistym
    )
    
    print("=== Demonstracja użycia komend apt ===\n")
    
    # Pobierz hasło sudo
    sudo_password = "Kz2.+Ac#" #getpass.getpass("Podaj hasło sudo (jeśli wymagane): ")
    if not sudo_password:
        sudo_password = None
    
    # Sprawdź i zainstaluj chronyd
    check_and_install_chronyd(runner, sudo_password)
    
    # Pokaż przykłady innych komend apt
    print("\nPrzykłady innych komend apt:")
    apt = AptCommand().with_sudo(sudo_password)
    
    # Sprawdź czas ostatniej aktualizacji apt
    print("\nSprawdzanie czasu ostatniej aktualizacji apt:")
    result = runner.execute(apt.getLastUpdateTime())
    if result.success:
        print(f"Ostatnia aktualizacja apt: {result.raw_output.strip()}")
    
    # Pobierz liczbę dostępnych aktualizacji
    print("\nSprawdzanie liczby dostępnych aktualizacji:")
    result = runner.execute(apt.get_updates_count())
    if result.success:
        print(f"Liczba dostępnych aktualizacji: {result.raw_output.strip()}")
    
    # Sprawdź status repozytoriów
    print("\nSprawdzanie statusu repozytoriów apt:")
    result = runner.execute(apt.get_repository_status())
    if result.success:
        print("Status repozytoriów:")
        lines = result.raw_output.split('\n')
        # Wyświetl tylko pierwsze 3 linie wyników
        for i, line in enumerate(lines):
            if i < 3:
                print(f"  {line}")
        if len(lines) > 3:
            print(f"  ... oraz {len(lines)-3} więcej linii")
    
    # Sprawdź status usługi chronyd
    print("\nSprawdzanie statusu usługi chronyd:")
    systemctl = SystemctlCommand().with_sudo(sudo_password)
    result = runner.execute(systemctl.status("chrony"))
    if result.success:
        print("Status usługi chronyd:")
        lines = result.raw_output.split('\n')
        # Wyświetl pierwsze 5 linii statusu
        for i, line in enumerate(lines):
            if i < 5:
                print(f"  {line}")
    
    # Sprawdź listę pakietów do aktualizacji
    print("\nLista pakietów do aktualizacji:")
    result = runner.execute(apt.list_upgradable_packages())
    if result.success:
        lines = result.raw_output.split('\n')
        if len(lines) > 1:  # Więcej niż nagłówek
            # Wyświetl tylko pierwsze 5 linii wyników
            for i, line in enumerate(lines):
                if i < 5:
                    print(f"  {line}")
            if len(lines) > 5:
                print(f"  ... oraz {len(lines)-5} więcej pakietów")
        else:
            print("  Brak pakietów do aktualizacji")
    
    print("\nDostępne funkcje do zarządzania apt:")
    print("  1. Podstawowe komendy:")
    print("     - apt.install(package) - instalacja pakietu")
    print("     - apt.remove(package) - usuwanie pakietu")
    print("     - apt.purge(package) - usuwanie pakietu wraz z konfiguracją")
    print("     - apt.update() - aktualizacja listy pakietów")
    print("     - apt.upgrade() - aktualizacja pakietów")
    print("     - apt.autoremove() - usuwanie nieużywanych pakietów")
    print("     - apt.clean() - czyszczenie cache")
    
    print("\n  2. Sprawdzanie stanu:")
    print("     - apt.isInstalled(package) - sprawdzanie czy pakiet jest zainstalowany (TRUE/FALSE)")
    print("     - apt.is_installed(package) - sprawdzanie czy pakiet jest zainstalowany (tekstowo)")
    print("     - apt.get_package_version(package) - pobieranie wersji pakietu")
    print("     - apt.get_commands_for_package(package) - pobieranie listy poleceń z pakietu")
    print("     - apt.get_updates_count() - liczba dostępnych aktualizacji")
    print("     - apt.get_repository_status() - status repozytoriów")
    print("     - apt.list_installed_packages() - lista zainstalowanych pakietów")
    print("     - apt.list_upgradable_packages() - lista pakietów do aktualizacji")
    
    print("\n  3. Zarządzanie blokadami i stanem apt:")
    print("     - apt.check_if_locked() - sprawdzenie czy apt jest zablokowany")
    print("     - apt.wait_if_locked(max_attempts, sleep_time) - czekanie aż apt nie będzie zablokowany")
    print("     - apt.refresh_if_locked(max_attempts, sleep_time) - odświeżanie informacji o blokadzie co określony czas")
    print("     - apt.getLastUpdateTime() - pobieranie czasu ostatniej aktualizacji apt")
    print("     - apt.needsUpdate(max_age_seconds) - sprawdzanie czy apt wymaga aktualizacji")
    print("     - apt.updateIfNeeded(max_age_seconds) - aktualizacja apt tylko jeśli potrzeba")
    
    print("\n  4. Zaawansowane opcje:")
    print("     - apt.with_sudo(password) - dodanie sudo do komendy")
    print("     - apt.full_upgrade() - pełna aktualizacja systemu (update + upgrade + autoremove)")
    print("     - apt.download_only() - tylko pobieranie pakietów bez instalacji")
    print("     - apt.no_install_recommends() - bez instalacji rekomendowanych pakietów")
    print("     - apt.force_yes() - wymuszenie odpowiedzi 'tak' na wszystkie pytania")

if __name__ == "__main__":
    main() 