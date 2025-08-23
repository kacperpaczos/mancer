"""
Mancer Terminal CLI - Główna klasa interfejsu wiersza poleceń
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text


class MancerCLI:
    """Główna klasa Mancer Terminal Emulator"""

    def __init__(self):
        self.console = Console()
        self.config = {}
        self.ssh_sessions = {}
        self.current_session = None

    def run(self, args: Optional[List[str]] = None):
        """Uruchamia CLI"""
        try:
            if args:
                self._parse_and_execute(args)
            else:
                self._interactive_mode()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Zamykanie Mancer Terminal...[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]Błąd krytyczny: {e}[/red]")
            sys.exit(1)

    def _parse_and_execute(self, args: List[str]):
        """Parsuje i wykonuje komendy"""
        if not args:
            return

        command = args[0]
        arguments = args[1:] if len(args) > 1 else []

        try:
            if command == "terminal":
                self._handle_terminal_command(arguments)
            elif command == "connect":
                self._handle_connect_command(arguments)
            elif command == "sessions":
                self._handle_sessions_command(arguments)
            elif command == "config":
                self._handle_config_command(arguments)
            elif command == "help":
                self._show_help()
            else:
                self.console.print(f"[red]Nieznana komenda: {command}[/red]")
                self._show_help()

        except Exception as e:
            self.console.print(f"[red]Błąd wykonania komendy: {e}[/red]")

    def _handle_terminal_command(self, arguments: List[str]):
        """Obsługuje komendy terminala"""
        if not arguments:
            self.console.print("[yellow]Użycie: mancer terminal <action>[/yellow]")
            return

        action = arguments[0]

        if action == "connect":
            self._handle_connect_command(arguments[1:])
        elif action == "sessions":
            self._handle_sessions_command(arguments[1:])
        else:
            self.console.print(f"[red]Nieznana akcja terminala: {action}[/red]")

    def _handle_connect_command(self, arguments: List[str]):
        """Obsługuje połączenia SSH"""
        if not arguments:
            self.console.print("[yellow]Użycie: mancer connect <server>[/yellow]")
            return

        server = arguments[0]
        self.console.print(f"[green]Łączę z serwerem: {server}[/green]")
        # TODO: Implementacja połączenia SSH

    def _handle_sessions_command(self, arguments: List[str]):
        """Obsługuje zarządzanie sesjami"""
        if not arguments:
            self._show_sessions()
            return

        action = arguments[0]

        if action == "list":
            self._show_sessions()
        elif action == "switch":
            session_id = arguments[1] if len(arguments) > 1 else None
            self._switch_session(session_id)
        else:
            self.console.print(f"[red]Nieznana akcja sesji: {action}[/red]")

    def _handle_config_command(self, arguments: List[str]):
        """Obsługuje komendy konfiguracji"""
        if not arguments:
            self._show_config()
            return

        action = arguments[0]

        if action == "show":
            self._show_config()
        elif action == "edit":
            self._edit_config()
        else:
            self.console.print(f"[red]Nieznana akcja konfiguracji: {action}[/red]")

    def _show_config(self):
        """Wyświetla aktualną konfigurację"""
        config_table = Table(title="Konfiguracja Mancer")
        config_table.add_column("Klucz", style="cyan")
        config_table.add_column("Wartość", style="green")

        config_table.add_row("Backend", "SSH + Local")
        config_table.add_row("Log Level", "INFO")
        config_table.add_row("Timeout", "30s")
        config_table.add_row("Retry Attempts", "3")

        self.console.print(config_table)

    def _edit_config(self):
        """Edycja konfiguracji"""
        self.console.print("[yellow]Edycja konfiguracji - funkcja w trakcie implementacji[/yellow]")

    def _interactive_mode(self):
        """Tryb interaktywny"""
        self.console.print(
            Panel(
                "[bold blue]MANCER TERMINAL - TRYB INTERAKTYWNY[/bold blue]\n\n"
                "1. [green]Zarządzanie systemd[/green]\n"
                "2. [yellow]Operacje SSH[/yellow]\n"
                "3. [cyan]Konfiguracja[/cyan]\n"
                "4. [magenta]Monitoring[/magenta]\n"
                "5. [red]Wyjście[/red]",
                title="[bold white]Mancer Terminal[/bold white]",
                border_style="blue",
            )
        )

        while True:
            try:
                choice = Prompt.ask("Wybierz opcję", choices=["1", "2", "3", "4", "5"])

                if choice == "1":
                    self._interactive_systemd()
                elif choice == "2":
                    self._interactive_ssh()
                elif choice == "3":
                    self._interactive_config()
                elif choice == "4":
                    self._interactive_monitoring()
                elif choice == "5":
                    if Confirm.ask("Czy na pewno chcesz wyjść?"):
                        break

            except KeyboardInterrupt:
                break

    def _interactive_systemd(self):
        """Interaktywne zarządzanie systemd"""
        self.console.print("[bold green]Zarządzanie systemd[/bold green]")
        # TODO: Implementacja interaktywnego zarządzania systemd

    def _interactive_ssh(self):
        """Interaktywne operacje SSH"""
        self.console.print("[bold yellow]Operacje SSH[/bold yellow]")
        # TODO: Implementacja interaktywnych operacji SSH

    def _interactive_config(self):
        """Interaktywna konfiguracja"""
        self.console.print("[bold cyan]Konfiguracja[/bold cyan]")
        # TODO: Implementacja interaktywnej konfiguracji

    def _interactive_monitoring(self):
        """Interaktywny monitoring"""
        self.console.print("[bold magenta]Monitoring[/bold magenta]")
        # TODO: Implementacja interaktywnego monitoringu

    def _show_help(self):
        """Wyświetla pomoc"""
        help_text = """
[bold blue]MANCER TERMINAL - POMOC[/bold blue]

[green]Podstawowe komendy:[/green]
  mancer systemd <action> <service>  - Zarządzanie systemd
  mancer ssh <action> <server>       - Operacje SSH
  mancer config <action>              - Zarządzanie konfiguracją
  mancer interactive                  - Tryb interaktywny
  mancer help                         - Wyświetla pomoc

[green]Przykłady:[/green]
  mancer systemd status nginx
  mancer ssh connect server-01
  mancer config show
  mancer interactive

[green]Akcje systemd:[/green]
  status, start, stop, restart, enable, disable

[green]Akcje SSH:[/green]
  connect, disconnect, execute, upload, download

[green]Akcje konfiguracji:[/green]
  show, edit, reload, validate
        """

        self.console.print(
            Panel(
                help_text,
                title="[bold white]Pomoc Mancer Terminal[/bold white]",
                border_style="blue",
            )
        )


def main():
    """Główna funkcja CLI"""
    cli = MancerCLI()
    cli.run(sys.argv[1:] if len(sys.argv) > 1 else None)


if __name__ == "__main__":
    main()
