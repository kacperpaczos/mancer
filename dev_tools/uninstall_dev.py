#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
from pathlib import Path

def deaktywuj_venv():
    """
    Wyświetla instrukcje jak deaktywować środowisko ręcznie, 
    ponieważ automatyczna deaktywacja nie jest możliwa z poziomu skryptu
    """
    print("\nDeaktywacja środowiska wirtualnego nie może być wykonana automatycznie z poziomu skryptu.")
    print("Proszę wykonać następujące kroki:")
    print("1. Wpisz 'deactivate' w terminalu, aby deaktywować środowisko.")
    print("2. Uruchom ten skrypt ponownie po deaktywacji z flagą --ignore-venv")
    print("   np. ./tools/uninstall_dev.py --ignore-venv")
    return False

def reset_venv_env_vars():
    """
    Resetuje zmienne środowiskowe związane z virtualenv
    """
    for var in ['VIRTUAL_ENV', 'PYTHONHOME']:
        if var in os.environ:
            del os.environ[var]
    
    # Resetuj PATH, usuwając ścieżkę do bin venv
    if 'PATH' in os.environ:
        path_parts = os.environ['PATH'].split(os.pathsep)
        new_path_parts = [p for p in path_parts if '.venv' not in p]
        os.environ['PATH'] = os.pathsep.join(new_path_parts)
    
    return True

def usuń_venv():
    """
    Usuwa środowisko wirtualne Python
    """
    venv_path = Path('.venv')
    
    if not venv_path.exists():
        print("Środowisko wirtualne nie istnieje, nic do usunięcia")
        return True
    
    print(f"Usuwanie środowiska wirtualnego z {venv_path}")
    try:
        shutil.rmtree(venv_path)
        print("Środowisko wirtualne zostało usunięte pomyślnie")
        return True
    except Exception as e:
        print(f"Błąd podczas usuwania środowiska wirtualnego: {e}")
        return False

def usuń_pliki_instalacyjne():
    """
    Usuwa pliki generowane podczas instalacji pakietu
    """
    try:
        # Usuń pliki .egg-info jeśli istnieją
        egg_info_dir = Path('src/mancer.egg-info')
        if egg_info_dir.exists():
            print(f"Usuwanie {egg_info_dir}")
            shutil.rmtree(egg_info_dir)
        
        # Usuń pliki __pycache__ w całym projekcie
        pycache_dirs = list(Path('.').glob('**/__pycache__'))
        for pycache in pycache_dirs:
            print(f"Usuwanie {pycache}")
            shutil.rmtree(pycache)
        
        # Usuń pliki .pyc w całym projekcie
        pyc_files = list(Path('.').glob('**/*.pyc'))
        for pyc_file in pyc_files:
            print(f"Usuwanie {pyc_file}")
            pyc_file.unlink()
        
        print("Wszystkie pliki instalacyjne zostały usunięte pomyślnie")
        return True
    except Exception as e:
        print(f"Błąd podczas usuwania plików instalacyjnych: {e}")
        return False

def usuń_build():
    """
    Usuwa katalogi build i dist, jeśli istnieją
    """
    try:
        for dir_name in ['build', 'dist']:
            dir_path = Path(dir_name)
            if dir_path.exists():
                print(f"Usuwanie katalogu {dir_path}")
                shutil.rmtree(dir_path)
        
        return True
    except Exception as e:
        print(f"Błąd podczas usuwania katalogów build/dist: {e}")
        return False

def potwierdź_usunięcie():
    """
    Prosi użytkownika o potwierdzenie usunięcia środowiska deweloperskiego
    """
    print("UWAGA: Zamierzasz usunąć środowisko deweloperskie Mancer.")
    print("To spowoduje usunięcie:")
    print("  - Wirtualnego środowiska Python (.venv)")
    print("  - Plików instalacyjnych (*.egg-info, __pycache__, itp.)")
    print("  - Katalogów build i dist (jeśli istnieją)")
    print("\nTwój kod źródłowy i pliki projektu NIE zostaną usunięte.\n")
    
    while True:
        odpowiedź = input("Czy na pewno chcesz kontynuować? (tak/nie): ").lower()
        if odpowiedź in ['tak', 't', 'yes', 'y']:
            return True
        elif odpowiedź in ['nie', 'n', 'no']:
            return False
        else:
            print("Proszę wpisać 'tak' lub 'nie'")

def main():
    print("=== Usuwanie środowiska deweloperskiego Mancer ===")
    
    # Przejdź do katalogu głównego projektu
    os.chdir(Path(__file__).parent.parent)
    
    # Pobierz argumenty wiersza poleceń
    force = False
    ignore_venv = False
    
    for arg in sys.argv[1:]:
        if arg in ['-f', '--force']:
            force = True
        elif arg in ['--ignore-venv']:
            ignore_venv = True
    
    if force:
        print("Tryb wymuszony - pomijam potwierdzenia")
    
    if ignore_venv:
        print("Ignoruję wykrywanie środowiska wirtualnego")
        reset_venv_env_vars()
    
    # Sprawdź czy jesteśmy w środowisku wirtualnym (tylko jeśli nie ignorujemy)
    if not ignore_venv:
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        if 'VIRTUAL_ENV' in os.environ:
            in_venv = True
        
        if in_venv:
            print("Wykryto aktywne środowisko wirtualne.")
            print("Nie można usunąć aktywnego środowiska.")
            deaktywuj_venv()
            return 1
    
    # Poproś o potwierdzenie (chyba że force=True)
    if not force and not potwierdź_usunięcie():
        print("Anulowano usuwanie środowiska deweloperskiego")
        return 0
    
    # Usuń środowisko wirtualne
    usuń_venv()
    
    # Usuń pliki instalacyjne
    usuń_pliki_instalacyjne()
    
    # Usuń katalogi build i dist
    usuń_build()
    
    print("\nŚrodowisko deweloperskie zostało pomyślnie usunięte!")
    print("Aby ponownie zainstalować środowisko, uruchom: ./tools/install_dev.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 