#!/usr/bin/env python3
"""
Mancer Systemd Prototype - Zaawansowany TUI do zarządzania systemd
Integruje funkcje z istniejących projektów oraz nowoczesne narzędzia TUI
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Dodaj ścieżkę do src/mancer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from rich import box
    from rich.align import Align
    from rich.columns import Columns
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
except ImportError as e:
    print(f"Błąd importu Rich: {e}")
    print("Zainstaluj: pip install rich")
    sys.exit(1)

try:
    from mancer.domain.service.systemd_service import SystemdService
    from mancer.domain.shared.profile_producer import ProfileProducer
    from mancer.infrastructure.backend.ssh_backend import SSHBackend
    from mancer.infrastructure.logging.mancer_logger import MancerLogger
except ImportError as e:
    print(f"Błąd importu Mancer: {e}")
    print("Upewnij się, że framework Mancer jest dostępny")
    sys.exit(1)


class SystemdTUI:
    """Główna klasa interfejsu TUI do zarządzania systemd"""

    def __init__(self):
        self.console = Console()
        self.logger = MancerLogger()
        self.profile_producer = ProfileProducer()
        self.systemd_service = SystemdService(self.profile_producer)
        self.current_server = None
        self.current_view = "main"
        self.units_data = {}
        self.filtered_units = []

    def run(self):
        """Główna pętla aplikacji"""
        try:
            self.show_welcome()
            self.main_menu()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Zamykanie aplikacji...[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Błąd krytyczny: {e}[/red]")
            self.logger.error(f"Błąd krytyczny w TUI: {e}")

    def show_welcome(self):
        """Wyświetla ekran powitalny"""
        welcome_text = Text("🚀 MANCER SYSTEMD PROTOTYPE", style="bold blue")
        subtitle = Text("Zaawansowany TUI do zarządzania systemd", style="italic green")

        panel = Panel(
            Align.center(Columns([welcome_text, subtitle], align="center"), vertical="middle"),
            title="[bold white]Witaj w Mancer Systemd Prototype[/bold white]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)
        self.console.print()

    def main_menu(self):
        """Główne menu aplikacji"""
        while True:
            self.console.clear()
            self.console.print(
                Panel(
                    "[bold blue]GŁÓWNE MENU[/bold blue]\n\n"
                    "1. [green]Zarządzanie serwerami[/green]\n"
                    "2. [yellow]Przegląd jednostek systemd[/yellow]\n"
                    "3. [cyan]Zarządzanie usługami[/cyan]\n"
                    "4. [magenta]Konfiguracja systemd[/magenta]\n"
                    "5. [blue]Logi i monitoring[/blue]\n"
                    "6. [red]Wyjście[/red]",
                    title="[bold white]Mancer Systemd Prototype[/bold white]",
                    border_style="blue",
                )
            )

            choice = Prompt.ask("Wybierz opcję", choices=["1", "2", "3", "4", "5", "6"])

            if choice == "1":
                self.server_management()
            elif choice == "2":
                self.units_overview()
            elif choice == "3":
                self.service_management()
            elif choice == "4":
                self.systemd_config()
            elif choice == "5":
                self.logs_monitoring()
            elif choice == "6":
                if Confirm.ask("Czy na pewno chcesz wyjść?"):
                    break

    def server_management(self):
        """Zarządzanie serwerami"""
        self.console.print("[bold green]Zarządzanie serwerami[/bold green]")
        # TODO: Implementacja zarządzania serwerami
        self.console.print("Funkcja w trakcie implementacji...")
        input("Naciśnij Enter, aby wrócić...")

    def units_overview(self):
        """Przegląd jednostek systemd"""
        self.console.print("[bold yellow]Przegląd jednostek systemd[/bold yellow]")
        # TODO: Implementacja przeglądu jednostek
        self.console.print("Funkcja w trakcie implementacji...")
        input("Naciśnij Enter, aby wrócić...")

    def service_management(self):
        """Zarządzanie usługami"""
        self.console.print("[bold cyan]Zarządzanie usługami[/bold cyan]")
        # TODO: Implementacja zarządzania usługami
        self.console.print("Funkcja w trakcie implementacji...")
        input("Naciśnij Enter, aby wrócić...")

    def systemd_config(self):
        """Konfiguracja systemd"""
        self.console.print("[bold magenta]Konfiguracja systemd[/bold magenta]")
        # TODO: Implementacja konfiguracji systemd
        self.console.print("Funkcja w trakcie implementacji...")
        input("Naciśnij Enter, aby wrócić...")

    def logs_monitoring(self):
        """Logi i monitoring"""
        self.console.print("[bold blue]Logi i monitoring[/bold blue]")
        # TODO: Implementacja logów i monitoringu
        self.console.print("Funkcja w trakcie implementacji...")
        input("Naciśnij Enter, aby wrócić...")


def main():
    """Główna funkcja aplikacji"""
    try:
        app = SystemdTUI()
        app.run()
    except Exception as e:
        console = Console()
        console.print(f"[red]Błąd uruchomienia aplikacji: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
