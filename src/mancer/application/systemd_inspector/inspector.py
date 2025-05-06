import subprocess
import getpass
from datetime import datetime
import json
import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Dict, List, Optional, Tuple, Any

class SystemdInspector:
    """
    Klasa do monitorowania i raportowania stanu jednostek systemd na zdalnych serwerach.
    Umożliwia pobieranie, analizowanie i generowanie raportów o jednostkach systemd.
    """

    def __init__(self, config_dir: str = None):
        """
        Inicjalizuje inspektor z określonym katalogiem konfiguracji.
        
        Args:
            config_dir: Ścieżka katalogu do przechowywania profili połączeń i konfiguracji
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".systemd_inspector"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.config_dir / "connection_profiles.json"

    def get_encryption_key(self) -> bytes:
        """
        Pobiera klucz szyfrowania do zabezpieczania haseł.
        
        Returns:
            Klucz szyfrowania w formacie bajtowym
        """
        # Używamy stałego klucza dla uproszczenia (w produkcji należy użyć bezpieczniejszego rozwiązania)
        key = b'TluxwB3fV_GWuLkR1_BzGs1Zk90TYAuhNMZP_0q4WyM='
        return base64.urlsafe_b64decode(key)

    def encrypt_password(self, password: str) -> Optional[str]:
        """
        Szyfruje hasło użytkownika.
        
        Args:
            password: Hasło do zaszyfrowania
            
        Returns:
            Zaszyfrowane hasło lub None w przypadku błędu
        """
        try:
            f = Fernet(self.get_encryption_key())
            return f.encrypt(password.encode()).decode()
        except Exception as e:
            print(f"Błąd szyfrowania hasła: {str(e)}")
            return None

    def decrypt_password(self, encrypted_password: str) -> Optional[str]:
        """
        Deszyfruje hasło użytkownika.
        
        Args:
            encrypted_password: Zaszyfrowane hasło
            
        Returns:
            Odszyfrowane hasło lub None w przypadku błędu
        """
        try:
            f = Fernet(self.get_encryption_key())
            return f.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            print(f"Błąd deszyfrowania hasła: {str(e)}")
            return None

    def get_systemd_units(self, hostname: str, username: str, password: Optional[str] = None) -> Optional[str]:
        """
        Pobiera listę jednostek systemd z serwera.
        
        Args:
            hostname: Adres serwera
            username: Nazwa użytkownika
            password: Hasło użytkownika (opcjonalnie)
            
        Returns:
            Surowy tekst z listą jednostek systemd lub None w przypadku błędu
        """
        try:
            # Tworzymy unikalną nazwę pliku tymczasowego
            temp_filename = f"systemd_units_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            remote_temp_file = f"/tmp/{temp_filename}"
            local_temp_file = self.config_dir / temp_filename
            
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
                scp_cmd = f"sshpass -p '{password}' scp {username}@{hostname}:{remote_temp_file} {local_temp_file}"
            else:
                scp_cmd = f"scp {username}@{hostname}:{remote_temp_file} {local_temp_file}"
            
            subprocess.run(scp_cmd, shell=True, check=True)
            
            # Usuń plik tymczasowy na zdalnym serwerze
            if password:
                cleanup_cmd = f"sshpass -p '{password}' ssh {username}@{hostname} 'rm {remote_temp_file}'"
            else:
                cleanup_cmd = f"ssh {username}@{hostname} 'rm {remote_temp_file}'"
            
            subprocess.run(cleanup_cmd, shell=True, check=True)
            
            # Odczytaj zawartość pliku lokalnego
            with open(local_temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Usuń lokalny plik tymczasowy
            os.remove(local_temp_file)
            
            return content
            
        except subprocess.CalledProcessError as e:
            print(f"Błąd wykonania polecenia: {e}")
            return None
        except Exception as e:
            print(f"Wystąpił błąd: {str(e)}")
            return None

    def parse_units(self, units_output: str) -> Dict[str, Any]:
        """
        Parsuje surowy tekst z listą jednostek systemd.
        
        Args:
            units_output: Surowy tekst z listą jednostek systemd
            
        Returns:
            Słownik z rozparsowanymi jednostkami systemd
        """
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
            'custom_groups': {
                'dimark': [],  # Jednostki specyficzne dla projektu
                'user': []     # Jednostki użytkownika
            }
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
                    units['custom_groups']['dimark'].append(unit_info)
                
                # Sprawdź czy to jednostka użytkownika
                if '@' in unit_name or 'user' in unit_name:
                    units['custom_groups']['user'].append(unit_info)
            
            # Zakończ parsowanie gdy napotkamy podsumowanie
            elif 'loaded units listed' in line.lower():
                break
        
        return units

    def save_report(self, hostname: str, units: Dict[str, Any], output_dir: Optional[str] = None) -> str:
        """
        Zapisuje raport o jednostkach systemd do pliku.
        
        Args:
            hostname: Nazwa serwera
            units: Słownik z jednostkami systemd
            output_dir: Katalog wyjściowy (opcjonalnie)
            
        Returns:
            Ścieżka do zapisanego pliku
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"systemd_inspector_report_{hostname}_{timestamp}.txt"
        
        output_path = Path(output_dir) if output_dir else Path.cwd()
        output_path.mkdir(parents=True, exist_ok=True)
        
        full_path = output_path / filename
        
        with open(full_path, 'w', encoding='utf-8') as f:
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
            if units['custom_groups']['dimark']:
                for unit in units['custom_groups']['dimark']:
                    f.write(f"{unit}\n")
            else:
                f.write("Brak jednostek dimark\n")
            f.write("\n")
            
            # Sekcja jednostek użytkownika
            f.write("JEDNOSTKI UŻYTKOWNIKA:\n")
            f.write("-" * 20 + "\n")
            if units['custom_groups']['user']:
                for unit in units['custom_groups']['user']:
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
        
        return str(full_path)

    def load_profile(self, profile_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Wczytuje profil połączenia z pliku.
        
        Args:
            profile_name: Nazwa profilu (opcjonalnie)
            
        Returns:
            Krotka (hostname, username, password) lub (None, None, None) w przypadku błędu
        """
        if not self.profile_path.exists():
            return None, None, None
            
        try:
            with open(self.profile_path, 'r') as f:
                profiles = json.load(f)
                
            if profile_name and profile_name in profiles:
                profile = profiles[profile_name]
                password = self.decrypt_password(profile['password']) if profile['password'] else None
                return profile['hostname'], profile['username'], password
                
            if profile_name is None and profiles:
                # Zwróć pierwszy profil, jeśli nie podano nazwy
                first_profile_name = next(iter(profiles))
                profile = profiles[first_profile_name]
                password = self.decrypt_password(profile['password']) if profile['password'] else None
                return profile['hostname'], profile['username'], password
                
        except Exception as e:
            print(f"Błąd odczytu profilu: {str(e)}")
            
        return None, None, None

    def save_profile(self, profile_name: str, hostname: str, username: str, password: Optional[str] = None) -> bool:
        """
        Zapisuje profil połączenia do pliku.
        
        Args:
            profile_name: Nazwa profilu
            hostname: Adres serwera
            username: Nazwa użytkownika
            password: Hasło użytkownika (opcjonalnie)
            
        Returns:
            True jeśli zapis się powiódł, False w przeciwnym przypadku
        """
        profiles = {}
        if self.profile_path.exists():
            try:
                with open(self.profile_path, 'r') as f:
                    profiles = json.load(f)
            except Exception:
                # Jeśli plik istnieje, ale nie można go odczytać, tworzymy nowy
                pass
                
        encrypted_password = self.encrypt_password(password) if password else None
        
        profiles[profile_name] = {
            'hostname': hostname,
            'username': username,
            'password': encrypted_password
        }
            
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(profiles, f, indent=4)
            return True
        except Exception as e:
            print(f"Błąd zapisu profilu: {str(e)}")
            return False

    def list_profiles(self) -> List[str]:
        """
        Zwraca listę dostępnych profili połączeń.
        
        Returns:
            Lista nazw profili
        """
        if not self.profile_path.exists():
            return []
            
        try:
            with open(self.profile_path, 'r') as f:
                profiles = json.load(f)
            return list(profiles.keys())
        except Exception:
            return []

    def delete_profile(self, profile_name: str) -> bool:
        """
        Usuwa profil połączenia.
        
        Args:
            profile_name: Nazwa profilu do usunięcia
            
        Returns:
            True jeśli usunięcie się powiodło, False w przeciwnym przypadku
        """
        if not self.profile_path.exists():
            return False
            
        try:
            with open(self.profile_path, 'r') as f:
                profiles = json.load(f)
                
            if profile_name in profiles:
                del profiles[profile_name]
                
                with open(self.profile_path, 'w') as f:
                    json.dump(profiles, f, indent=4)
                return True
            return False
        except Exception:
            return False 