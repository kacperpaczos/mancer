#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from pathlib import Path

def aktywuj_venv():
    """
    Sprawdza czy jesteśmy w środowisku wirtualnym, jeśli nie - próbuje je aktywować
    """
    # Sprawdź czy już jesteśmy w środowisku wirtualnym
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Już jesteśmy w środowisku wirtualnym")
        return True
    
    # Określ ścieżkę do aktywacji venv
    if sys.platform == 'win32':
        activate_script = '.venv\\Scripts\\activate'
        py_cmd = ['.venv\\Scripts\\python']
    else:
        activate_script = '.venv/bin/activate'
        py_cmd = ['.venv/bin/python']
    
    if not os.path.exists(activate_script):
        print(f"Błąd: Nie znaleziono skryptu aktywacji środowiska: {activate_script}")
        print("Czy środowisko deweloperskie zostało zainstalowane? Uruchom najpierw tools/install_dev.py")
        return False
    
    # Uruchom ten sam skrypt w środowisku wirtualnym
    try:
        print("Aktywuję środowisko wirtualne i uruchamiam ponownie...")
        script_path = os.path.abspath(__file__)
        
        # Przekazujemy wszystkie argumenty do nowej instancji skryptu
        script_args = ' '.join(sys.argv[1:])
        
        if sys.platform == 'win32':
            activate_cmd = f"call {activate_script} && python {script_path} {script_args}"
            subprocess.run(["cmd", "/c", activate_cmd], check=True)
        else:
            activate_cmd = f"source {activate_script} && python {script_path} {script_args}"
            subprocess.run(["bash", "-c", activate_cmd], check=True)
        
        # Jeśli dotarliśmy tutaj, to skrypt został uruchomiony w venv, więc możemy zakończyć obecną instancję
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas aktywacji środowiska wirtualnego: {e}")
        return False

def uruchom_mancer():
    """
    Uruchamia aplikację Mancer w wersji deweloperskiej
    """
    print("=== Uruchamianie Mancer (wersja deweloperska) ===")
    
    # Tutaj możesz dodać kod uruchamiający twoją aplikację
    # Na przykład:
    # from mancer import run_app
    # run_app()
    
    # Przykładowy kod tylko do demonstracji
    try:
        print("Sprawdzanie wersji Mancer...")
        python_code = '''
import sys
from mancer import __version__
print(f"Mancer wersja: {__version__}")
'''
        subprocess.run([sys.executable, "-c", python_code], check=True)
        print("\nAplikacja zakończyła działanie pomyślnie")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas uruchamiania aplikacji: {e}")
        return False

def main():
    # Przejdź do katalogu głównego projektu
    os.chdir(Path(__file__).parent.parent)
    
    # Pobierz argumenty wiersza poleceń
    force = False
    for arg in sys.argv[1:]:
        if arg in ['-f', '--force']:
            force = True
            break
    
    # Sprawdź czy jesteśmy w środowisku wirtualnym
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("Nie jesteśmy w środowisku wirtualnym.")
        
        if force:
            print("Automatycznie aktywuję środowisko wirtualne (tryb wymuszony)...")
            aktywuj_venv()
            return 0  # aktywuj_venv zakończy ten proces jeśli się powiedzie
        
        while True:
            odpowiedź = input("Czy chcesz, abym aktywował środowisko wirtualne i uruchomił aplikację? (tak/nie): ").lower()
            if odpowiedź in ['tak', 't', 'yes', 'y']:
                aktywuj_venv()
                return 0  # aktywuj_venv zakończy ten proces jeśli się powiedzie
            elif odpowiedź in ['nie', 'n', 'no']:
                print("Aby aktywować środowisko wirtualne ręcznie, wykonaj:")
                if sys.platform == 'win32':
                    print("\t.venv\\Scripts\\activate")
                else:
                    print("\tsource .venv/bin/activate")
                return 1
            else:
                print("Proszę wpisać 'tak' lub 'nie'")
    
    # Jeśli jesteśmy tutaj, to znaczy że jesteśmy w venv
    if not uruchom_mancer():
        print("Błąd: Nie udało się uruchomić aplikacji")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 