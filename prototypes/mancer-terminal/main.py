#!/usr/bin/env python3
"""
Mancer Terminal - SSH Terminal Emulator
Główny plik aplikacji PyQt
"""

import os
import sys
from pathlib import Path

# Dodaj ścieżkę do Mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from gui.main_window import MancerTerminalWindow
    from PyQt6.QtWidgets import QApplication
except ImportError as e:
    print(f"Błąd importu: {e}")
    print("Upewnij się, że PyQt6 jest zainstalowane: pip install PyQt6")
    sys.exit(1)


def setup_logging():
    """Konfiguruje logowanie Mancera do pliku"""
    try:
        from mancer.infrastructure.logging.mancer_logger import MancerLogger

        # Pobierz instancję loggera
        logger = MancerLogger.get_instance()

        # Konfiguruj logowanie do pliku
        logs_dir = Path(__file__).parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        logger.initialize(
            log_level="info",
            log_format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            log_dir=str(logs_dir),
            log_file="mancer_terminal.log",
            console_enabled=True,  # Również do konsoli
            file_enabled=True,  # I do pliku
            force_standard=True,  # Użyj standardowego backendu
        )

        logger.info("Mancer Terminal - logowanie skonfigurowane")
        return logger

    except Exception as e:
        print(f"Błąd konfiguracji logowania: {e}")
        return None


def main():
    """Główna funkcja aplikacji"""
    # Konfiguruj logowanie przed uruchomieniem GUI
    logger = setup_logging()

    app = QApplication(sys.argv)

    # Ustawienia aplikacji
    app.setApplicationName("Mancer Terminal")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Mancer")

    try:
        if logger:
            logger.info("Uruchamiam Mancer Terminal")

        # Stwórz główne okno
        window = MancerTerminalWindow()
        window.show()

        if logger:
            logger.info("Główne okno utworzone i wyświetlone")

        # Uruchom aplikację
        sys.exit(app.exec())

    except Exception as e:
        error_msg = f"Błąd aplikacji: {e}"
        print(error_msg)
        if logger:
            logger.error(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
