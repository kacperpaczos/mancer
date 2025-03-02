import subprocess
import getpass
from datetime import datetime
import json
import os
import base64
from cryptography.fernet import Fernet

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
        'dimark': [], #TODO Kategoryzowac ponazwie,nie na sztywno.
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
    if os.path.exists('connection_profile.json'):
        try:
            with open('connection_profile.json', 'r') as f:
                profile = json.load(f)
                print("\nZnaleziono zapisany profil połączenia:")
                print(f"Host: {profile['hostname']}")
                print(f"Użytkownik: {profile['username']}")
                
                use_profile = input("\nCzy chcesz użyć tego profilu? (t/n): ").lower()
                if use_profile == 't':
                    return profile['hostname'], profile['username'], profile['password']
        except Exception as e:
            print(f"Błąd odczytu profilu: {str(e)}")
    return None, None, None

def save_profile(hostname, username, password):
    profile = {
        'hostname': hostname,
        'username': username,
        'password': password
    }
    try:
        with open('connection_profile.json', 'w') as f:
            json.dump(profile, f, indent=4)
        print("Profil połączenia został zapisany")
    except Exception as e:
        print(f"Błąd zapisu profilu: {str(e)}")

def main():
    saved_hostname, saved_username, saved_password = load_profile()
    
    if saved_hostname and saved_username and saved_password:
        hostname = saved_hostname
        username = saved_username
        password = saved_password
    else:
        hostname = input("Podaj adres hosta: ")
        username = input("Podaj nazwę użytkownika: ")
        password = getpass.getpass("Podaj hasło: ")
        save_profile(hostname, username, password)
    
    print("Łączenie z serwerem...")
    units_output = get_systemd_units(hostname, username, password)
    
    if units_output:
        units = parse_units(units_output)
        filename = save_report(hostname, units)
        print(f"\nRaport został zapisany do pliku: {filename}")

if __name__ == "__main__":
    main()
