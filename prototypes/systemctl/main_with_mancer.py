import os
import getpass
from datetime import datetime
import json
import sys

# Dodaj ścieżkę do katalogu głównego projektu, aby można było importować moduły z mancera
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.mancer.domain.service.systemd_service import SystemdService
from src.mancer.domain.shared.profile_producer import ProfileProducer, ConnectionProfile


def main():
    """
    Główna funkcja programu do zarządzania jednostkami systemd z wykorzystaniem 
    funkcjonalności Mancera.
    """
    print("ZARZĄDZANIE SYSTEMD")
    print("-" * 30)
    
    # Inicjalizacja usług
    profile_producer = ProfileProducer()
    systemd_service = SystemdService(profile_producer)
    
    while True:
        print("\nMENU GŁÓWNE")
        print("-" * 20)
        print("1. Zarządzaj profilami serwerów")
        print("2. Pobierz dane systemd z serwerów")
        print("3. Zarządzaj usługami")
        print("4. Wyjście")
        
        choice = input("\nWybierz opcję (1-4): ")
        
        if choice == '1':
            manage_profiles(profile_producer)
        
        elif choice == '2':
            get_systemd_data(systemd_service, profile_producer)
            
        elif choice == '3':
            manage_services(systemd_service, profile_producer)
        
        elif choice == '4':
            print("Do widzenia!")
            break
        
        else:
            print("Nieprawidłowa opcja!")


def manage_profiles(profile_producer):
    """
    Zarządzanie profilami połączeń.
    
    Args:
        profile_producer: Instancja ProfileProducer
    """
    while True:
        print("\nZARZĄDZANIE PROFILAMI")
        print("-" * 30)
        
        # Pobierz listę wszystkich profili
        profiles = profile_producer.list_profiles()
        
        if profiles:
            print(f"\nDostępne profile ({len(profiles)}):")
            for i, profile in enumerate(profiles, 1):
                print(f"{i}. {profile.name} - {profile.hostname} (użytkownik: {profile.username})")
        else:
            print("\nBrak zapisanych profili.")
        
        print("\nOpcje:")
        print("1. Dodaj nowy profil")
        print("2. Edytuj profil")
        print("3. Usuń profil")
        print("4. Powrót")
        
        choice = input("\nWybierz opcję (1-4): ")
        
        if choice == '1':
            add_profile(profile_producer)
        
        elif choice == '2':
            if not profiles:
                print("Brak profili do edycji!")
                continue
                
            profile_idx = int(input("Podaj numer profilu do edycji: ")) - 1
            if 0 <= profile_idx < len(profiles):
                edit_profile(profile_producer, profiles[profile_idx])
            else:
                print("Nieprawidłowy numer profilu!")
        
        elif choice == '3':
            if not profiles:
                print("Brak profili do usunięcia!")
                continue
                
            profile_idx = int(input("Podaj numer profilu do usunięcia: ")) - 1
            if 0 <= profile_idx < len(profiles):
                delete_profile(profile_producer, profiles[profile_idx])
            else:
                print("Nieprawidłowy numer profilu!")
        
        elif choice == '4':
            break
        
        else:
            print("Nieprawidłowa opcja!")


def add_profile(profile_producer):
    """
    Dodaje nowy profil połączenia.
    
    Args:
        profile_producer: Instancja ProfileProducer
    """
    print("\nDODAWANIE NOWEGO PROFILU")
    print("-" * 30)
    
    name = input("Podaj unikalną nazwę profilu: ")
    hostname = input("Podaj adres hosta: ")
    username = input("Podaj nazwę użytkownika: ")
    port = input("Podaj port SSH [22]: ")
    port = int(port) if port.strip() else 22
    
    auth_type = input("Wybierz metodę autoryzacji (1 - hasło, 2 - klucz): ")
    
    password = None
    key_filename = None
    passphrase = None
    
    if auth_type == '1':
        password = getpass.getpass("Podaj hasło: ")
    elif auth_type == '2':
        key_filename = input("Podaj ścieżkę do klucza prywatnego: ")
        use_passphrase = input("Czy klucz wymaga hasła? (t/n): ").lower()
        if use_passphrase == 't':
            passphrase = getpass.getpass("Podaj hasło do klucza: ")
    
    group = input("Podaj grupę serwera (opcjonalnie): ")
    description = input("Podaj opis profilu (opcjonalnie): ")
    
    profile = ConnectionProfile(
        name=name,
        hostname=hostname,
        username=username,
        port=port,
        password=password,
        key_filename=key_filename,
        passphrase=passphrase,
        group=group if group else None,
        description=description if description else None
    )
    
    if profile_producer.add_profile(profile):
        print(f"Profil '{name}' został dodany.")
    else:
        print(f"Nie można dodać profilu '{name}'. Prawdopodobnie już istnieje.")


