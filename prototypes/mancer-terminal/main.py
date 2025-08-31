#!/usr/bin/env python3
"""
Mancer Terminal - Główny plik uruchamiający
Terminal-based interface dla frameworka Mancer
"""

import os
import sys
from pathlib import Path

# Dodaj ścieżkę do src/mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from cli.main import MancerCLI, main
except ImportError:
    print(
        "Błąd importu modułów CLI. Upewnij się, że wszystkie zależności są zainstalowane."
    )
    sys.exit(1)


def run_terminal():
    """Uruchamia Mancer Terminal"""
    try:
        # Sprawdź czy są argumenty wiersza poleceń
        if len(sys.argv) > 1:
            # Tryb komend
            main()
        else:
            # Tryb interaktywny
            cli = MancerCLI()
            cli.run()

    except KeyboardInterrupt:
        print("\n[yellow]Zamykanie Mancer Terminal...[/yellow]")
    except Exception as e:
        print(f"\n[red]Błąd uruchomienia: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    run_terminal()
