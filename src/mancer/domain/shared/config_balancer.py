import os
import re
import json
import yaml
import configparser
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from ...infrastructure.shared.ssh_connecticer import SSHConnecticer
from ...infrastructure.shared.file_tracer import FileTracer
from .profile_producer import ConnectionProfile


class ConfigDiff:
    """Reprezentuje różnice między konfiguracjami."""
    
    def __init__(self, source_path: str, target_path: str, 
                differences: List[str], 
                is_source_remote: bool = False,
                is_target_remote: bool = False):
        """
        Inicjalizuje obiekt różnic.
        
        Args:
            source_path: Ścieżka do pliku źródłowego
            target_path: Ścieżka do pliku docelowego
            differences: Lista linii różnic
            is_source_remote: Czy źródło jest zdalne
            is_target_remote: Czy cel jest zdalny
        """
        self.source_path = source_path
        self.target_path = target_path
        self.differences = differences
        self.is_source_remote = is_source_remote
        self.is_target_remote = is_target_remote
        self.timestamp = datetime.datetime.now()
    
    def has_differences(self) -> bool:
        """
        Sprawdza czy istnieją różnice.
        
        Returns:
            bool: True jeśli są różnice
        """
        return len(self.differences) > 0
    
    def get_summary(self) -> str:
        """
        Zwraca podsumowanie różnic.
        
        Returns:
            str: Podsumowanie różnic
        """
        if not self.has_differences():
            return "Brak różnic"
        
        source_display = f"{'remote:' if self.is_source_remote else 'local:'}{self.source_path}"
        target_display = f"{'remote:' if self.is_target_remote else 'local:'}{self.target_path}"
        
        summary = f"Różnice pomiędzy {source_display} i {target_display}\n"
        summary += f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"Liczba różnic: {len(self.differences)}\n"
        summary += "-" * 40 + "\n"
        
        # Pokaż część różnic
        max_diff_to_show = min(10, len(self.differences))
        for i in range(max_diff_to_show):
            summary += f"{self.differences[i]}\n"
        
        if len(self.differences) > max_diff_to_show:
            summary += f"... i {len(self.differences) - max_diff_to_show} więcej różnic\n"
        
        return summary


class ConfigFormat:
    """Typ formatu konfiguracji."""
    INI = "ini"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    PLAIN = "plain"
    
    @staticmethod
    def detect_format(file_path: str) -> str:
        """
        Wykrywa format na podstawie rozszerzenia pliku.
        
        Args:
            file_path: Ścieżka do pliku
            
        Returns:
            str: Wykryty format
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.ini', '.conf', '.cfg']:
            return ConfigFormat.INI
        elif ext in ['.json']:
            return ConfigFormat.JSON
        elif ext in ['.yaml', '.yml']:
            return ConfigFormat.YAML
        elif ext in ['.xml']:
            return ConfigFormat.XML
        else:
            return ConfigFormat.PLAIN


class ConfigTemplate:
    """Reprezentuje szablon konfiguracji."""
    
    def __init__(self, name: str, template_content: str, 
                format_type: str, description: Optional[str] = None,
                variables: Optional[Dict[str, str]] = None):
        """
        Inicjalizuje szablon konfiguracji.
        
        Args:
            name: Nazwa szablonu
            template_content: Zawartość szablonu
            format_type: Format (ini, json, yaml, xml, plain)
            description: Opis szablonu
            variables: Słownik zmiennych do zastąpienia
        """
        self.name = name
        self.template_content = template_content
        self.format_type = format_type
        self.description = description
        self.variables = variables or {}
    
    def render(self, variables: Optional[Dict[str, str]] = None) -> str:
        """
        Renderuje szablon ze zmiennymi.
        
        Args:
            variables: Zmienne do zastąpienia (nadpisują domyślne)
            
        Returns:
            str: Wyrenderowana konfiguracja
        """
        # Połącz domyślne zmienne z podanymi
        all_vars = dict(self.variables)
        if variables:
            all_vars.update(variables)
        
        # Renderuj szablon
        content = self.template_content
        for var_name, var_value in all_vars.items():
            placeholder = f"{{{{%{var_name}%}}}}"
            content = content.replace(placeholder, str(var_value))
        
        return content


class ConfigValidator:
    """Walidator konfiguracji."""
    
    def __init__(self, name: str, format_type: str, 
                validator_func: Callable[[str], Tuple[bool, Optional[str]]],
                description: Optional[str] = None):
        """
        Inicjalizuje walidator.
        
        Args:
            name: Nazwa walidatora
            format_type: Format konfiguracji (ini, json, yaml, xml, plain)
            validator_func: Funkcja walidująca, zwraca (is_valid, error_message)
            description: Opis walidatora
        """
        self.name = name
        self.format_type = format_type
        self.validator_func = validator_func
        self.description = description
    
    def validate(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Waliduje zawartość konfiguracji.
        
        Args:
            content: Zawartość konfiguracji
            
        Returns:
            Tuple[bool, Optional[str]]: (czy poprawna, komunikat błędu)
        """
        return self.validator_func(content)


