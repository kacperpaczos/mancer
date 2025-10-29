#!/usr/bin/env python3
"""
Przykład demonstrujący użycie nowego systemu logowania w Mancer.

Ten przykład pokazuje:
1. Jak konfigurować i używać MancerLogger
2. Jak logować różne rodzaje komunikatów
3. Jak śledzić dane pipeline'ów komend
4. Jak logować łańcuchy komend
"""

import os
import sys
import time
from pprint import pprint

# Dodaj ścieżkę do katalogu głównego projektu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importuj komponenty Mancer
from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.model.data_format import DataFormat
from src.mancer.domain.service.log_backend_interface import LogLevel
from src.mancer.infrastructure.command.system.df_command import DfCommand
from src.mancer.infrastructure.command.system.grep_command import GrepCommand
from src.mancer.infrastructure.command.system.ls_command import LsCommand
from src.mancer.infrastructure.logging.mancer_logger import MancerLogger


def print_separator(title):
    """Wyświetla separator z tytułem sekcji."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def demo_basic_logging():
    """Demonstracja podstawowego logowania."""
    print_separator("PODSTAWOWE LOGOWANIE")

    # Pobierz singleton instancję loggera
    logger = MancerLogger.get_instance()

    # Ustaw poziom logowania na DEBUG
    logger.initialize(log_level=LogLevel.DEBUG, console_enabled=True)

    # Logowanie na różnych poziomach
    logger.debug("To jest wiadomość debug")
    logger.info("To jest wiadomość informacyjna")
    logger.warning("To jest ostrzeżenie!")
    logger.error("To jest błąd!")
    logger.critical("To jest błąd krytyczny!")

    # Logowanie z kontekstem (dodatkowymi danymi)
    logger.info(
        "Wiadomość z kontekstem",
        {"user": "admin", "action": "login", "timestamp": time.time()},
    )


def demo_command_logging():
    """Demonstracja logowania komend."""
    print_separator("LOGOWANIE KOMEND")

    # Pobierz singleton instancję loggera
    logger = MancerLogger.get_instance()

    # Zaloguj rozpoczęcie i zakończenie wykonania komendy
    command_info = logger.log_command_start(
        command_name="ls",
        command_string="ls -la /tmp",
        context_params={"current_directory": "/home/user", "execution_mode": "local"},
    )

    # Symuluj wykonanie komendy
    print("Wykonywanie komendy ls -la /tmp...")
    time.sleep(1)

    # Zaloguj zakończenie komendy
    logger.log_command_end(
        command_info=command_info,
        success=True,
        exit_code=0,
        output="drwxrwxrwt 15 root root 4096 May 10 12:34 /tmp",
        error=None,
    )

    # Zaloguj błędną komendę
    command_info = logger.log_command_start(
        command_name="nieistniejąca",
        command_string="nieistniejąca_komenda",
        context_params={},
    )

    # Symuluj wykonanie komendy
    print("Próba wykonania nieistniejącej komendy...")
    time.sleep(0.5)

    # Zaloguj błąd
    logger.log_command_end(
        command_info=command_info,
        success=False,
        exit_code=127,
        output="",
        error="command not found: nieistniejąca_komenda",
    )


def demo_pipeline_logging():
    """Demonstracja logowania danych pipeline'ów."""
    print_separator("LOGOWANIE PIPELINE'ÓW")

    # Pobierz singleton instancję loggera
    logger = MancerLogger.get_instance()

    # Logowanie danych wejściowych komendy
    logger.log_command_input(
        command_name="grep",
        data=[
            "line1: important data",
            "line2: unimportant data",
            "line3: important stuff",
        ],
    )

    # Symuluj przetwarzanie
    print("Przetwarzanie danych wejściowych przez grep...")
    time.sleep(0.5)

    # Logowanie danych wyjściowych komendy
    logger.log_command_output(command_name="grep", data=["line1: important data", "line3: important stuff"])

    # Pokaż historię pipeline'ów
    print("\nDane pipeline'ów:")
    pipeline_data = logger.get_pipeline_data()
    pprint(pipeline_data)


