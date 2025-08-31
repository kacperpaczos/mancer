#!/usr/bin/env python3
import argparse
import getpass
import sys
from typing import List, Optional

from .inspector import SystemdInspector


def create_parser() -> argparse.ArgumentParser:
    """
    Tworzy parser argumentów linii poleceń.

    Returns:
        Skonfigurowany parser argumentów
    """
    parser = argparse.ArgumentParser(
        prog="systemd-inspector",
        description="Narzędzie do monitorowania i raportowania stanu jednostek systemd na zdalnych serwerach",
    )

    # Utworzenie podpoleceń (subparsers)
    subparsers = parser.add_subparsers(dest="command", help="Dostępne polecenia")

    # Polecenie inspect - pobranie i wygenerowanie raportu jednostek systemd
    inspect_parser = subparsers.add_parser(
        "inspect", help="Pobierz i wygeneruj raport jednostek systemd"
    )
    inspect_parser.add_argument("-H", "--host", help="Adres serwera", type=str)
    inspect_parser.add_argument("-u", "--user", help="Nazwa użytkownika", type=str)
    inspect_parser.add_argument(
        "-p", "--profile", help="Nazwa profilu do użycia", type=str
    )
    inspect_parser.add_argument(
        "-o", "--output-dir", help="Katalog wyjściowy dla raportu", type=str
    )

    # Polecenie profile - zarządzanie profilami połączeń
    profile_parser = subparsers.add_parser(
        "profile", help="Zarządzaj profilami połączeń"
    )
    profile_subparsers = profile_parser.add_subparsers(
        dest="profile_command", help="Dostępne operacje na profilach"
    )

    # Polecenie profile add - dodanie nowego profilu
    profile_add_parser = profile_subparsers.add_parser(
        "add", help="Dodaj nowy profil połączenia"
    )
    profile_add_parser.add_argument("name", help="Nazwa profilu", type=str)
    profile_add_parser.add_argument(
        "-H", "--host", help="Adres serwera", type=str, required=True
    )
    profile_add_parser.add_argument(
        "-u", "--user", help="Nazwa użytkownika", type=str, required=True
    )
    profile_add_parser.add_argument(
        "--password",
        help="Hasło (opcjonalnie, jeśli nie podane, zostanie zapytane interaktywnie)",
        action="store_true",
    )

    # Polecenie profile list - wyświetlenie listy profili
    profile_list_parser = profile_subparsers.add_parser(
        "list", help="Wyświetl listę profili połączeń"
    )

    # Polecenie profile remove - usunięcie profilu
    profile_remove_parser = profile_subparsers.add_parser(
        "remove", help="Usuń profil połączenia"
    )
    profile_remove_parser.add_argument(
        "name", help="Nazwa profilu do usunięcia", type=str
    )

    return parser


def command_inspect(inspector: SystemdInspector, args: argparse.Namespace) -> int:
    """
    Obsługuje polecenie inspect - pobiera i generuje raport jednostek systemd.

    Args:
        inspector: Instancja SystemdInspector
        args: Argumenty z linii poleceń

    Returns:
        Kod wyjścia (0 dla sukcesu, inny dla błędu)
    """
    hostname = None
    username = None
    password = None

    # Jeśli podano profil, użyj go
    if args.profile:
        hostname, username, password = inspector.load_profile(args.profile)
        if not hostname:
            print(f"Błąd: Profil '{args.profile}' nie istnieje")
            return 1
        print(f"Używam profilu '{args.profile}'")
    else:
        # Jeśli nie podano profilu, użyj parametrów z linii poleceń
        if not args.host:
            hostname_input = input("Podaj adres hosta: ")
            hostname = hostname_input if hostname_input else None
        else:
            hostname = args.host

        if not args.user:
            username_input = input("Podaj nazwę użytkownika: ")
            username = username_input if username_input else None
        else:
            username = args.user

        if not hostname or not username:
            print("Błąd: Nie podano adresu hosta lub nazwy użytkownika")
            return 1

        password = getpass.getpass(
            "Podaj hasło (pozostaw puste dla uwierzytelniania kluczem): "
        )
        password = password if password else None

        # Zapytaj o zapisanie profilu
        save_profile_input = input(
            "Czy chcesz zapisać ten profil na przyszłość? (t/n): "
        ).lower()
        if save_profile_input == "t":
            profile_name = input("Podaj nazwę profilu: ")
            if profile_name:
                if inspector.save_profile(profile_name, hostname, username, password):
                    print(f"Profil '{profile_name}' został zapisany")
                else:
                    print("Błąd: Nie można zapisać profilu")
            else:
                print("Błąd: Nie podano nazwy profilu")

    # Pobierz jednostki systemd
    print(f"Łączenie z serwerem {hostname}...")
    units_output = inspector.get_systemd_units(hostname, username, password)

    if not units_output:
        print("Błąd: Nie można pobrać jednostek systemd")
        return 1

    # Parsuj jednostki
    units = inspector.parse_units(units_output)

    # Zapisz raport
    output_dir = args.output_dir if args.output_dir else None
    filename = inspector.save_report(hostname, units, output_dir)

    print(f"\nRaport został zapisany do pliku: {filename}")

    # Wypisz podsumowanie
    print("\nPODSUMOWANIE:")
    print(f"Całkowita liczba jednostek: {units['summary']['total']}")
    print(f"Aktywne: {units['summary']['active']}")
    print(f"Nieaktywne: {units['summary']['inactive']}")
    print(f"Uszkodzone: {units['summary']['failed']}")

    return 0


