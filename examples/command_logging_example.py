#!/usr/bin/env python3
"""
Przykład wykorzystania uniwersalnego podsystemu logowania komend w Mancer.

Ten przykład pokazuje:
1. Konfigurację systemu logowania z różnymi opcjami
2. Wykonywanie komend w różnych kontekstach i ich logowanie
3. Zaawansowane filtrowanie i analiza logów
4. Integracja z własnymi komendami
"""

import logging
import os
import sys
import time
from typing import Any, Dict, List

# Dodanie ścieżki do modułów Mancer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modułów Mancer
from src.mancer.application.shell_runner import ShellRunner
from src.mancer.domain.model.command_context import CommandContext
from src.mancer.domain.service.command_logger_service import CommandLoggerService
from src.mancer.infrastructure.command.base_command import BaseCommand
from src.mancer.infrastructure.command.system.cat_command import CatCommand
from src.mancer.infrastructure.command.system.df_command import DfCommand
from src.mancer.infrastructure.command.system.grep_command import GrepCommand
from src.mancer.infrastructure.command.system.ls_command import LsCommand
from src.mancer.infrastructure.command.system.ps_command import PsCommand

# Konfiguracja podstawowego loggera dla skryptu
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


# Tworzenie własnej komendy dla demonstracji
class MojaKomenda(BaseCommand):
    """Przykładowa własna komenda"""

    def __init__(self, nazwa: str = "moja-komenda"):
        super().__init__(nazwa)

    def execute(self, context: CommandContext, input_result=None):
        """Implementacja metody execute"""
        # Budowanie komendy
        command_str = self.build_command()

        # Pobieranie backendu
        backend = self._get_backend(context)

        # Własna logika komendy
        logger.info(f"Wykonuję własną komendę: {command_str}")

        # Symulacja wykonania (w prawdziwym przypadku użylibyśmy backendu)
        exit_code = 0
        output = f"Wynik mojej komendy: {' '.join(self._args)}"
        error = ""

        # Tworzenie wyniku
        return self._prepare_result(
            raw_output=output,
            success=exit_code == 0,
            exit_code=exit_code,
            error_message=error,
        )


def demonstracja_podstawowa():
    """Demonstracja podstawowych funkcji loggera"""
    logger.info("=== Demonstracja podstawowego użycia loggera ===")

    # Inicjalizacja CommandLoggerService
    command_logger = CommandLoggerService.get_instance()
    command_logger.initialize(
        log_level="info",  # Poziom logowania
        log_dir="logs",  # Katalog logów
        log_file="mancer_demo.log",  # Nazwa pliku logu
        console_enabled=True,  # Logowanie na konsolę
        file_enabled=True,  # Logowanie do pliku
    )

    # Utworzenie ShellRunner
    runner = ShellRunner(
        enable_command_logging=True,  # Włączenie logowania
        log_to_file=True,  # Zapisywanie do pliku
        log_level="info",  # Poziom logowania
    )

    # Wykonanie kilku komend
    logger.info("Wykonywanie podstawowych komend systemowych...")

    # Komenda ls
    ls_cmd = LsCommand().with_option("-la")
    ls_wynik = runner.execute(ls_cmd)
    print(f"Wynik ls: {len(ls_wynik.structured_output)} plików/katalogów")

    # Komenda df
    df_cmd = DfCommand().with_option("-h")
    df_wynik = runner.execute(df_cmd)
    print(f"Wynik df: {len(df_wynik.structured_output)} systemów plików")

    # Własna komenda
    moja_cmd = MojaKomenda("testowa").add_arg("parametr1").add_arg("--opcja")
    moja_wynik = runner.execute(moja_cmd)
    print(f"Wynik własnej komendy: {moja_wynik.raw_output}")

    # Pobranie historii
    historia = command_logger.get_command_history()
    print(f"\nWykonano {len(historia)} komend.")