class ConfigBalancer:
    """
    Klasa do zarządzania konfiguracjami na wielu serwerach.
    Obsługuje porównywanie, synchronizację i walidację konfiguracji.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Inicjalizuje ConfigBalancer.
        
        Args:
            storage_dir: Katalog do przechowywania szablonów i historii
        """
        if storage_dir is None:
            self.storage_dir = os.path.join(os.path.expanduser("~"), ".mancer", "configs")
        else:
            self.storage_dir = storage_dir
            
        self.templates_dir = os.path.join(self.storage_dir, "templates")
        self.history_dir = os.path.join(self.storage_dir, "history")
        
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        
        self.file_tracer = FileTracer()
        self._templates: Dict[str, ConfigTemplate] = {}
        self._validators: Dict[str, ConfigValidator] = {}
        
        # Zarejestruj domyślne walidatory
        self._register_default_validators()
    
    def compare_configs(self, source_path: str, target_path: str,
                      source_ssh: Optional[SSHConnecticer] = None,
                      target_ssh: Optional[SSHConnecticer] = None) -> ConfigDiff:
        """
        Porównuje dwie konfiguracje.
        
        Args:
            source_path: Ścieżka do pliku źródłowego
            target_path: Ścieżka do pliku docelowego
            source_ssh: Opcjonalne połączenie SSH do źródła
            target_ssh: Opcjonalne połączenie SSH do celu
            
        Returns:
            ConfigDiff: Obiekt różnic
        """
        # Konfiguruj FileTracer dla źródła
        source_tracer = FileTracer(source_ssh) if source_ssh else FileTracer()
        is_source_remote = source_ssh is not None
        
        # Konfiguruj FileTracer dla celu
        target_tracer = FileTracer(target_ssh) if target_ssh else FileTracer()
        is_target_remote = target_ssh is not None
        
        # Pobierz zawartość plików
        try:
            source_content = source_tracer._get_file_content(source_path, is_source_remote)
        except Exception as e:
            return ConfigDiff(
                source_path=source_path,
                target_path=target_path,
                differences=[f"Błąd odczytu źródła: {str(e)}"],
                is_source_remote=is_source_remote,
                is_target_remote=is_target_remote
            )
        
        try:
            target_content = target_tracer._get_file_content(target_path, is_target_remote)
        except Exception as e:
            return ConfigDiff(
                source_path=source_path,
                target_path=target_path,
                differences=[f"Błąd odczytu celu: {str(e)}"],
                is_source_remote=is_source_remote,
                is_target_remote=is_target_remote
            )
        
        # Porównaj zawartość
        if source_content == target_content:
            return ConfigDiff(
                source_path=source_path,
                target_path=target_path,
                differences=[],
                is_source_remote=is_source_remote,
                is_target_remote=is_target_remote
            )
        
        # Generuj różnice
        import difflib
        differ = difflib.Differ()
        diff = list(differ.compare(source_content.splitlines(), target_content.splitlines()))
        
        return ConfigDiff(
            source_path=source_path,
            target_path=target_path,
            differences=diff,
            is_source_remote=is_source_remote,
            is_target_remote=is_target_remote
        )
    
    def sync_config(self, source_path: str, target_path: str,
                  source_ssh: Optional[SSHConnecticer] = None,
                  target_ssh: Optional[SSHConnecticer] = None,
                  make_backup: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Synchronizuje konfigurację z źródła do celu.
        
        Args:
            source_path: Ścieżka do pliku źródłowego
            target_path: Ścieżka do pliku docelowego
            source_ssh: Opcjonalne połączenie SSH do źródła
            target_ssh: Opcjonalne połączenie SSH do celu
            make_backup: Czy utworzyć backup przed synchronizacją
            
        Returns:
            Tuple[bool, Optional[str]]: (sukces, ścieżka do backupu lub komunikat błędu)
        """
        # Konfiguruj FileTracer dla źródła
        source_tracer = FileTracer(source_ssh) if source_ssh else FileTracer()
        is_source_remote = source_ssh is not None
        
        # Konfiguruj FileTracer dla celu
        target_tracer = FileTracer(target_ssh) if target_ssh else FileTracer()
        is_target_remote = target_ssh is not None
        
        # Najpierw zrób backup jeśli wymagany
        backup_path = None
        if make_backup:
            try:
                backup_path = target_tracer.backup_file(target_path, is_target_remote, "before_sync")
            except Exception as e:
                # Kontynuuj nawet jeśli backup się nie powiedzie
                pass
        
        # Pobierz zawartość pliku źródłowego
        try:
            source_content = source_tracer._get_file_content(source_path, is_source_remote)
        except Exception as e:
            return False, f"Błąd odczytu źródła: {str(e)}"
        
        # Zapisz zawartość do pliku docelowego
        try:
            success = target_tracer._set_file_content(target_path, source_content, is_target_remote)
            if not success:
                return False, "Błąd zapisu do pliku docelowego"
        except Exception as e:
            return False, f"Błąd zapisu do celu: {str(e)}"
        
        # Zapisz historię operacji
        diff = self.compare_configs(source_path, target_path, source_ssh, target_ssh)
        self._save_sync_history(diff, backup_path)
        
        return True, backup_path
    
    def add_template(self, template: ConfigTemplate) -> bool:
        """
        Dodaje szablon konfiguracji.
        
        Args:
            template: Szablon do dodania
            
        Returns:
            bool: Czy operacja się powiodła
        """
        # Dodaj do pamięci
        self._templates[template.name] = template
        
        # Zapisz do pliku
        return self._save_template(template)
    
    def get_template(self, name: str) -> Optional[ConfigTemplate]:
        """
        Pobiera szablon o określonej nazwie.
        
        Args:
            name: Nazwa szablonu
            
        Returns:
            Optional[ConfigTemplate]: Szablon lub None
        """
        # Sprawdź czy szablon jest już załadowany
        if name in self._templates:
            return self._templates[name]
        
        # Próba załadowania szablonu z pliku
        template_path = os.path.join(self.templates_dir, f"{name}.json")
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                template = ConfigTemplate(
                    name=data['name'],
                    template_content=data['content'],
                    format_type=data['format'],
                    description=data.get('description'),
                    variables=data.get('variables', {})
                )
                
                self._templates[name] = template
                return template
            except Exception:
                return None
        
        return None
    
    def list_templates(self) -> List[str]:
        """
        Listuje dostępne szablony.
        
        Returns:
            List[str]: Lista nazw szablonów
        """
        # Załaduj wszystkie szablony z katalogu
        templates = []
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                template_name = os.path.splitext(filename)[0]
                templates.append(template_name)
        
        return sorted(templates)
    
    def register_validator(self, validator: ConfigValidator) -> bool:
        """
        Rejestruje walidator konfiguracji.
        
        Args:
            validator: Walidator do zarejestrowania
            
        Returns:
            bool: Czy operacja się powiodła
        """
        self._validators[validator.name] = validator
        return True
    
    def validate_config(self, content: str, format_type: Optional[str] = None, 
                      validator_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Waliduje konfigurację.
        
        Args:
            content: Zawartość konfiguracji
            format_type: Format konfiguracji (auto-detekcja jeśli None)
            validator_name: Nazwa walidatora (domyślny dla formatu jeśli None)
            
        Returns:
            Tuple[bool, Optional[str]]: (czy poprawna, komunikat błędu)
        """
        # Wybierz walidator
        if validator_name and validator_name in self._validators:
            validator = self._validators[validator_name]
        elif format_type and f"default_{format_type}" in self._validators:
            validator = self._validators[f"default_{format_type}"]
        else:
            return False, "Brak odpowiedniego walidatora"
        
        # Wykonaj walidację
        return validator.validate(content)
    
    def _save_template(self, template: ConfigTemplate) -> bool:
        """
        Zapisuje szablon do pliku.
        
        Args:
            template: Szablon do zapisania
            
        Returns:
            bool: Czy operacja się powiodła
        """
        template_path = os.path.join(self.templates_dir, f"{template.name}.json")
        
        try:
            data = {
                'name': template.name,
                'content': template.template_content,
                'format': template.format_type,
                'description': template.description,
                'variables': template.variables
            }
            
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def _save_sync_history(self, diff: ConfigDiff, backup_path: Optional[str] = None) -> bool:
        """
        Zapisuje historię synchronizacji.
        
        Args:
            diff: Obiekt różnic
            backup_path: Opcjonalna ścieżka do backupu
            
        Returns:
            bool: Czy operacja się powiodła
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        history_path = os.path.join(self.history_dir, f"sync_{timestamp}.json")
        
        try:
            data = {
                'timestamp': timestamp,
                'source_path': diff.source_path,
                'target_path': diff.target_path,
                'is_source_remote': diff.is_source_remote,
                'is_target_remote': diff.is_target_remote,
                'has_differences': diff.has_differences(),
                'differences_count': len(diff.differences),
                'backup_path': backup_path
            }
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def _register_default_validators(self) -> None:
        """Rejestruje domyślne walidatory dla różnych formatów."""
        
        # Walidator dla INI
        def validate_ini(content: str) -> Tuple[bool, Optional[str]]:
            try:
                config = configparser.ConfigParser()
                config.read_string(content)
                return True, None
            except Exception as e:
                return False, f"Błąd walidacji INI: {str(e)}"
        
        # Walidator dla JSON
        def validate_json(content: str) -> Tuple[bool, Optional[str]]:
            try:
                json.loads(content)
                return True, None
            except Exception as e:
                return False, f"Błąd walidacji JSON: {str(e)}"
        
        # Walidator dla YAML
        def validate_yaml(content: str) -> Tuple[bool, Optional[str]]:
            try:
                yaml.safe_load(content)
                return True, None
            except Exception as e:
                return False, f"Błąd walidacji YAML: {str(e)}"
        
        # Rejestracja walidatorów
        self.register_validator(ConfigValidator(
            name="default_ini",
            format_type=ConfigFormat.INI,
            validator_func=validate_ini,
            description="Domyślny walidator dla plików INI"
        ))
        
        self.register_validator(ConfigValidator(
            name="default_json",
            format_type=ConfigFormat.JSON,
            validator_func=validate_json,
            description="Domyślny walidator dla plików JSON"
        ))
        
        self.register_validator(ConfigValidator(
            name="default_yaml",
            format_type=ConfigFormat.YAML,
            validator_func=validate_yaml,
            description="Domyślny walidator dla plików YAML"
        )) 