def command_profile_add(inspector: SystemdInspector, args: argparse.Namespace) -> int:
    """
    Obsługuje polecenie profile add - dodaje nowy profil połączenia.

    Args:
        inspector: Instancja SystemdInspector
        args: Argumenty z linii poleceń

    Returns:
        Kod wyjścia (0 dla sukcesu, inny dla błędu)
    """
    hostname = args.host
    username = args.user
    password = None

    if args.password:
        password = getpass.getpass(
            "Podaj hasło (pozostaw puste dla uwierzytelniania kluczem): "
        )

    if inspector.save_profile(args.name, hostname, username, password):
        print(f"Profil '{args.name}' został zapisany")
        return 0
    else:
        print("Błąd: Nie można zapisać profilu")
        return 1


def command_profile_list(inspector: SystemdInspector, args: argparse.Namespace) -> int:
    """
    Obsługuje polecenie profile list - wyświetla listę profili połączeń.

    Args:
        inspector: Instancja SystemdInspector
        args: Argumenty z linii poleceń

    Returns:
        Kod wyjścia (0 dla sukcesu, inny dla błędu)
    """
    profiles = inspector.list_profiles()

    if not profiles:
        print("Brak zapisanych profili")
        return 0

    print("Dostępne profile połączeń:")
    for i, profile_name in enumerate(profiles, 1):
        hostname, username, _ = inspector.load_profile(profile_name)
        print(f"{i}. {profile_name} ({username}@{hostname})")

    return 0


def command_profile_remove(
    inspector: SystemdInspector, args: argparse.Namespace
) -> int:
    """
    Obsługuje polecenie profile remove - usuwa profil połączenia.

    Args:
        inspector: Instancja SystemdInspector
        args: Argumenty z linii poleceń

    Returns:
        Kod wyjścia (0 dla sukcesu, inny dla błędu)
    """
    if inspector.delete_profile(args.name):
        print(f"Profil '{args.name}' został usunięty")
        return 0
    else:
        print(f"Błąd: Profil '{args.name}' nie istnieje lub nie może zostać usunięty")
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """
    Główna funkcja programu.

    Args:
        args: Lista argumentów linii poleceń (opcjonalnie)

    Returns:
        Kod wyjścia (0 dla sukcesu, inny dla błędu)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args if args is not None else sys.argv[1:])

    inspector = SystemdInspector()

    # Obsługa polecenia inspect
    if parsed_args.command == "inspect":
        return command_inspect(inspector, parsed_args)

    # Obsługa poleceń profile
    elif parsed_args.command == "profile":
        if parsed_args.profile_command == "add":
            return command_profile_add(inspector, parsed_args)
        elif parsed_args.profile_command == "list":
            return command_profile_list(inspector, parsed_args)
        elif parsed_args.profile_command == "remove":
            return command_profile_remove(inspector, parsed_args)
        else:
            parser.print_help()
            return 1

    # Jeśli nie podano polecenia, wyświetl pomoc
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
