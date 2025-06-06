import os
import re
import json
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from ...infrastructure.shared.ssh_connecticer import SSHConnecticer
from ...infrastructure.shared.command_enforcer import CommandEnforcer
from ...domain.shared.profile_producer import ProfileProducer, ConnectionProfile
from ...infrastructure.command.system.systemctl_command import SystemctlCommand
from ...domain.model.command_context import CommandContext, ExecutionMode, RemoteHost


class SystemdUnit:
    """Model jednostki systemd."""
    
    def __init__(self, name: str, load_state: str = "", active_state: str = "", 
                sub_state: str = "", description: str = ""):
        """
        Inicjalizuje jednostkę systemd.
        
        Args:
            name: Nazwa jednostki
            load_state: Stan załadowania (loaded, not-found, itp.)
            active_state: Stan aktywności (active, inactive, failed, itp.)
            sub_state: Stan szczegółowy (running, dead, exited, itp.)
            description: Opis jednostki
        """
        self.name = name
        self.load_state = load_state
        self.active_state = active_state
        self.sub_state = sub_state
        self.description = description
        
        # Wnioskowanie typu jednostki z nazwy
        parts = name.split('.')
        self.unit_type = parts[-1] if len(parts) > 1 else "unknown"
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'SystemdUnit':
        """
        Tworzy jednostkę z słownika.
        
        Args:
            data: Słownik z danymi jednostki
            
        Returns:
            SystemdUnit: Nowa jednostka
        """
        return cls(
            name=data.get('unit', ''),
            load_state=data.get('load', ''),
            active_state=data.get('active', ''),
            sub_state=data.get('sub', ''),
            description=data.get('description', '')
        )
    
    def to_dict(self) -> Dict[str, str]:
        """
        Konwertuje jednostkę do słownika.
        
        Returns:
            Dict[str, str]: Słownik z danymi jednostki
        """
        return {
            'unit': self.name,
            'load': self.load_state,
            'active': self.active_state,
            'sub': self.sub_state,
            'description': self.description,
            'unit_type': self.unit_type
        }
    
    def is_active(self) -> bool:
        """
        Sprawdza czy jednostka jest aktywna.
        
        Returns:
            bool: True jeśli jednostka jest aktywna
        """
        return self.active_state == "active"
    
    def is_failed(self) -> bool:
        """
        Sprawdza czy jednostka jest w stanie błędu.
        
        Returns:
            bool: True jeśli jednostka jest w stanie błędu
        """
        return self.active_state == "failed"
    
    def is_service(self) -> bool:
        """
        Sprawdza czy jednostka jest usługą.
        
        Returns:
            bool: True jeśli jednostka jest usługą
        """
        return self.unit_type == "service"


