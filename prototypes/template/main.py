#!/usr/bin/env python3
"""
Prototyp: Nazwa Prototypu

Ten prototyp demonstruje użycie frameworka Mancer do [cel].
"""

import sys
from pathlib import Path

# Dodaj ścieżkę do frameworka (dla trybu develop)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mancer.application.command_manager import CommandManager
from mancer.infrastructure.backend.bash_backend import BashBackend
from mancer.domain.model.command_result import CommandResult


class PrototypeApp:
    """Główna klasa prototypu używająca frameworka Mancer."""
    
    def __init__(self):
        self.command_manager = CommandManager()
        self.backend = BashBackend()
        
    def run(self):
        """Główna logika prototypu."""
        print("🚀 Uruchamianie prototypu z frameworkiem Mancer...")
        
        # Przykład użycia frameworka
        try:
            # Wykonaj komendę systemową
            result = self.backend.execute("hostname")
            print(f"Hostname: {result.output}")
            
            # Użyj command manager
            # self.command_manager.execute_command(...)
            
        except Exception as e:
            print(f"Błąd: {e}")
            return False
            
        return True


def main():
    """Główna funkcja."""
    app = PrototypeApp()
    success = app.run()
    
    if success:
        print("✅ Prototyp zakończony pomyślnie")
    else:
        print("❌ Prototyp zakończony z błędami")
        sys.exit(1)


if __name__ == "__main__":
    main()
