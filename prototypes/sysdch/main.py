import subprocess
import getpass
from datetime import datetime
import json
import os
import base64
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import time
from pathlib import Path
from fuzzywuzzy import process

def get_encryption_key():
    # Używamy stałego klucza dla uproszczenia (w produkcji należy użyć bezpieczniejszego rozwiązania)
    key = b'TluxwB3fV_GWuLkR1_BzGs1Zk90TYAuhNMZP_0q4WyM='
    return base64.urlsafe_b64decode(key)

def encrypt_password(password):
    try:
        f = Fernet(get_encryption_key())
        return f.encrypt(password.encode()).decode()
    except Exception as e:
        print(f"Błąd szyfrowania hasła: {str(e)}")
        return None

def decrypt_password(encrypted_password):
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        print(f"Błąd deszyfrowania hasła: {str(e)}")
        return None

def get_systemd_units(hostname, username, password=None):
    try:
        # Tworzymy unikalną nazwę pliku tymczasowego
        temp_filename = f"systemd_units_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        remote_temp_file = f"/tmp/{temp_filename}"
        
        # Polecenie do pobrania wszystkich jednostek i zapisania do pliku
        systemctl_cmd = f"systemctl list-units --all --no-pager > {remote_temp_file}"
        
        # Wykonaj polecenie na zdalnym serwerze
        if password:
            ssh_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} '{systemctl_cmd}'"
        else:
            ssh_cmd = f"ssh {username}@{hostname} '{systemctl_cmd}'"
        
        # Wykonaj polecenie SSH
        subprocess.run(ssh_cmd, shell=True, check=True)
        
        # Skopiuj plik ze zdalnego serwera
        if password:
            scp_cmd = f"sshpass -p '{password}' scp {username}@{hostname}:{remote_temp_file} ./{temp_filename}"
        else:
            scp_cmd = f"scp {username}@{hostname}:{remote_temp_file} ./{temp_filename}"
        
        subprocess.run(scp_cmd, shell=True, check=True)
        
        # Usuń plik tymczasowy na zdalnym serwerze
        if password:
            cleanup_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} 'rm {remote_temp_file}'"
        else:
            cleanup_cmd = f"ssh {username}@{hostname} 'rm {remote_temp_file}'"
        
        subprocess.run(cleanup_cmd, shell=True, check=True)
        
        # Odczytaj zawartość pliku lokalnego
        with open(temp_filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Usuń lokalny plik tymczasowy
        os.remove(temp_filename)
        
        return content
        
    except subprocess.CalledProcessError as e:
        print(f"Błąd wykonania polecenia: {e}")
        return None
    except Exception as e:
        print(f"Wystąpił błąd: {str(e)}")
        return None

def parse_units(units_output):
    units = {
        'summary': {
            'total': 0,
            'active': 0,
            'inactive': 0,
            'failed': 0
        },
        'by_type': {
            'service': [],
            'socket': [],
            'target': [],
            'path': [],
            'timer': [],
            'mount': [],
            'other': []
        },
        'by_state': {
            'active': [],
            'inactive': [],
            'failed': [],
            'other': []
        },
        'dimark': [], #TODO zrobić żeby moża było kategoryzwać po naziwe automatycznie
        'user': []
    }
    
    if not units_output:
        return units
    
    lines = units_output.split('\n')
    parsing_units = False
    
    for line in lines:
        # Pomijamy puste linie i nagłówki
        if not line.strip() or 'UNIT' in line and 'LOAD' in line and 'ACTIVE' in line:
            continue
            
        # Sprawdzamy czy linia zawiera informacje o jednostce
        if '●' in line or ('.' in line and not line.startswith('To show')):
            parsing_units = True
            parts = line.split()
            if len(parts) < 3:
                continue
            
            # Pobierz nazwę jednostki (pierwszy element zawierający kropkę)
            unit_name = next((part for part in parts if '.' in part), '')
            if not unit_name:
                continue
                
            # Pobierz stan (active, inactive, failed)
            status = next((part for part in parts if part.lower() in ['active', 'inactive', 'failed']), 'other')
            
            unit_info = f"{unit_name} - {status}"
            
            # Aktualizuj statystyki
            units['summary']['total'] += 1
            units['summary'][status if status in ['active', 'inactive', 'failed'] else 'inactive'] += 1
            
            # Kategoryzuj według typu
            unit_type = unit_name.split('.')[-1] if '.' in unit_name else 'other'
            if unit_type in units['by_type']:
                units['by_type'][unit_type].append(unit_info)
            else:
                units['by_type']['other'].append(unit_info)
            
            # Kategoryzuj według stanu
            if status in units['by_state']:
                units['by_state'][status].append(unit_info)
            else:
                units['by_state']['other'].append(unit_info)
            
            # Sprawdź czy to jednostka dimark
            if 'dimark_' in unit_name.lower():
                units['dimark'].append(unit_info)
            
            # Sprawdź czy to jednostka użytkownika
            if '@' in unit_name or 'user' in unit_name:
                units['user'].append(unit_info)
        
        # Zakończ parsowanie gdy napotkamy podsumowanie
        elif 'loaded units listed' in line.lower():
            break
    
    return units

def save_report(hostname, units):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"systemd_units_report_{hostname}_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Raport jednostek systemd dla {hostname}\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        # Podsumowanie
        f.write("PODSUMOWANIE:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Całkowita liczba jednostek: {units['summary']['total']}\n")
        f.write(f"Aktywne: {units['summary']['active']}\n")
        f.write(f"Nieaktywne: {units['summary']['inactive']}\n")
        f.write(f"Uszkodzone: {units['summary']['failed']}\n\n")
        
        # Sekcja jednostek Dimark
        f.write("JEDNOSTKI DIMARK:\n")
        f.write("-" * 20 + "\n")
        if units['dimark']:
            for unit in units['dimark']:
                f.write(f"{unit}\n")
        else:
            f.write("Brak jednostek dimark\n")
        f.write("\n")
        
        # Sekcja jednostek użytkownika
        f.write("JEDNOSTKI UŻYTKOWNIKA:\n")
        f.write("-" * 20 + "\n")
        if units['user']:
            for unit in units['user']:
                f.write(f"{unit}\n")
        else:
            f.write("Brak jednostek użytkownika\n")
        f.write("\n")
        
        # Sekcje według typu
        f.write("PODZIAŁ WEDŁUG TYPU:\n")
        f.write("-" * 20 + "\n")
        for unit_type, units_list in units['by_type'].items():
            if units_list:  # Pokazuj tylko typy, które mają jakieś jednostki
                f.write(f"\n{unit_type.upper()}:\n")
                for unit in units_list:
                    f.write(f"{unit}\n")
        f.write("\n")
        
        # Sekcje według stanu
        f.write("PODZIAŁ WEDŁUG STANU:\n")
        f.write("-" * 20 + "\n")
        for state, units_list in units['by_state'].items():
            if units_list:  # Pokazuj tylko stany, które mają jakieś jednostki
                f.write(f"\n{state.upper()}:\n")
                for unit in units_list:
                    f.write(f"{unit}\n")
    
    return filename

def load_profile():
    try:
        with open('connection_profile.json', 'r') as f:
            data = json.load(f)
            return data.get('hostname'), data.get('username'), data.get('password')
    except FileNotFoundError:
        return None, None, None

def save_profile(hostname, username, password):
    data = {
        'hostname': hostname,
        'username': username,
        'password': password
    }
    with open('connection_profile.json', 'w') as f:
        json.dump(data, f, indent=4)

def find_unit_path(hostname, username, password, unit_name):
    """Znajduje pełną ścieżkę do pliku jednostki w systemie"""
    search_paths = [
        "/etc/systemd/system/",
        "/usr/lib/systemd/system/",
        "/run/systemd/system/",
        "/usr/local/lib/systemd/system/"
    ]
    
    for path in search_paths:
        cmd = f"sshpass -p '{password}' ssh {username}@{hostname} 'test -f {path}{unit_name} && echo {path}{unit_name}'"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                return result.stdout.strip()
        except subprocess.CalledProcessError:
            continue
    
    return None

def find_unit_fuzzy(unit_name, units):
    # Tworzymy listę wszystkich nazw jednostek
    all_units = []
    for unit_type in units['by_type'].values():
        for unit_info in unit_type:
            name = unit_info.split(" - ")[0]
            all_units.append(name)
    
    # Znajdujemy najlepsze dopasowanie
    matches = process.extractBests(unit_name, all_units, score_cutoff=50, limit=5)
    return matches

def select_unit_from_matches(console, matches):
    """Wyświetla listę dopasowań i pozwala wybrać jednostkę numerem"""
    if not matches:
        return None
        
    console.print("\n[bold]Znalezione jednostki:[/]")
    for idx, (unit, score) in enumerate(matches, 1):
        console.print(f"[cyan]{idx}.[/] {unit} (podobieństwo: {score}%)")
    
    choice = Prompt.ask(
        "\nWybierz numer jednostki",
        choices=[str(i) for i in range(1, len(matches) + 1)]
    )
    
    return matches[int(choice) - 1][0]

def manage_systemd_unit(hostname, username, password, unit_name):
    console = Console()
    
    unit_path = find_unit_path(hostname, username, password, unit_name)
    if not unit_path:
        console.print(f"[red]Nie można znaleźć pliku jednostki {unit_name}![/]")
        return unit_name
    
    console.print(f"[green]Znaleziono plik jednostki:[/] {unit_path}")
    
    while True:
        console.print(Panel(f"Zarządzanie jednostką: [bold green]{unit_name}[/]\nŚcieżka: {unit_path}"))
        console.print("\n[bold]Dostępne opcje:[/]")
        console.print("1. Zmień nazwę jednostki")
        console.print("2. Pokaż status")
        console.print("3. Powrót")
        
        choice = Prompt.ask("Wybierz opcję", choices=["1", "2", "3"])
        
        if choice == "1":
            new_name = Prompt.ask("Podaj nową nazwę jednostki")
            new_path = f"{'/'.join(unit_path.split('/')[:-1])}/{new_name}"
            
            # Poprawiona kolejność operacji
            commands = [
                # 1. Zatrzymujemy i wyłączamy starą jednostkę
                f'SUDO_ASKPASS="echo {password}" sudo -A systemctl stop {unit_name}',
                f'SUDO_ASKPASS="echo {password}" sudo -A systemctl disable {unit_name}',
                
                # 2. Kopiujemy plik jednostki pod nową nazwą
                f'SUDO_ASKPASS="echo {password}" sudo -A cp {unit_path} {new_path}',
                
                # 3. Usuwamy stary plik jednostki
                f'SUDO_ASKPASS="echo {password}" sudo -A rm {unit_path}',
                
                # 4. Przeładowujemy konfigurację systemd
                'SUDO_ASKPASS="echo {password}" sudo -A systemctl daemon-reload',
                
                # 5. Włączamy i uruchamiamy nową jednostkę
                f'SUDO_ASKPASS="echo {password}" sudo -A systemctl enable {new_name}',
                f'SUDO_ASKPASS="echo {password}" sudo -A systemctl start {new_name}'
            ]
            
            # Tworzymy tymczasowy skrypt askpass
            setup_cmd = f"""
            echo '#!/bin/bash
            echo "{password}"' > /tmp/askpass.sh && chmod +x /tmp/askpass.sh && 
            export SUDO_ASKPASS=/tmp/askpass.sh && 
            {" && ".join(commands)} && 
            rm /tmp/askpass.sh
            """
            
            ssh_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} '{setup_cmd}'"
            
            try:
                subprocess.run(ssh_cmd, shell=True, check=True)
                console.print(f"[green]Pomyślnie zmieniono nazwę jednostki na {new_name}[/]")
                
                # Sprawdzenie statusu nowej jednostki
                status_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} 'SUDO_ASKPASS=/tmp/askpass.sh sudo -A systemctl is-active {new_name}'"
                result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout.strip() == "active":
                    console.print("[green]Jednostka jest aktywna![/]")
                else:
                    console.print("[red]Uwaga: Jednostka nie jest aktywna![/]")
                
                return new_name
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Błąd podczas zmiany nazwy jednostki: {str(e)}[/]")
                
        elif choice == "2":
            # Uproszczone polecenie do sprawdzenia statusu
            status_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} 'sudo -S systemctl status {unit_name}'"
            try:
                # Przekazujemy hasło przez STDIN
                result = subprocess.run(
                    status_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    input=f"{password}\n"
                )
                if result.stdout:
                    console.print(Panel(result.stdout))
                else:
                    console.print(Panel(result.stderr))
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Błąd podczas pobierania statusu: {str(e)}[/]")
                
        else:
            return unit_name

