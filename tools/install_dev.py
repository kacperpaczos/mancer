#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import sys
from pathlib import Path

def aktualizuj_wersje():
    """
    Aktualizuje wersję w pliku setup.py, zwiększając ostatnią cyfrę w formacie X.Y.Z
    """
    setup_path = Path('setup.py').resolve()
    
    # Sprawdź czy plik istnieje
    if not setup_path.exists():
        print(f"Błąd: Nie znaleziono pliku {setup_path}")
        return False
    
    # Odczytaj zawartość pliku
    with open(setup_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Znajdź aktualną wersję
    version_pattern = r'version="(\d+)\.(\d+)\.(\d+)"'
    match = re.search(version_pattern, content)
    
    if not match:
        print("Błąd: Nie znaleziono wersji w formacie X.Y.Z w pliku setup.py")
        return False
    
    # Pobierz aktualne wartości X.Y.Z
    x, y, z = map(int, match.groups())
    
    # Zwiększ wartość Z
    nowa_wersja = f"{x}.{y}.{z+1}"
    
    # Zastąp starą wersję nową
    nowa_zawartosc = re.sub(version_pattern, f'version="{nowa_wersja}"', content)
    
    # Zapisz zaktualizowaną zawartość
    with open(setup_path, 'w', encoding='utf-8') as f:
        f.write(nowa_zawartosc)
    
    print(f"Zaktualizowano wersję do {nowa_wersja}")
    return True

def utworz_venv():
    """
    Tworzy środowisko wirtualne Python, jeśli jeszcze nie istnieje
    """
    venv_path = Path('.venv')
    
    if venv_path.exists():
        print("Środowisko wirtualne już istnieje, pomijam tworzenie")
        return True
    
    print("Tworzenie środowiska wirtualnego...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', '.venv'], check=True)
        print("Środowisko wirtualne zostało utworzone pomyślnie")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas tworzenia środowiska wirtualnego: {e}")
        return False

def instaluj_pakiet_deweloperski():
    """
    Instaluje pakiet w trybie deweloperskim w środowisku wirtualnym
    """
    # Określ ścieżkę do interpretera Python w środowisku wirtualnym
    if sys.platform == 'win32':
        python = '.venv\\Scripts\\python'
    else:
        python = '.venv/bin/python'
    
    # Sprawdź czy interpreter istnieje
    if not os.path.exists(python):
        print(f"Błąd: Nie znaleziono interpretera Python w środowisku wirtualnym: {python}")
        return False
    
    print("Instalowanie pakietu w trybie deweloperskim...")
    try:
        # Aktualizacja pip
        subprocess.run([python, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        
        # Instalacja wymagań
        subprocess.run([python, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        
        # Instalacja pakietu w trybie deweloperskim
        subprocess.run([python, '-m', 'pip', 'install', '-e', '.'], check=True)
        
        print("Pakiet został zainstalowany pomyślnie w trybie deweloperskim")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas instalacji pakietu: {e}")
        return False

def aktywuj_venv():
    """
    Aktywuje środowisko wirtualne i uruchamia podaną komendę lub interpreter
    """
    print("Aktywuję środowisko wirtualne...")
    
    # Określ ścieżkę do aktywacji venv
    if sys.platform == 'win32':
        activate_script = '.venv\\Scripts\\activate'
        cmd = f"start cmd /k \"cd {os.getcwd()} && {activate_script}\""
    else:
        activate_script = '.venv/bin/activate'
        cmd = f"gnome-terminal -- bash -c 'cd {os.getcwd()} && source {activate_script}; exec bash'"
        # Alternatywnie możemy spróbować standardowo
        if not os.path.exists("/usr/bin/gnome-terminal"):
            cmd = f"x-terminal-emulator -e 'bash -c \"cd {os.getcwd()} && source {activate_script}; exec bash\"'"
    
    try:
        if sys.platform == 'win32':
            os.system(cmd)
        else:
            # Spróbuj kilka różnych terminali
            success = False
            for terminal_cmd in [
                f"gnome-terminal -- bash -c 'cd {os.getcwd()} && source {activate_script}; exec bash'",
                f"xterm -e 'cd {os.getcwd()} && source {activate_script}; exec bash'",
                f"konsole -e 'cd {os.getcwd()} && source {activate_script}; exec bash'",
                f"xfce4-terminal -e 'cd {os.getcwd()} && source {activate_script}; exec bash'"
            ]:
                try:
                    result = subprocess.run(terminal_cmd, shell=True, stderr=subprocess.DEVNULL)
                    if result.returncode == 0:
                        success = True
                        break
                except:
                    pass
            
            if not success:
                print("Nie udało się automatycznie otworzyć terminala.")
                print(f"Aby aktywować środowisko, wykonaj: source {activate_script}")
                return False
        
        print("Środowisko zostało aktywowane w nowym oknie terminala.")
        return True
    except Exception as e:
        print(f"Błąd podczas aktywacji środowiska: {e}")
        print(f"Aby aktywować środowisko ręcznie, wykonaj:")
        if sys.platform == 'win32':
            print(f"\t{activate_script}")
        else:
            print(f"\tsource {activate_script}")
        return False

def main():
    print("=== Instalacja wersji deweloperskiej Mancer ===")
    
    # Przejdź do katalogu głównego projektu (gdzie znajduje się setup.py)
    os.chdir(Path(__file__).parent.parent)
    
    # Pobierz argumenty wiersza poleceń
    force = False
    auto_activate = False
    
    for arg in sys.argv[1:]:
        if arg in ['-f', '--force']:
            force = True
        elif arg in ['-a', '--activate']:
            auto_activate = True
    
    # Sprawdź czy jesteśmy w środowisku wirtualnym
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("Jesteś już w środowisku wirtualnym, kontynuuję instalację...")
    
    # Aktualizuj wersję
    if not aktualizuj_wersje():
        print("Ostrzeżenie: Nie udało się zaktualizować wersji, kontynuuję instalację...")
    
    # Utwórz środowisko wirtualne
    if not utworz_venv():
        print("Błąd: Nie udało się utworzyć środowiska wirtualnego")
        return 1
    
    # Zainstaluj pakiet
    if not instaluj_pakiet_deweloperski():
        print("Błąd: Nie udało się zainstalować pakietu")
        return 1
    
    print("\nInstalacja zakończona pomyślnie!")
    
    # Jeśli nie jesteśmy w środowisku wirtualnym, zapytaj o aktywację
    if not in_venv:
        if auto_activate or force:
            print("Automatycznie aktywuję środowisko wirtualne...")
            aktywuj_venv()
        else:
            while True:
                odpowiedź = input("Czy chcesz, abym aktywował środowisko wirtualne w nowym oknie terminala? (tak/nie): ").lower()
                if odpowiedź in ['tak', 't', 'yes', 'y']:
                    aktywuj_venv()
                    break
                elif odpowiedź in ['nie', 'n', 'no']:
                    print("Aby aktywować środowisko wirtualne ręcznie, wykonaj:")
                    if sys.platform == 'win32':
                        print("\t.venv\\Scripts\\activate")
                    else:
                        print("\tsource .venv/bin/activate")
                    break
                else:
                    print("Proszę wpisać 'tak' lub 'nie'")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 