def edit_profile(profile_producer, profile):
    """
    Edytuje istniejący profil połączenia.
    
    Args:
        profile_producer: Instancja ProfileProducer
        profile: Profil do edycji
    """
    print(f"\nEDYCJA PROFILU: {profile.name}")
    print("-" * 30)
    
    # Pobierz nowe wartości, z domyślnymi wartościami z istniejącego profilu
    hostname = input(f"Adres hosta [{profile.hostname}]: ") or profile.hostname
    username = input(f"Nazwa użytkownika [{profile.username}]: ") or profile.username
    port_str = input(f"Port SSH [{profile.port}]: ") or str(profile.port)
    port = int(port_str)
    
    change_auth = input("Czy chcesz zmienić dane autoryzacji? (t/n): ").lower()
    
    password = profile.password
    key_filename = profile.key_filename
    passphrase = profile.passphrase
    
    if change_auth == 't':
        auth_type = input("Wybierz metodę autoryzacji (1 - hasło, 2 - klucz): ")
        
        if auth_type == '1':
            password = getpass.getpass("Podaj hasło: ")
            key_filename = None
            passphrase = None
        elif auth_type == '2':
            password = None
            key_filename = input("Podaj ścieżkę do klucza prywatnego: ")
            use_passphrase = input("Czy klucz wymaga hasła? (t/n): ").lower()
            if use_passphrase == 't':
                passphrase = getpass.getpass("Podaj hasło do klucza: ")
            else:
                passphrase = None
    
    group = input(f"Grupa serwera [{profile.group or ''}]: ") or profile.group
    description = input(f"Opis profilu [{profile.description or ''}]: ") or profile.description
    
    updated_profile = ConnectionProfile(
        name=profile.name,  # Nazwa profilu pozostaje niezmieniona
        hostname=hostname,
        username=username,
        port=port,
        password=password,
        key_filename=key_filename,
        passphrase=passphrase,
        group=group,
        description=description
    )
    
    if profile_producer.update_profile(updated_profile):
        print(f"Profil '{profile.name}' został zaktualizowany.")
    else:
        print(f"Nie można zaktualizować profilu '{profile.name}'.")


def delete_profile(profile_producer, profile):
    """
    Usuwa profil połączenia.
    
    Args:
        profile_producer: Instancja ProfileProducer
        profile: Profil do usunięcia
    """
    confirm = input(f"Czy na pewno chcesz usunąć profil '{profile.name}'? (t/n): ").lower()
    
    if confirm == 't':
        if profile_producer.delete_profile(profile.name):
            print(f"Profil '{profile.name}' został usunięty.")
        else:
            print(f"Nie można usunąć profilu '{profile.name}'.")