def demonstracja_zaawansowana():
    """Demonstracja zaawansowanych funkcji loggera"""
    logger.info("=== Demonstracja zaawansowanego użycia loggera ===")

    # Konfiguracja debugowania
    command_logger = CommandLoggerService.get_instance()
    command_logger.initialize(
        log_level="debug",  # Więcej szczegółów
        file_enabled=True,
        console_enabled=True,
    )

    # Utworzenie ShellRunner z debugowaniem
    runner = ShellRunner(
        enable_command_logging=True,
        log_level="debug",  # Poziom debug
    )

    # Wykonanie komend z różnymi parametrami
    komendy = [
        GrepCommand().with_param("pattern", "test").with_option("-i"),
        CatCommand().add_arg("/etc/hostname"),
        LsCommand().with_option("-la").add_arg("/tmp"),
        MojaKomenda("analiza").add_arg("--format=json").add_arg("--verbose"),
    ]

    # Wykonujemy komendy i mierzymy czas
    logger.info("Wykonywanie sekwencji komend z debugowaniem...")
    for i, cmd in enumerate(komendy, 1):
        start = time.time()
        wynik = runner.execute(cmd)
        czas = time.time() - start

        print(
            f"Komenda {i}: {cmd.name} - Status: {'OK' if wynik.success else 'BŁĄD'} (czas: {czas:.3f}s)"
        )

    # Pobieranie historii tylko udanych komend
    udane = command_logger.get_command_history(success_only=True)
    print(f"\nUdanych komend: {len(udane)} z {len(komendy)}")

    # Eksport logów do pliku
    sciezka = command_logger.export_history()
    print(f"Historia komend wyeksportowana do: {sciezka}")


def analiza_logów():
    """Demonstracja analizy zapisanych logów"""
    logger.info("=== Analiza zapisanych logów ===")

    # Pobieranie historii
    command_logger = CommandLoggerService.get_instance()
    historia = command_logger.get_command_history()

    if not historia:
        print("Brak historii komend do analizy")
        return

    # Statystyki
    liczba_komend = len(historia)
    udane_komendy = sum(
        1
        for entry in historia
        if entry.get("completed", False) and entry.get("result", {}).get("success", False)
    )

    błędne_komendy = liczba_komend - udane_komendy

    # Średni czas wykonania
    czasy = [
        entry.get("result", {}).get("execution_time", 0) for entry in historia if "result" in entry
    ]
    średni_czas = sum(czasy) / len(czasy) if czasy else 0

    # Wypisanie statystyk
    print("\nStatystyki wykonania komend:")
    print(f"Liczba wykonanych komend: {liczba_komend}")
    print(f"Udane komendy: {udane_komendy} ({(udane_komendy/liczba_komend*100):.1f}%)")
    print(f"Błędne komendy: {błędne_komendy} ({(błędne_komendy/liczba_komend*100):.1f}%)")
    print(f"Średni czas wykonania: {średni_czas:.3f}s")

    # Najdłużej wykonujące się komendy
    if czasy:
        posortowane = sorted(
            [
                (
                    entry.get("command", {}).get("command_name", ""),
                    entry.get("result", {}).get("execution_time", 0),
                )
                for entry in historia
                if "result" in entry
            ],
            key=lambda x: x[1],
            reverse=True,
        )

        print("\nNajdłużej wykonujące się komendy:")
        for nazwa, czas in posortowane[:3]:
            print(f"  {nazwa}: {czas:.3f}s")


def główna_funkcja():
    """Główna funkcja przykładu"""
    logger.info("Rozpoczynam demonstrację systemu logowania komend Mancer")

    try:
        # Część 1: Podstawowe użycie
        demonstracja_podstawowa()

        # Część 2: Zaawansowane funkcje
        demonstracja_zaawansowana()

        # Część 3: Analiza logów
        analiza_logów()

        logger.info("Demonstracja zakończona pomyślnie")
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas demonstracji: {e}")
    finally:
        # Czyszczenie po demonstracji
        logger.info("Sprzątanie po demonstracji...")


if __name__ == "__main__":
    główna_funkcja()