class SystemdInspector:
    """
    Klasa do monitorowania i zarządzania usługami systemd na zdalnych serwerach.
    Korzysta z wspólnych komponentów do połączeń SSH i zarządzania profilami.
    """
    
    def __init__(self, profile_storage_dir: Optional[str] = None):
        """
        Inicjalizuje SystemdInspector.
        
        Args:
            profile_storage_dir: Katalog do przechowywania profili połączeń
        """
        self.profile_producer = ProfileProducer(profile_storage_dir)
        self.report_dir = os.path.join(os.path.expanduser("~"), ".mancer", "systemd_reports")
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Aktywne połączenie i kontekst
        self.active_connection: Optional[SSHConnecticer] = None
        self.active_profile: Optional[ConnectionProfile] = None
        self.context: Optional[CommandContext] = None
    
    def connect(self, profile_name: str) -> bool:
        """
        Nawiązuje połączenie z serwerem na podstawie profilu.
        
        Args:
            profile_name: Nazwa profilu połączenia
            
        Returns:
            bool: Czy połączenie się powiodło
        """
        # Pobierz profil
        profile = self.profile_producer.get_profile(profile_name)
        if not profile:
            return False
        
        # Utwórz połączenie
        self.active_connection = profile.create_ssh_connection()
        self.active_profile = profile
        
        # Sprawdź połączenie
        if not self.active_connection.check_connection():
            self.active_connection = None
            self.active_profile = None
            return False
        
        # Utwórz kontekst wykonania
        remote_host = RemoteHost(
            hostname=profile.hostname,
            username=profile.username,
            password=profile.password,
            port=profile.port,
            key_filename=profile.key_filename,
            passphrase=profile.passphrase
        )
        
        self.context = CommandContext(
            execution_mode=ExecutionMode.REMOTE,
            remote_host=remote_host
        )
        
        return True
    
    def disconnect(self) -> None:
        """Rozłącza aktywne połączenie."""
        self.active_connection = None
        self.active_profile = None
        self.context = None
    
    def get_all_units(self) -> List[SystemdUnit]:
        """
        Pobiera wszystkie jednostki systemd.
        
        Returns:
            List[SystemdUnit]: Lista jednostek
        """
        if not self._check_connection():
            return []
        
        # Wykonaj komendę systemctl list-units
        command = SystemctlCommand().list_units()
        
        # Dodaj obsługę retry i walidację
        enforced_command = CommandEnforcer(command) \
            .with_retry(max_retries=1) \
            .with_validator(CommandEnforcer.ensure_success_output_contains("UNIT")) \
            .with_timeout(30)
        
        # Wykonaj komendę
        result = enforced_command(self.context)
        
        # Parsuj wynik
        units = []
        if result.success and result.structured_output:
            for unit_data in result.structured_output:
                unit = SystemdUnit.from_dict(unit_data)
                units.append(unit)
        
        return units
    
    def get_unit_status(self, unit_name: str) -> Optional[SystemdUnit]:
        """
        Pobiera status jednostki.
        
        Args:
            unit_name: Nazwa jednostki
            
        Returns:
            Optional[SystemdUnit]: Status jednostki lub None
        """
        if not self._check_connection():
            return None
        
        # Wykonaj komendę systemctl status
        command = SystemctlCommand().status(unit_name)
        
        # Dodaj obsługę błędów i walidację
        enforced_command = CommandEnforcer(command) \
            .with_retry(max_retries=1)
        
        # Wykonaj komendę
        result = enforced_command(self.context)
        
        # W przypadku sukcesu zwróć jednostkę
        if result.success:
            # Pobierz wszystkie jednostki i znajdź tę z pasującą nazwą
            all_units = self.get_all_units()
            for unit in all_units:
                if unit.name == unit_name:
                    return unit
        
        return None
    
    def start_unit(self, unit_name: str) -> bool:
        """
        Uruchamia jednostkę.
        
        Args:
            unit_name: Nazwa jednostki
            
        Returns:
            bool: Czy operacja się powiodła
        """
        if not self._check_connection():
            return False
        
        # Wykonaj komendę systemctl start z sudo
        command = SystemctlCommand().start(unit_name).with_sudo()
        
        # Wykonaj komendę z retry
        enforced_command = CommandEnforcer(command).with_retry(max_retries=1)
        result = enforced_command(self.context)
        
        return result.success
    
    def stop_unit(self, unit_name: str) -> bool:
        """
        Zatrzymuje jednostkę.
        
        Args:
            unit_name: Nazwa jednostki
            
        Returns:
            bool: Czy operacja się powiodła
        """
        if not self._check_connection():
            return False
        
        # Wykonaj komendę systemctl stop z sudo
        command = SystemctlCommand().stop(unit_name).with_sudo()
        
        # Wykonaj komendę z retry
        enforced_command = CommandEnforcer(command).with_retry(max_retries=1)
        result = enforced_command(self.context)
        
        return result.success
    
    def restart_unit(self, unit_name: str) -> bool:
        """
        Restartuje jednostkę.
        
        Args:
            unit_name: Nazwa jednostki
            
        Returns:
            bool: Czy operacja się powiodła
        """
        if not self._check_connection():
            return False
        
        # Wykonaj komendę systemctl restart z sudo
        command = SystemctlCommand().restart(unit_name).with_sudo()
        
        # Wykonaj komendę z retry
        enforced_command = CommandEnforcer(command).with_retry(max_retries=1)
        result = enforced_command(self.context)
        
        return result.success
    
    def enable_unit(self, unit_name: str) -> bool:
        """
        Włącza jednostkę przy starcie systemu.
        
        Args:
            unit_name: Nazwa jednostki
            
        Returns:
            bool: Czy operacja się powiodła
        """
        if not self._check_connection():
            return False
        
        # Wykonaj komendę systemctl enable z sudo
        command = SystemctlCommand().enable(unit_name).with_sudo()
        
        # Wykonaj komendę z retry
        enforced_command = CommandEnforcer(command).with_retry(max_retries=1)
        result = enforced_command(self.context)
        
        return result.success
    
    def disable_unit(self, unit_name: str) -> bool:
        """
        Wyłącza jednostkę przy starcie systemu.
        
        Args:
            unit_name: Nazwa jednostki
            
        Returns:
            bool: Czy operacja się powiodła
        """
        if not self._check_connection():
            return False
        
        # Wykonaj komendę systemctl disable z sudo
        command = SystemctlCommand().disable(unit_name).with_sudo()
        
        # Wykonaj komendę z retry
        enforced_command = CommandEnforcer(command).with_retry(max_retries=1)
        result = enforced_command(self.context)
        
        return result.success
    
    def filter_units_by_type(self, unit_type: str) -> List[SystemdUnit]:
        """
        Filtruje jednostki według typu.
        
        Args:
            unit_type: Typ jednostki (service, socket, timer, itp.)
            
        Returns:
            List[SystemdUnit]: Lista przefiltrowanych jednostek
        """
        all_units = self.get_all_units()
        return [unit for unit in all_units if unit.unit_type == unit_type]
    
    def filter_units_by_state(self, state: str) -> List[SystemdUnit]:
        """
        Filtruje jednostki według stanu.
        
        Args:
            state: Stan jednostki (active, inactive, failed, itp.)
            
        Returns:
            List[SystemdUnit]: Lista przefiltrowanych jednostek
        """
        all_units = self.get_all_units()
        return [unit for unit in all_units if unit.active_state == state]
    
    def filter_units_by_pattern(self, pattern: str) -> List[SystemdUnit]:
        """
        Filtruje jednostki według wzorca nazwy.
        
        Args:
            pattern: Wzorzec do dopasowania w nazwie jednostki
            
        Returns:
            List[SystemdUnit]: Lista przefiltrowanych jednostek
        """
        all_units = self.get_all_units()
        return [unit for unit in all_units if re.search(pattern, unit.name)]
    
    def generate_report(self) -> str:
        """
        Generuje raport o jednostkach systemd.
        
        Returns:
            str: Ścieżka do wygenerowanego pliku raportu
        """
        if not self._check_connection():
            return ""
        
        # Pobierz wszystkie jednostki
        all_units = self.get_all_units()
        
        # Przygotuj dane do raportu
        server_name = self.active_profile.hostname
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_filename = f"systemd_report_{server_name}_{timestamp}.txt"
        report_path = os.path.join(self.report_dir, report_filename)
        
        # Statystyki
        total_units = len(all_units)
        active_units = len([u for u in all_units if u.is_active()])
        failed_units = len([u for u in all_units if u.is_failed()])
        
        # Kategoryzuj według typu
        units_by_type = {}
        for unit in all_units:
            if unit.unit_type not in units_by_type:
                units_by_type[unit.unit_type] = []
            units_by_type[unit.unit_type].append(unit)
        
        # Kategoryzuj według stanu
        units_by_state = {}
        for unit in all_units:
            if unit.active_state not in units_by_state:
                units_by_state[unit.active_state] = []
            units_by_state[unit.active_state].append(unit)
        
        # Zapisz raport
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"Raport jednostek systemd dla {server_name}\n")
            f.write(f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # Podsumowanie
            f.write("PODSUMOWANIE:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Całkowita liczba jednostek: {total_units}\n")
            f.write(f"Aktywne: {active_units}\n")
            f.write(f"Uszkodzone: {failed_units}\n\n")
            
            # Sekcja uszkodzonych jednostek
            f.write("USZKODZONE JEDNOSTKI:\n")
            f.write("-" * 20 + "\n")
            if failed_units > 0:
                for unit in units_by_state.get('failed', []):
                    f.write(f"{unit.name} - {unit.description}\n")
            else:
                f.write("Brak uszkodzonych jednostek\n")
            f.write("\n")
            
            # Podział według typu
            f.write("PODZIAŁ WEDŁUG TYPU:\n")
            f.write("-" * 20 + "\n")
            for unit_type, units in units_by_type.items():
                if units:  # Pokazuj tylko typy, które mają jakieś jednostki
                    f.write(f"\n{unit_type.upper()}:\n")
                    for unit in units:
                        state_mark = "✓" if unit.is_active() else "✗" if unit.is_failed() else "-"
                        f.write(f"{state_mark} {unit.name} - {unit.active_state}/{unit.sub_state} - {unit.description}\n")
            f.write("\n")
            
            # Podział według stanu
            f.write("PODZIAŁ WEDŁUG STANU:\n")
            f.write("-" * 20 + "\n")
            for state, units in units_by_state.items():
                if units:  # Pokazuj tylko stany, które mają jakieś jednostki
                    f.write(f"\n{state.upper()}:\n")
                    for unit in units:
                        f.write(f"{unit.name} - {unit.unit_type} - {unit.description}\n")
        
        return report_path
    
    def _check_connection(self) -> bool:
        """
        Sprawdza czy połączenie jest aktywne.
        
        Returns:
            bool: Czy połączenie jest aktywne
        """
        if not self.active_connection or not self.context:
            return False
        
        return self.active_connection.is_alive()
    
    def get_logs_for_unit(self, unit_name: str, lines: int = 50) -> str:
        """
        Pobiera logi dla jednostki.
        
        Args:
            unit_name: Nazwa jednostki
            lines: Liczba linii logów do pobrania
            
        Returns:
            str: Treść logów
        """
        if not self._check_connection():
            return ""
        
        # Wykonaj komendę journalctl dla jednostki
        command_str = f"journalctl -u {unit_name} -n {lines}"
        result = self.active_connection.execute_command(command_str)
        
        if result.success:
            return result.raw_output
        
        return "" 