def main():
    console = Console()
    saved_hostname, saved_username, saved_password = load_profile()
    
    if saved_hostname and saved_username and saved_password:
        hostname = saved_hostname
        username = saved_username
        password = saved_password
    else:
        hostname = Prompt.ask("Podaj adres hosta")
        username = Prompt.ask("Podaj nazwę użytkownika")
        password = getpass.getpass("Podaj hasło: ")
        save_profile(hostname, username, password)
    
    while True:
        console.print("[bold blue]Pobieranie listy jednostek...[/]")
        units_output = get_systemd_units(hostname, username, password)
        
        if units_output:
            units = parse_units(units_output)
            
            table = Table(title="Jednostki systemd")
            table.add_column("Nazwa jednostki", style="cyan")
            table.add_column("Stan", style="magenta")
            
            for unit_type in units['by_type'].values():
                for unit_info in unit_type:
                    name, state = unit_info.split(" - ")
                    table.add_row(name, state)
            
            console.print(table)
            
            unit_choice = Prompt.ask("\nWyszukaj jednostkę (lub 'q' aby wyjść)")
            if unit_choice.lower() == 'q':
                break
            
            # Fuzzy search i wybór z listy
            matches = find_unit_fuzzy(unit_choice, units)
            if matches:
                selected_unit = select_unit_from_matches(console, matches)
                if selected_unit:
                    manage_systemd_unit(hostname, username, password, selected_unit)
                else:
                    console.print("[red]Nie wybrano jednostki![/]")
            else:
                console.print("[red]Nie znaleziono pasujących jednostek![/]")
        
        if not Confirm.ask("Czy chcesz kontynuować?"):
            break

if __name__ == "__main__":
    main()
