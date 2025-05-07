import os
import re
import json
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from ...infrastructure.shared.ssh_connecticer import SSHConnecticer
from ...infrastructure.shared.file_tracer import FileTracer
from ...domain.shared.profile_producer import ProfileProducer, ConnectionProfile
from ...domain.shared.config_balancer import (
    ConfigBalancer, ConfigTemplate, ConfigDiff, ConfigFormat, ConfigValidator
)


class ConfigSyncTask:
    """Reprezentuje zadanie synchronizacji konfiguracji."""
    
    def __init__(self, name: str, source_profile: str, source_path: str,
                target_profiles: List[str], target_path: str,
                description: Optional[str] = None,
                validate_before_sync: bool = True):
        """
        Inicjalizuje zadanie synchronizacji.
        
        Args:
            name: Nazwa zadania
            source_profile: Nazwa profilu źródłowego
            source_path: Ścieżka do pliku źródłowego
            target_profiles: Lista profili docelowych
            target_path: Ścieżka do pliku docelowego
            description: Opis zadania
            validate_before_sync: Czy walidować przed synchronizacją
        """
        self.name = name
        self.source_profile = source_profile
        self.source_path = source_path
        self.target_profiles = target_profiles
        self.target_path = target_path
        self.description = description
        self.validate_before_sync = validate_before_sync
        self.created_at = datetime.datetime.now()
        self.last_run = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje zadanie do słownika.
        
        Returns:
            Dict[str, Any]: Słownik z danymi zadania
        """
        return {
            'name': self.name,
            'source_profile': self.source_profile,
            'source_path': self.source_path,
            'target_profiles': self.target_profiles,
            'target_path': self.target_path,
            'description': self.description,
            'validate_before_sync': self.validate_before_sync,
            'created_at': self.created_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigSyncTask':
        """
        Tworzy zadanie z słownika.
        
        Args:
            data: Słownik z danymi zadania
            
        Returns:
            ConfigSyncTask: Utworzone zadanie
        """
        task = cls(
            name=data['name'],
            source_profile=data['source_profile'],
            source_path=data['source_path'],
            target_profiles=data['target_profiles'],
            target_path=data['target_path'],
            description=data.get('description'),
            validate_before_sync=data.get('validate_before_sync', True)
        )
        
        if data.get('created_at'):
            task.created_at = datetime.datetime.fromisoformat(data['created_at'])
        
        if data.get('last_run'):
            task.last_run = datetime.datetime.fromisoformat(data['last_run'])
        
        return task


class SyncResult:
    """Reprezentuje wynik synchronizacji."""
    
    def __init__(self, task_name: str, target_profile: str, success: bool,
                error_message: Optional[str] = None,
                backup_path: Optional[str] = None):
        """
        Inicjalizuje wynik synchronizacji.
        
        Args:
            task_name: Nazwa zadania
            target_profile: Nazwa profilu docelowego
            success: Czy synchronizacja się powiodła
            error_message: Komunikat błędu
            backup_path: Ścieżka do backupu
        """
        self.task_name = task_name
        self.target_profile = target_profile
        self.success = success
        self.error_message = error_message
        self.backup_path = backup_path
        self.timestamp = datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje wynik do słownika.
        
        Returns:
            Dict[str, Any]: Słownik z danymi wyniku
        """
        return {
            'task_name': self.task_name,
            'target_profile': self.target_profile,
            'success': self.success,
            'error_message': self.error_message,
            'backup_path': self.backup_path,
            'timestamp': self.timestamp.isoformat()
        }