def demo_command_chain():
    """Demonstracja logowania łańcuchów komend."""
    print_separator("LOGOWANIE ŁAŃCUCHÓW KOMEND")

    # Utwórz łańcuch komend
    ls_command = LsCommand().with_option("-la")
    grep_command = GrepCommand().with_pattern("py")

    # Utwórz łańcuch: ls -la | grep py
    chain = ls_command.pipe(grep_command)

    # Wykonaj łańcuch (logger zostanie użyty automatycznie)
    context = CommandContext()
    result = chain.execute(context)

    print(f"\nWynik łańcucha komend: {result.success}\n")
    print(f"Dane wyjściowe: {result.raw_output[:150]}{'...' if len(result.raw_output) > 150 else ''}\n")

    # Wyświetl historię wykonania
    print("Historia komend:")
    logger_instance = MancerLogger.get_instance()
    for entry in logger_instance.get_command_history():
        cmd = entry.get("command", {})
        cmd_name = cmd.get("command_name", "unknown")
        cmd_str = cmd.get("command_string", "")
        status = "✓" if entry.get("completed", False) and entry.get("result", {}).get("success", False) else "✗"

        print(f"{status} {cmd_name}: {cmd_str}")


def demo_command_history_export():
    """Demonstracja eksportu historii komend."""
    print_separator("EKSPORT HISTORII KOMEND")

    # Pobierz singleton instancję loggera
    logger = MancerLogger.get_instance()

    # Wykonaj kilka komend, aby wypełnić historię
    context = CommandContext()

    commands = [
        LsCommand().with_option("-la"),
        DfCommand().with_option("-h"),
        GrepCommand().with_pattern("python").with_option("-r"),
    ]

    print("Wykonywanie przykładowych komend...")
    for cmd in commands:
        try:
            result = cmd.execute(context)
            print(f"  ✓ {cmd.build_command()}")
        except Exception as e:
            print(f"  ✗ {cmd.build_command()} - {str(e)}")

    # Eksportuj historię do pliku
    history_file = logger.export_history()
    print(f"\nHistoria komend została wyeksportowana do pliku: {history_file}")

    # Wyświetl podsumowanie historii
    history = logger.get_command_history()
    print(f"\nPodsumowanie historii ({len(history)} komend):")

    success_count = 0
    for entry in history:
        if entry.get("completed", False) and entry.get("result", {}).get("success", False):
            success_count += 1

    print(f"Udanych komend: {success_count}")
    print(f"Nieudanych komend: {len(history) - success_count}")


def demo_custom_backend():
    """Demonstracja używania niestandardowego backendu."""
    print_separator("NIESTANDARDOWY BACKEND")

    # W rzeczywistym przypadku użycia, można by zaimplementować własny backend
    # Tutaj symulujemy zmianę konfiguracji istniejącego backendu

    # Pobierz singleton instancję loggera
    logger = MancerLogger.get_instance()

    # Zmień konfigurację istniejącego backendu
    logger.initialize(
        log_level=LogLevel.INFO,
        log_format="[%(levelname)s] %(message)s",  # Prostszy format
        console_enabled=True,
        file_enabled=True,  # Włącz logowanie do pliku
        log_file="custom_log.log",
    )

    print("Logger z niestandardową konfiguracją:")
    logger.info("To jest testowa wiadomość z niestandardową konfiguracją")
    print(f"Logi są zapisywane do pliku: {os.path.join(os.getcwd(), 'logs', 'custom_log.log')}")


def main():
    """Funkcja główna demonstrująca różne aspekty nowego systemu logowania."""
    # Oczyść ekran i wyświetl tytuł
    print("\n" + "*" * 80)
    print("*" + " DEMONSTRACJA NOWEGO SYSTEMU LOGOWANIA MANCER ".center(78) + "*")
    print("*" * 80 + "\n")

    # Uruchom demonstracje
    demo_basic_logging()
    demo_command_logging()
    demo_pipeline_logging()
    demo_command_chain()
    demo_command_history_export()
    demo_custom_backend()

    print("\n" + "=" * 80)
    print(" KONIEC DEMONSTRACJI ".center(80, "="))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
