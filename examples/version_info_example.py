#!/usr/bin/env python3
"""
Przykład użycia modułu informacji o wersji pakietu Mancer.

Demonstruje, jak uzyskać dostęp do informacji o wersji zainstalowanego pakietu Mancer.
"""

import os
import sys
import logging

# Dodaj ścieżkę projektu do PYTHONPATH
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Import klasy VersionInfo bezpośrednio z modułu
from src.mancer.domain.model.version_info import VersionInfo

def demonstrate_version_info():
    """Demonstruje dostęp do informacji o wersji pakietu Mancer."""
    print("Demonstracja dostępu do informacji o wersji pakietu Mancer:")
    
    # Pobierz informacje o wersji
    version_info = VersionInfo.get_mancer_version()
    
    # Wyświetl podstawowe informacje
    print(f"- Nazwa pakietu: {version_info.name}")
    print(f"- Wersja: {version_info.version}")
    print(f"- Opis: {version_info.summary}")
    
    # Sprawdź, czy to wersja deweloperska
    if version_info.is_dev_version:
        print("- To jest wersja deweloperska")
    else:
        print("- To jest wersja produkcyjna")
    
    # Dodatkowe informacje o autorze, jeśli dostępne
    if version_info.author:
        print(f"- Autor: {version_info.author}")
    if version_info.author_email:
        print(f"- Email autora: {version_info.author_email}")
    
    # Sprawdź, czy możemy uzyskać dostęp przez zmienną __version__
    try:
        import mancer
        print(f"- Wersja z __version__: {mancer.__version__}")
    except (ImportError, AttributeError):
        print("- Zmienna __version__ niedostępna - pakiet nie jest zainstalowany")

def main():
    """Główna funkcja wykonująca wszystkie przykłady."""
    print("Mancer Framework - Przykład informacji o wersji")
    
    demonstrate_version_info()
    
    print("\nPrzykład zakończony pomyślnie")

if __name__ == "__main__":
    main() 