class RemoteConfigManager:
    """
    Klasa do zarządzania konfiguracjami na zdalnych serwerach.
    Korzysta z wspólnych komponentów do połączeń SSH, zarządzania profilami
    i operacji na plikach.
    """
    
    def __init__(self, profile_storage_dir: Optional[str] = None,
                config_storage_dir: Optional[str] = None):
        """
        Inicjalizuje RemoteConfigManager.
        
        Args:
            profile_storage_dir: Katalog do przechowywania profili połączeń
            config_storage_dir: Katalog do przechowywania konfiguracji
        """
        self.profile_producer = ProfileProducer(profile_storage_dir)
        self.config_balancer = ConfigBalancer(config_storage_dir)
        
        # Katalog na zadania synchronizacji
        self.tasks_dir = os.path.join(os.path.expanduser("~"), ".mancer", "config_tasks")
        os.makedirs(self.tasks_dir, exist_ok=True)
        
        # Katalog na wyniki synchronizacji
        self.results_dir = os.path.join(os.path.expanduser("~"), ".mancer", "config_results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Aktywne połączenia
        self.connections: Dict[str, SSHConnecticer] = {}
        
        # Załaduj istniejące zadania
        self._tasks: Dict[str, ConfigSyncTask] = {}
        self._load_tasks()
    
    def connect(self, profile_name: str) -> bool:
        """
        Nawiązuje połączenie z serwerem na podstawie profilu.
        
        Args:
            profile_name: Nazwa profilu połączenia
            
        Returns:
            bool: Czy połączenie się powiodło
        """
        # Sprawdź czy już połączono
        if profile_name in self.connections:
            return self.connections[profile_name].is_alive()
        
        # Pobierz profil
        profile = self.profile_producer.get_profile(profile_name)
        if not profile:
            return False
        
        # Utwórz połączenie
        connection = profile.create_ssh_connection()
        
        # Sprawdź połączenie
        if not connection.check_connection():
            return False
        
        # Zapisz połączenie
        self.connections[profile_name] = connection
        
        return True
    
    def disconnect(self, profile_name: Optional[str] = None) -> None:
        """
        Rozłącza połączenie.
        
        Args:
            profile_name: Nazwa profilu do rozłączenia (None = wszystkie)
        """
        if profile_name:
            # Rozłącz konkretne połączenie
            if profile_name in self.connections:
                del self.connections[profile_name]
        else:
            # Rozłącz wszystkie połączenia
            self.connections.clear()
    
    def get_remote_file_content(self, profile_name: str, file_path: str) -> Optional[str]:
        """
        Pobiera zawartość pliku ze zdalnego serwera.
        
        Args:
            profile_name: Nazwa profilu połączenia
            file_path: Ścieżka do pliku
            
        Returns:
            Optional[str]: Zawartość pliku lub None
        """
        # Upewnij się, że jest połączenie
        if not self._ensure_connection(profile_name):
            return None
        
        # Pobierz zawartość
        file_tracer = FileTracer(self.connections[profile_name])
        try:
            return file_tracer._get_file_content(file_path, is_remote=True)
        except Exception:
            return None
    
    def save_remote_file(self, profile_name: str, file_path: str, content: str) -> bool:
        """
        Zapisuje zawartość do pliku na zdalnym serwerze.
        
        Args:
            profile_name: Nazwa profilu połączenia
            file_path: Ścieżka do pliku
            content: Zawartość do zapisania
            
        Returns:
            bool: Czy operacja się powiodła
        """
        # Upewnij się, że jest połączenie
        if not self._ensure_connection(profile_name):
            return False
        
        # Zapisz zawartość
        file_tracer = FileTracer(self.connections[profile_name])
        return file_tracer._set_file_content(file_path, content, is_remote=True)
    
    def compare_config_files(self, source_profile: str, source_path: str,
                          target_profile: str, target_path: str) -> ConfigDiff:
        """
        Porównuje pliki konfiguracyjne.
        
        Args:
            source_profile: Nazwa profilu źródłowego
            source_path: Ścieżka do pliku źródłowego
            target_profile: Nazwa profilu docelowego
            target_path: Ścieżka do pliku docelowego
            
        Returns:
            ConfigDiff: Różnice między plikami
        """
        # Upewnij się, że są połączenia
        if not self._ensure_connection(source_profile) or not self._ensure_connection(target_profile):
            return ConfigDiff(
                source_path=source_path,
                target_path=target_path,
                differences=["Błąd połączenia z jednym z serwerów"],
                is_source_remote=True,
                is_target_remote=True
            )
        
        # Porównaj pliki
        return self.config_balancer.compare_configs(
            source_path=source_path,
            target_path=target_path,
            source_ssh=self.connections[source_profile],
            target_ssh=self.connections[target_profile]
        )
    
    def sync_config_file(self, source_profile: str, source_path: str,
                       target_profile: str, target_path: str,
                       make_backup: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Synchronizuje plik konfiguracyjny z źródła do celu.
        
        Args:
            source_profile: Nazwa profilu źródłowego
            source_path: Ścieżka do pliku źródłowego
            target_profile: Nazwa profilu docelowego
            target_path: Ścieżka do pliku docelowego
            make_backup: Czy utworzyć backup przed synchronizacją
            
        Returns:
            Tuple[bool, Optional[str]]: (sukces, ścieżka do backupu lub komunikat błędu)
        """
        # Upewnij się, że są połączenia
        if not self._ensure_connection(source_profile) or not self._ensure_connection(target_profile):
            return False, "Błąd połączenia z jednym z serwerów"
        
        # Synchronizuj plik
        return self.config_balancer.sync_config(
            source_path=source_path,
            target_path=target_path,
            source_ssh=self.connections[source_profile],
            target_ssh=self.connections[target_profile],
            make_backup=make_backup
        )
    
    def add_sync_task(self, task: ConfigSyncTask) -> bool:
        """
        Dodaje zadanie synchronizacji.
        
        Args:
            task: Zadanie do dodania
            
        Returns:
            bool: Czy operacja się powiodła
        """
        # Sprawdź czy zadanie o takiej nazwie już istnieje
        if task.name in self._tasks:
            return False
        
        # Dodaj zadanie
        self._tasks[task.name] = task
        
        # Zapisz zadanie
        return self._save_task(task)
    
    def update_sync_task(self, task: ConfigSyncTask) -> bool:
        """
        Aktualizuje zadanie synchronizacji.
        
        Args:
            task: Zadanie do aktualizacji
            
        Returns:
            bool: Czy operacja się powiodła
        """
        # Aktualizuj zadanie
        self._tasks[task.name] = task
        
        # Zapisz zadanie
        return self._save_task(task)
    
    def get_sync_task(self, name: str) -> Optional[ConfigSyncTask]:
        """
        Pobiera zadanie synchronizacji.
        
        Args:
            name: Nazwa zadania
            
        Returns:
            Optional[ConfigSyncTask]: Zadanie lub None
        """
        return self._tasks.get(name)
    
    def delete_sync_task(self, name: str) -> bool:
        """
        Usuwa zadanie synchronizacji.
        
        Args:
            name: Nazwa zadania
            
        Returns:
            bool: Czy operacja się powiodła
        """
        # Usuń zadanie z pamięci
        if name in self._tasks:
            del self._tasks[name]
        
        # Usuń plik zadania
        task_path = os.path.join(self.tasks_dir, f"{name}.json")
        if os.path.exists(task_path):
            try:
                os.remove(task_path)
                return True
            except OSError:
                return False
        
        return False
    
    def list_sync_tasks(self) -> List[ConfigSyncTask]:
        """
        Listuje zadania synchronizacji.
        
        Returns:
            List[ConfigSyncTask]: Lista zadań
        """
        return list(self._tasks.values())
    
    def run_sync_task(self, task_name: str) -> List[SyncResult]:
        """
        Wykonuje zadanie synchronizacji.
        
        Args:
            task_name: Nazwa zadania
            
        Returns:
            List[SyncResult]: Lista wyników synchronizacji
        """
        # Pobierz zadanie
        task = self.get_sync_task(task_name)
        if not task:
            return []
        
        results = []
        
        # Uzyskaj połączenie do źródła
        if not self._ensure_connection(task.source_profile):
            # Nie udało się połączyć do źródła, więc nie ma co synchronizować
            for target_profile in task.target_profiles:
                results.append(SyncResult(
                    task_name=task.name,
                    target_profile=target_profile,
                    success=False,
                    error_message=f"Błąd połączenia ze źródłem: {task.source_profile}"
                ))
            return results
        
        # Pobierz zawartość pliku źródłowego
        source_content = self.get_remote_file_content(task.source_profile, task.source_path)
        if not source_content:
            # Nie udało się odczytać źródła
            for target_profile in task.target_profiles:
                results.append(SyncResult(
                    task_name=task.name,
                    target_profile=target_profile,
                    success=False,
                    error_message=f"Błąd odczytu pliku źródłowego: {task.source_path}"
                ))
            return results
        
        # Waliduj zawartość jeśli wymagane
        if task.validate_before_sync:
            format_type = ConfigFormat.detect_format(task.source_path)
            is_valid, error = self.config_balancer.validate_config(source_content, format_type)
            if not is_valid:
                # Walidacja nie powiodła się
                for target_profile in task.target_profiles:
                    results.append(SyncResult(
                        task_name=task.name,
                        target_profile=target_profile,
                        success=False,
                        error_message=f"Walidacja konfiguracji nie powiodła się: {error}"
                    ))
                return results
        
        # Synchronizuj do każdego celu
        for target_profile in task.target_profiles:
            # Uzyskaj połączenie do celu
            if not self._ensure_connection(target_profile):
                results.append(SyncResult(
                    task_name=task.name,
                    target_profile=target_profile,
                    success=False,
                    error_message=f"Błąd połączenia z celem: {target_profile}"
                ))
                continue
            
            # Wykonaj synchronizację
            success, result = self.sync_config_file(
                source_profile=task.source_profile,
                source_path=task.source_path,
                target_profile=target_profile,
                target_path=task.target_path
            )
            
            # Zapisz wynik
            if success:
                results.append(SyncResult(
                    task_name=task.name,
                    target_profile=target_profile,
                    success=True,
                    backup_path=result
                ))
            else:
                results.append(SyncResult(
                    task_name=task.name,
                    target_profile=target_profile,
                    success=False,
                    error_message=result
                ))
        
        # Zaktualizuj czas ostatniego uruchomienia
        task.last_run = datetime.datetime.now()
        self.update_sync_task(task)
        
        # Zapisz wyniki
        self._save_sync_results(task.name, results)
        
        return results
    
    def create_template_from_file(self, profile_name: str, file_path: str,
                               template_name: str, description: Optional[str] = None,
                               variables: Optional[Dict[str, str]] = None) -> bool:
        """
        Tworzy szablon z pliku.
        
        Args:
            profile_name: Nazwa profilu połączenia
            file_path: Ścieżka do pliku
            template_name: Nazwa szablonu
            description: Opis szablonu
            variables: Zmienne do zastąpienia w szablonie
            
        Returns:
            bool: Czy operacja się powiodła
        """
        # Pobierz zawartość pliku
        content = self.get_remote_file_content(profile_name, file_path)
        if not content:
            return False
        
        # Wykryj format
        format_type = ConfigFormat.detect_format(file_path)
        
        # Tworzenie szablonu - zastąp wartości zmiennych placeholderami
        if variables:
            for var_name, var_value in variables.items():
                content = content.replace(var_value, f"{{{{%{var_name}%}}}}")
        
        # Utwórz i dodaj szablon
        template = ConfigTemplate(
            name=template_name,
            template_content=content,
            format_type=format_type,
            description=description,
            variables=variables
        )
        
        return self.config_balancer.add_template(template)
    
    def apply_template(self, template_name: str, profile_name: str, target_path: str,
                     variables: Optional[Dict[str, str]] = None) -> bool:
        """
        Zastosowuje szablon na zdalnym serwerze.
        
        Args:
            template_name: Nazwa szablonu
            profile_name: Nazwa profilu połączenia
            target_path: Ścieżka docelowa
            variables: Zmienne do podstawienia
            
        Returns:
            bool: Czy operacja się powiodła
        """
        # Pobierz szablon
        template = self.config_balancer.get_template(template_name)
        if not template:
            return False
        
        # Renderuj szablon
        content = template.render(variables)
        
        # Zapisz na serwerze
        return self.save_remote_file(profile_name, target_path, content)
    
    def _ensure_connection(self, profile_name: str) -> bool:
        """
        Upewnia się, że połączenie jest aktywne.
        
        Args:
            profile_name: Nazwa profilu połączenia
            
        Returns:
            bool: Czy połączenie jest aktywne
        """
        # Sprawdź czy już połączono
        if profile_name in self.connections:
            # Sprawdź czy połączenie jest aktywne
            if self.connections[profile_name].is_alive():
                return True
            # Jeśli nie, usuń nieaktywne połączenie
            del self.connections[profile_name]
        
        # Nawiąż nowe połączenie
        return self.connect(profile_name)
    
    def _save_task(self, task: ConfigSyncTask) -> bool:
        """
        Zapisuje zadanie do pliku.
        
        Args:
            task: Zadanie do zapisania
            
        Returns:
            bool: Czy operacja się powiodła
        """
        task_path = os.path.join(self.tasks_dir, f"{task.name}.json")
        
        try:
            with open(task_path, 'w', encoding='utf-8') as f:
                json.dump(task.to_dict(), f, indent=2)
            
            return True
        except Exception:
            return False
    
    def _load_tasks(self) -> None:
        """Ładuje zadania z plików."""
        for filename in os.listdir(self.tasks_dir):
            if filename.endswith('.json'):
                task_path = os.path.join(self.tasks_dir, filename)
                
                try:
                    with open(task_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    task = ConfigSyncTask.from_dict(data)
                    self._tasks[task.name] = task
                except Exception:
                    continue
    
    def _save_sync_results(self, task_name: str, results: List[SyncResult]) -> bool:
        """
        Zapisuje wyniki synchronizacji.
        
        Args:
            task_name: Nazwa zadania
            results: Lista wyników
            
        Returns:
            bool: Czy operacja się powiodła
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_path = os.path.join(self.results_dir, f"{task_name}_{timestamp}.json")
        
        try:
            data = {
                'task_name': task_name,
                'timestamp': timestamp,
                'results': [result.to_dict() for result in results]
            }
            
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False 