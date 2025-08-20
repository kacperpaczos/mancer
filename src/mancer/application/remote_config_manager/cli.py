#!/usr/bin/env python3
"""
Moduł implementujący interfejs wiersza poleceń dla RemoteConfigManager.
"""
import argparse
import getpass
import sys
from typing import List, Optional

from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .manager import RemoteConfigManager


class CLI:
    """
    Klasa implementująca interfejs wiersza poleceń dla RemoteConfigManager.
    """
    
    def __init__(self):
        """
        Inicjalizuje interfejs wiersza poleceń.
        """
        self.console = Console()
        self.manager = RemoteConfigManager()

    def print_header(self, title: str) -> None:
        """
        Wyświetla nagłówek.
        
        Args:
            title: Tytuł nagłówka
        """
        self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
        self.console.print("=" * len(title), style="cyan")

    def print_success(self, message: str) -> None:
        """
        Wyświetla komunikat sukcesu.
        
        Args:
            message: Komunikat
        """
        rprint(f"[bold green]✓[/bold green] {message}")

    def print_error(self, message: str) -> None:
        """
        Wyświetla komunikat błędu.
        
        Args:
            message: Komunikat
        """
        rprint(f"[bold red]✗[/bold red] {message}")

    def print_warning(self, message: str) -> None:
        """
        Wyświetla ostrzeżenie.
        
        Args:
            message: Komunikat
        """
        rprint(f"[bold yellow]![/bold yellow] {message}")

    def print_info(self, message: str) -> None:
        """
        Wyświetla informację.
        
        Args:
            message: Komunikat
        """
        rprint(f"[bold blue]i[/bold blue] {message}")

    def create_parser(self) -> argparse.ArgumentParser:
        """
        Tworzy parser argumentów wiersza poleceń.
        
        Returns:
            Parser argumentów
        """
        parser = argparse.ArgumentParser(
            prog="remote-config-manager",
            description="Narzędzie do zarządzania konfiguracjami na zdalnych serwerach"
        )
        
        # Utwórz podpolecenia
        subparsers = parser.add_subparsers(dest="command", help="Polecenie do wykonania")
        
        # Polecenie connect - połącz z serwerem
        connect_parser = subparsers.add_parser("connect", help="Połącz z serwerem")
        connect_parser.add_argument("-p", "--profile", help="Nazwa profilu do użycia")
        
        # Polecenie backup - utwórz kopię zapasową plików
        backup_parser = subparsers.add_parser("backup", help="Utwórz kopię zapasową plików")
        
        # Polecenie diff - pokaż różnice między plikami
        diff_parser = subparsers.add_parser("diff", help="Pokaż różnice między plikami")
        
        # Polecenie update - aktualizuj pliki na serwerze
        update_parser = subparsers.add_parser("update", help="Aktualizuj pliki na serwerze")
        
        # Polecenie profile - zarządzaj profilami
        profile_parser = subparsers.add_parser("profile", help="Zarządzaj profilami")
        profile_subparsers = profile_parser.add_subparsers(dest="profile_command", help="Operacja na profilach")
        
        # Polecenie profile add - dodaj profil
        profile_add_parser = profile_subparsers.add_parser("add", help="Dodaj nowy profil")
        profile_add_parser.add_argument("name", help="Nazwa profilu")
        profile_add_parser.add_argument("-H", "--host", help="Adres hosta", required=True)
        profile_add_parser.add_argument("-u", "--user", help="Nazwa użytkownika", required=True)
        profile_add_parser.add_argument("-d", "--dir", help="Katalog aplikacji", required=True)
        profile_add_parser.add_argument("-s", "--services", help="Usługi do restartowania (oddzielone przecinkami)", required=True)
        
        # Polecenie profile list - wyświetl listę profili
        profile_list_parser = profile_subparsers.add_parser("list", help="Wyświetl listę profili")
        
        # Polecenie profile remove - usuń profil
        profile_remove_parser = profile_subparsers.add_parser("remove", help="Usuń profil")
        profile_remove_parser.add_argument("name", help="Nazwa profilu")
        
        # Polecenie profile activate - aktywuj profil
        profile_activate_parser = profile_subparsers.add_parser("activate", help="Aktywuj profil")
        profile_activate_parser.add_argument("name", help="Nazwa profilu")
        
        return parser

    def connect_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie connect.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header("Łączenie z serwerem")
        
        # Jeśli podano profil, użyj go
        if args.profile:
            if not self.manager.set_active_profile(args.profile):
                self.print_error(f"Profil '{args.profile}' nie istnieje")
                return 1
            self.print_info(f"Używam profilu '{args.profile}'")
            
        # Jeśli nie ma aktywnego profilu, wybierz z listy
        if not self.manager.active_profile:
            profiles = self.manager.list_profiles()
            if not profiles:
                self.print_error("Brak zapisanych profili. Użyj 'profile add', aby dodać profil")
                return 1
                
            self.console.print("Dostępne profile:")
            for i, profile in enumerate(profiles, 1):
                self.console.print(f"{i}. {profile}")
                
            choice = Prompt.ask("Wybierz numer profilu", choices=[str(i) for i in range(1, len(profiles) + 1)])
            profile_name = profiles[int(choice) - 1]
            
            if not self.manager.set_active_profile(profile_name):
                self.print_error(f"Nie można ustawić profilu '{profile_name}'")
                return 1
                
            self.print_info(f"Aktywowano profil '{profile_name}'")
            
        # Poproś o hasło, jeśli nie jest ustawione
        if not self.manager.config.server.password:
            password = getpass.getpass("Podaj hasło SSH: ")
            self.manager.config.server.password = password
            
        if not self.manager.config.server.sudo_password:
            sudo_password = getpass.getpass("Podaj hasło sudo: ")
            self.manager.config.server.sudo_password = sudo_password
            
        # Połącz z serwerem
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Łączenie z serwerem..."),
            transient=True,
        ) as progress:
            progress.add_task("connect", total=None)
            success, error = self.manager.connect_to_server()
            
        if not success:
            self.print_error(f"Nie można połączyć się z serwerem: {error}")
            return 1
            
        self.print_success(f"Połączono z serwerem {self.manager.config.server.host}")
        
        # Wyświetl informacje o serwerze
        table = Table(title=f"Informacje o serwerze {self.manager.config.server.host}")
        table.add_column("Parametr", style="cyan")
        table.add_column("Wartość", style="green")
        
        table.add_row("Host", self.manager.config.server.host)
        table.add_row("Użytkownik", self.manager.config.server.username)
        table.add_row("Katalog aplikacji", self.manager.config.server.app_dir)
        table.add_row("Usługi", ", ".join(self.manager.config.server.services))
        
        self.console.print(table)
        
        # Zapytaj czy chcesz zaktualizować hasła w profilu
        update_passwords = Confirm.ask("Czy chcesz zapisać hasła w profilu?")
        if update_passwords:
            profile_data = {
                "name": self.manager.config.name,
                "server": {
                    "host": self.manager.config.server.host,
                    "username": self.manager.config.server.username,
                    "password": self.manager.config.server.password,
                    "sudo_password": self.manager.config.server.sudo_password,
                    "app_dir": self.manager.config.server.app_dir,
                    "services": self.manager.config.server.services
                }
            }
            
            if self.manager.save_profile(self.manager.config.name, profile_data):
                self.print_success(f"Zaktualizowano profil '{self.manager.config.name}'")
            else:
                self.print_error(f"Nie można zaktualizować profilu '{self.manager.config.name}'")
                
        return 0

    def backup_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie backup.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header("Kopia zapasowa plików konfiguracyjnych")
        
        # Sprawdź czy jest aktywny profil
        if not self.manager.active_profile:
            self.print_error("Brak aktywnego profilu. Użyj 'connect', aby połączyć się z serwerem")
            return 1
            
        # Sprawdź czy jest połączenie z serwerem
        if not self.manager.ssh_manager:
            self.print_error("Brak połączenia z serwerem. Użyj 'connect', aby połączyć się z serwerem")
            return 1
            
        # Utwórz kopię zapasową
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Tworzenie kopii zapasowej..."),
            transient=True,
        ) as progress:
            progress.add_task("backup", total=None)
            success, successful, failed = self.manager.backup_server_files()
            
        if not success:
            self.print_error("Nie można utworzyć kopii zapasowej")
            return 1
            
        self.print_success(f"Utworzono kopię zapasową plików konfiguracyjnych ({len(successful)} plików)")
        
        if failed:
            self.print_warning(f"Nie udało się skopiować {len(failed)} plików:")
            for path in failed:
                self.console.print(f"  - {path}")
                
        # Skopiuj do pamięci podręcznej
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Kopiowanie do pamięci podręcznej..."),
            transient=True,
        ) as progress:
            progress.add_task("cache", total=None)
            success = self.manager.copy_server_to_cache()
            
        if success:
            self.print_success("Skopiowano pliki do pamięci podręcznej")
        else:
            self.print_error("Nie można skopiować plików do pamięci podręcznej")
            
        return 0

    def diff_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie diff.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header("Różnice w plikach konfiguracyjnych")
        
        # Sprawdź czy jest aktywny profil
        if not self.manager.active_profile:
            self.print_error("Brak aktywnego profilu. Użyj 'connect', aby połączyć się z serwerem")
            return 1
            
        # Znajdź różnice
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Wyszukiwanie różnic..."),
            transient=True,
        ) as progress:
            progress.add_task("diff", total=None)
            differences = self.manager.find_differences()
            
        if not differences:
            self.print_info("Nie znaleziono różnic między plikami")
            return 0
            
        self.print_info(f"Znaleziono różnice w {len(differences)} plikach:")
        
        for i, diff in enumerate(differences, 1):
            panel = Panel(
                f"Plik: [bold cyan]{diff.rel_path}[/bold cyan]\n"
                f"Stan serwera: [bold blue]{diff.server_path}[/bold blue]\n"
                f"Stan lokalny: [bold green]{diff.cache_path}[/bold green]\n\n"
                + "\n".join([
                    line.replace("- ", "[bold red]- [/bold red]").replace("+ ", "[bold green]+ [/bold green]")
                    for line in diff.differences[:10]
                ]) +
                (f"\n[italic]...i {len(diff.differences) - 10} więcej linii[/italic]" if len(diff.differences) > 10 else ""),
                title=f"Różnica {i}/{len(differences)}",
                expand=False
            )
            self.console.print(panel)
            
        return 0

    def update_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie update.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header("Aktualizacja plików konfiguracyjnych")
        
        # Sprawdź czy jest aktywny profil
        if not self.manager.active_profile:
            self.print_error("Brak aktywnego profilu. Użyj 'connect', aby połączyć się z serwerem")
            return 1
            
        # Sprawdź czy jest połączenie z serwerem
        if not self.manager.ssh_manager:
            self.print_error("Brak połączenia z serwerem. Użyj 'connect', aby połączyć się z serwerem")
            return 1
            
        # Znajdź różnice
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Wyszukiwanie różnic..."),
            transient=True,
        ) as progress:
            progress.add_task("diff", total=None)
            differences = self.manager.find_differences()
            
        if not differences:
            self.print_info("Nie znaleziono różnic między plikami")
            return 0
            
        self.print_info(f"Znaleziono różnice w {len(differences)} plikach")
        
        for i, diff in enumerate(differences, 1):
            self.console.print(f"[bold cyan]{i}.[/bold cyan] {diff.rel_path}")
            
        update_confirm = Confirm.ask("Czy chcesz zaktualizować pliki na serwerze?")
        if not update_confirm:
            self.print_info("Anulowano aktualizację")
            return 0
            
        # Aktualizuj pliki
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Aktualizacja plików..."),
            transient=True,
        ) as progress:
            progress.add_task("update", total=None)
            updated, failed = self.manager.update_server_files(differences)
            
        if not updated:
            self.print_error("Nie udało się zaktualizować żadnego pliku")
            return 1
            
        self.print_success(f"Zaktualizowano {len(updated)} plików")
        
        if failed:
            self.print_warning(f"Nie udało się zaktualizować {len(failed)} plików:")
            for path in failed:
                self.console.print(f"  - {path}")
                
        # Restart usług
        restart_confirm = Confirm.ask("Czy chcesz zrestartować usługi?")
        if restart_confirm:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Restart usług..."),
                transient=True,
            ) as progress:
                progress.add_task("restart", total=None)
                results = self.manager.restart_services()
                
            for service, success in results.items():
                if success:
                    self.print_success(f"Zrestartowano usługę {service}")
                else:
                    self.print_error(f"Nie udało się zrestartować usługi {service}")
                    
        return 0

    def profile_add_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie profile add.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header(f"Dodawanie profilu '{args.name}'")
        
        # Sprawdź czy profil już istnieje
        if args.name in self.manager.list_profiles():
            overwrite = Confirm.ask(f"Profil '{args.name}' już istnieje. Czy chcesz go nadpisać?")
            if not overwrite:
                self.print_info("Anulowano dodawanie profilu")
                return 0
                
        # Przygotuj dane profilu
        profile_data = {
            "name": args.name,
            "server": {
                "host": args.host,
                "username": args.user,
                "password": "",
                "sudo_password": "",
                "app_dir": args.dir,
                "services": args.services.split(",")
            }
        }
        
        # Zapytaj o hasła
        save_passwords = Confirm.ask("Czy chcesz zapisać hasła w profilu?")
        if save_passwords:
            password = getpass.getpass("Podaj hasło SSH: ")
            sudo_password = getpass.getpass("Podaj hasło sudo: ")
            
            profile_data["server"]["password"] = password
            profile_data["server"]["sudo_password"] = sudo_password
            
        # Zapisz profil
        if self.manager.save_profile(args.name, profile_data):
            self.print_success(f"Dodano profil '{args.name}'")
            
            # Zapytaj czy ustawić jako aktywny
            if not self.manager.active_profile:
                activate = Confirm.ask("Czy chcesz ustawić ten profil jako aktywny?")
                if activate and self.manager.set_active_profile(args.name):
                    self.print_success(f"Ustawiono profil '{args.name}' jako aktywny")
                    
            return 0
        else:
            self.print_error(f"Nie udało się dodać profilu '{args.name}'")
            return 1

    def profile_list_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie profile list.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header("Lista profili")
        
        profiles = self.manager.list_profiles()
        if not profiles:
            self.print_info("Brak zapisanych profili")
            return 0
            
        table = Table(title="Dostępne profile")
        table.add_column("Nazwa", style="cyan")
        table.add_column("Host", style="green")
        table.add_column("Użytkownik", style="green")
        table.add_column("Katalog aplikacji", style="green")
        table.add_column("Usługi", style="green")
        table.add_column("Aktywny", style="green")
        
        for profile_name in profiles:
            details = self.manager.get_profile_details(profile_name)
            if details:
                table.add_row(
                    profile_name,
                    details["server"]["host"],
                    details["server"]["username"],
                    details["server"]["app_dir"],
                    ", ".join(details["server"]["services"]),
                    "✓" if self.manager.active_profile == profile_name else ""
                )
                
        self.console.print(table)
        return 0

    def profile_remove_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie profile remove.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header(f"Usuwanie profilu '{args.name}'")
        
        # Sprawdź czy profil istnieje
        if args.name not in self.manager.list_profiles():
            self.print_error(f"Profil '{args.name}' nie istnieje")
            return 1
            
        # Potwierdź usunięcie
        confirm = Confirm.ask(f"Czy na pewno chcesz usunąć profil '{args.name}'?")
        if not confirm:
            self.print_info("Anulowano usuwanie profilu")
            return 0
            
        # Usuń profil
        if self.manager.delete_profile(args.name):
            self.print_success(f"Usunięto profil '{args.name}'")
            return 0
        else:
            self.print_error(f"Nie udało się usunąć profilu '{args.name}'")
            return 1

    def profile_activate_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie profile activate.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        self.print_header(f"Aktywacja profilu '{args.name}'")
        
        # Sprawdź czy profil istnieje
        if args.name not in self.manager.list_profiles():
            self.print_error(f"Profil '{args.name}' nie istnieje")
            return 1
            
        # Aktywuj profil
        if self.manager.set_active_profile(args.name):
            self.print_success(f"Aktywowano profil '{args.name}'")
            return 0
        else:
            self.print_error(f"Nie udało się aktywować profilu '{args.name}'")
            return 1

    def profile_command(self, args: argparse.Namespace) -> int:
        """
        Obsługuje polecenie profile.
        
        Args:
            args: Argumenty wiersza poleceń
            
        Returns:
            Kod wyjścia
        """
        if args.profile_command == "add":
            return self.profile_add_command(args)
        elif args.profile_command == "list":
            return self.profile_list_command(args)
        elif args.profile_command == "remove":
            return self.profile_remove_command(args)
        elif args.profile_command == "activate":
            return self.profile_activate_command(args)
        else:
            self.print_error("Nieznane polecenie profilu")
            return 1

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Uruchamia interfejs wiersza poleceń.
        
        Args:
            args: Argumenty wiersza poleceń (domyślnie sys.argv[1:])
            
        Returns:
            Kod wyjścia
        """
        parser = self.create_parser()
        parsed_args = parser.parse_args(args if args is not None else sys.argv[1:])
        
        # Jeśli nie podano polecenia, wyświetl pomoc
        if not parsed_args.command:
            parser.print_help()
            return 0
            
        # Obsłuż polecenie
        if parsed_args.command == "connect":
            return self.connect_command(parsed_args)
        elif parsed_args.command == "backup":
            return self.backup_command(parsed_args)
        elif parsed_args.command == "diff":
            return self.diff_command(parsed_args)
        elif parsed_args.command == "update":
            return self.update_command(parsed_args)
        elif parsed_args.command == "profile":
            return self.profile_command(parsed_args)
        else:
            self.print_error("Nieznane polecenie")
            return 1

def main():
    """
    Główna funkcja programu.
    """
    cli = CLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main()) 