def get_systemd_data(systemd_service, profile_producer):
    """
    Pobiera dane systemd z wybranych serwerów.
    
    Args:
        systemd_service: Instancja SystemdService
        profile_producer: Instancja ProfileProducer
    """
    profiles = profile_producer.list_profiles()
    
    if not profiles:
        print("Brak zapisanych profili. Najpierw dodaj profile serwerów.")
        return
    
    print("\nDostępne profile:")
    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile.name} - {profile.hostname} (użytkownik: {profile.username})")
    
    selection = input("\nPodaj numery serwerów oddzielone przecinkami (lub 'all' dla wszystkich): ")
    
    profile_names = []
    if selection.lower() == 'all':
        profile_names = [p.name for p in profiles]
    else:
        try:
            selected_indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
            for idx in selected_indices:
                if 0 <= idx < len(profiles):
                    profile_names.append(profiles[idx].name)
                else:
                    print(f"Ignorowanie nieprawidłowego indeksu: {idx + 1}")
        except ValueError:
            print("Nieprawidłowy format selekcji. Użyj liczb oddzielonych przecinkami.")
            return
    
    if not profile_names:
        print("Nie wybrano żadnych serwerów.")
        return
    
    print(f"\nPobieranie danych systemd z {len(profile_names)} serwerów...")
    
    # Pobranie danych systemd ze wszystkich wybranych serwerów
    results = systemd_service.get_systemd_units(profile_names)
    
    successful = [r for r in results.values() if r['status'] == 'success']
    failed = [r for r in results.values() if r['status'] != 'success']
    
    print(f"\nPodsumowanie: {len(successful)} sukces, {len(failed)} błąd")
    
    if failed:
        print("\nBłędy:")
        for result in failed:
            print(f"- {result['profile_name']}: {result.get('error', 'Nieznany błąd')}")
    
    # Parsowanie i zapisywanie raportów dla udanych połączeń
    if successful:
        # Utwórz katalog na raporty, jeśli nie istnieje
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        print("\nGenerowanie raportów...")
        for result in successful:
            units = systemd_service.parse_units(result['content'])
            file_path = systemd_service.save_report(result['hostname'], units, reports_dir)
            print(f"Raport dla {result['hostname']} zapisany do pliku: {file_path}")


def manage_services(systemd_service, profile_producer):
    """
    Zarządza usługami systemd na wybranym serwerze.
    
    Args:
        systemd_service: Instancja SystemdService
        profile_producer: Instancja ProfileProducer
    """
    profiles = profile_producer.list_profiles()
    
    if not profiles:
        print("Brak zapisanych profili. Najpierw dodaj profile serwerów.")
        return
    
    print("\nWybierz serwer:")
    for i, profile in enumerate(profiles, 1):
        print(f"{i}. {profile.name} - {profile.hostname} (użytkownik: {profile.username})")
    
    try:
        server_idx = int(input("\nPodaj numer serwera: ")) - 1
        if not (0 <= server_idx < len(profiles)):
            print("Nieprawidłowy numer serwera!")
            return
    except ValueError:
        print("Nieprawidłowy format numeru!")
        return
    
    selected_profile = profiles[server_idx]
    
    # Menu akcji dla usługi
    print(f"\nZarządzanie usługami dla {selected_profile.hostname}")
    print("1. Pokaż status usługi")
    print("2. Uruchom usługę")
    print("3. Zatrzymaj usługę")
    print("4. Zrestartuj usługę")
    print("5. Włącz usługę (enable)")
    print("6. Wyłącz usługę (disable)")
    
    actions = {
        '1': 'status',
        '2': 'start',
        '3': 'stop',
        '4': 'restart',
        '5': 'enable',
        '6': 'disable'
    }
    
    action_choice = input("\nWybierz akcję (1-6): ")
    
    if action_choice not in actions:
        print("Nieprawidłowa opcja!")
        return
    
    service_name = input("Podaj nazwę usługi: ")
    
    print(f"\nWykonywanie operacji {actions[action_choice]} dla usługi {service_name} na {selected_profile.hostname}...")
    
    result = systemd_service.manage_systemd_service(selected_profile.name, service_name, actions[action_choice])
    
    print(f"\nWynik operacji {actions[action_choice]} dla {service_name} na {result['hostname']}:")
    if result['status'] == 'success':
        print("Status: SUKCES")
        if result.get('output'):
            print(result['output'])
    else:
        print(f"Status: BŁĄD - {result.get('error', 'Nieznany błąd')}")
        if result.get('output'):
            print(result['output'])


if __name__ == "__main__":
    main() 