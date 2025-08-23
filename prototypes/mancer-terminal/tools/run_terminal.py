#!/usr/bin/env python3
"""
Mancer Terminal - Skrypt uruchamiający (Python)
Uruchamia Mancer Terminal w środowisku wirtualnym z deweloperskim Mancerem
"""

import os
import subprocess
import sys
import venv
from pathlib import Path
from typing import List, Optional, Tuple


# Kolory dla output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_info(message: str):
    """Wyświetla informację"""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def print_success(message: str):
    """Wyświetla sukces"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def print_warning(message: str):
    """Wyświetla ostrzeżenie"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def print_error(message: str):
    """Wyświetla błąd"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def run_command(
    command: List[str], cwd: Optional[Path] = None, check: bool = True
) -> Tuple[int, str, str]:
    """Uruchamia komendę i zwraca (return_code, stdout, stderr)"""
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=check)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr


def check_directory() -> bool:
    """Sprawdza czy jesteśmy w odpowiednim katalogu"""
    if not Path("prototypes/mancer-terminal/main.py").exists():
        print_error("Skrypt musi być uruchomiony z katalogu głównego projektu Mancer")
        print_info("Przejdź do katalogu głównego i uruchom ponownie")
        return False
    return True


def check_python() -> bool:
    """Sprawdza czy Python jest dostępny"""
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print_error(f"Wymagany Python 3.8+, dostępny: {version.major}.{version.minor}")
            return False

        print_success(f"Znaleziono Python {version.major}.{version.minor}.{version.micro}")
        return True
    except Exception as e:
        print_error(f"Błąd sprawdzania wersji Pythona: {e}")
        return False


def check_venv() -> bool:
    """Sprawdza czy venv istnieje"""
    venv_path = Path("venv")
    if not venv_path.exists():
        print_warning("Środowisko wirtualne nie istnieje. Tworzę nowe...")
        return create_venv()
    else:
        print_success("Znaleziono istniejące środowisko wirtualne")
        return True


def create_venv() -> bool:
    """Tworzy nowe środowisko wirtualne"""
    try:
        print_info("Tworzę nowe środowisko wirtualne...")
        venv.create("venv", with_pip=True)
        print_success("Środowisko wirtualne utworzone")
        return True
    except Exception as e:
        print_error(f"Błąd tworzenia środowiska wirtualnego: {e}")
        return False


def activate_venv() -> bool:
    """Aktywuje środowisko wirtualne"""
    try:
        venv_path = Path("venv")
        if not venv_path.exists():
            print_error("Środowisko wirtualne nie istnieje")
            return False

        # Sprawdź czy jesteśmy w venv
        if hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            print_success("Środowisko wirtualne jest już aktywne")
            return True

        # Aktywuj venv
        activate_script = venv_path / "bin" / "activate_this.py"
        if activate_script.exists():
            with open(activate_script) as f:
                exec(f.read(), {"__file__": str(activate_script)})
            print_success("Środowisko wirtualne aktywowane")
            return True
        else:
            print_warning(
                "Nie można automatycznie aktywować venv - uruchom ręcznie: source venv/bin/activate"
            )
            return True
    except Exception as e:
        print_error(f"Błąd aktywacji środowiska wirtualnego: {e}")
        return False


def upgrade_pip() -> bool:
    """Aktualizuje pip"""
    try:
        print_info("Aktualizuję pip...")
        return_code, stdout, stderr = run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        )

        if return_code == 0:
            print_success("pip zaktualizowany")
            return True
        else:
            print_warning(f"pip nie został zaktualizowany: {stderr}")
            return False
    except Exception as e:
        print_error(f"Błąd aktualizacji pip: {e}")
        return False


def install_mancer_dev() -> bool:
    """Instaluje Mancer w trybie deweloperskim"""
    try:
        print_info("Instaluję Mancer w trybie deweloperskim...")

        src_path = Path("src/mancer")
        if src_path.exists():
            print_info("Instaluję z katalogu src/mancer...")
            return_code, stdout, stderr = run_command(
                [sys.executable, "-m", "pip", "install", "-e", "src/"]
            )

            if return_code == 0:
                print_success("Mancer zainstalowany w trybie deweloperskim")
                return True
            else:
                print_warning(f"Instalacja Mancer nie powiodła się: {stderr}")
                return False
        else:
            print_warning("Katalog src/mancer nie istnieje, pomijam instalację Mancer")
            return True
    except Exception as e:
        print_error(f"Błąd instalacji Mancer: {e}")
        return False


def install_terminal_deps() -> bool:
    """Instaluje zależności Mancer Terminal"""
    try:
        print_info("Instaluję zależności Mancer Terminal...")

        requirements_path = Path("prototypes/mancer-terminal/requirements.txt")
        if requirements_path.exists():
            print_info("Instaluję zależności z requirements.txt...")
            return_code, stdout, stderr = run_command(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)]
            )

            if return_code == 0:
                print_success("Zależności Mancer Terminal zainstalowane")
                return True
            else:
                print_warning(f"Instalacja zależności nie powiodła się: {stderr}")
                return False
        else:
            print_warning("Plik requirements.txt nie istnieje")
            return False
    except Exception as e:
        print_error(f"Błąd instalacji zależności: {e}")
        return False


def check_pyqt6() -> bool:
    """Sprawdza czy PyQt6 jest zainstalowane"""
    try:
        print_info("Sprawdzam instalację PyQt6...")

        return_code, stdout, stderr = run_command(
            [sys.executable, "-c", "import PyQt6"], check=False
        )

        if return_code == 0:
            print_success("PyQt6 jest zainstalowane")
            return True
        else:
            print_info("Instaluję PyQt6...")
            return_code, stdout, stderr = run_command(
                [sys.executable, "-m", "pip", "install", "PyQt6"]
            )

            if return_code == 0:
                print_success("PyQt6 zainstalowane")
                return True
            else:
                print_error(f"Instalacja PyQt6 nie powiodła się: {stderr}")
                return False
    except Exception as e:
        print_error(f"Błąd sprawdzania/instalacji PyQt6: {e}")
        return False


def check_mancer() -> bool:
    """Sprawdza czy Mancer jest dostępny"""
    try:
        print_info("Sprawdzam dostępność Mancer...")

        return_code, stdout, stderr = run_command(
            [sys.executable, "-c", "import mancer"], check=False
        )

        if return_code == 0:
            print_success("Mancer jest dostępny")
            return True
        else:
            print_warning("Mancer nie jest dostępny - niektóre funkcje mogą nie działać")
            return False
    except Exception as e:
        print_error(f"Błąd sprawdzania Mancer: {e}")
        return False


def run_gui_test() -> bool:
    """Uruchamia test GUI"""
    try:
        print_info("Uruchamiam test GUI...")

        test_path = Path("prototypes/mancer-terminal/test_gui.py")
        if test_path.exists():
            print_info("Uruchamiam test_gui.py...")
            return_code, stdout, stderr = run_command([sys.executable, str(test_path)], check=False)

            if return_code == 0:
                print_success("Test GUI zakończony pomyślnie")
                return True
            else:
                print_warning("Test GUI wykazał problemy")
                if stderr:
                    print_info(f"Błędy: {stderr}")
                return False
        else:
            print_warning("Plik test_gui.py nie istnieje")
            return False
    except Exception as e:
        print_error(f"Błąd uruchamiania testu GUI: {e}")
        return False


def run_terminal() -> bool:
    """Uruchamia Mancer Terminal GUI"""
    try:
        print_info("Uruchamiam Mancer Terminal GUI...")

        main_path = Path("prototypes/mancer-terminal/main.py")
        if main_path.exists():
            print_info("Uruchamiam GUI (main.py)...")
            # Uruchom w nowym procesie
            subprocess.run([sys.executable, str(main_path)])
            return True
        else:
            print_error("Plik main.py nie istnieje")
            return False
    except Exception as e:
        print_error(f"Błąd uruchamiania GUI: {e}")
        return False


def show_help():
    """Wyświetla pomoc"""
    print("Użycie: python run_terminal.py [OPCJE]")
    print("")
    print("Mancer Terminal - SSH Terminal Emulator (GUI)")
    print("")
    print("Opcje:")
    print("  --test     Uruchom test GUI przed uruchomieniem emulatora")
    print("  --help     Pokaż tę pomoc")
    print("")
    print("Przykład:")
    print("  python run_terminal.py --test  # Uruchom test GUI, a następnie emulator terminala")
    print("  python run_terminal.py         # Uruchom emulator terminala (GUI)")


def main():
    """Główna funkcja"""
    print("🚀 Mancer Terminal - Skrypt uruchamiający (Python)")
    print("==================================================")

    # Sprawdź argumenty
    test_mode = "--test" in sys.argv
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
        return

    # Sprawdzenia wstępne
    if not check_directory():
        return

    if not check_python():
        return

    if not check_venv():
        return

    # Aktywuj venv
    if not activate_venv():
        return

    # Instalacja i aktualizacja
    upgrade_pip()
    install_mancer_dev()
    install_terminal_deps()
    check_pyqt6()
    check_mancer()

    print("")
    print("🔧 Środowisko gotowe!")
    print("==================================================")

    # Opcjonalny test GUI
    if test_mode:
        run_gui_test()
        print("")

    # Uruchom Mancer Terminal GUI
    print_info("Mancer Terminal to emulator terminala - uruchamiam GUI...")
    run_terminal()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrzerwano przez użytkownika")
        sys.exit(1)
    except Exception as e:
        print_error(f"Nieoczekiwany błąd: {e}")
        sys.exit(1)
