from typing import Dict, Any, Optional, List, Union
from ..domain.model.command_context import CommandContext, ExecutionMode, RemoteHostInfo
from ..domain.model.command_result import CommandResult
from ..domain.interface.command_interface import CommandInterface
from ..domain.service.command_chain_service import CommandChain
from ..infrastructure.factory.command_factory import CommandFactory
from ..infrastructure.backend.bash_backend import BashBackend
from ..infrastructure.backend.ssh_backend import SshBackend
from .command_cache import CommandCache
import uuid
import hashlib

# Definicje typów komend w różnych językach
COMMAND_TYPES_TRANSLATION = {
    "pl": {
        "ls": "Lista plików",
        "ps": "Procesy systemowe",
        "hostname": "Nazwa hosta",
        "netstat": "Status sieci",
        "systemctl": "Kontrola usług",
        "df": "Użycie dysku",
        "echo": "Wyświetlanie tekstu",
        "cat": "Wyświetlanie pliku",
        "grep": "Wyszukiwanie wzorca",
        "tail": "Koniec pliku",
        "head": "Początek pliku",
        "find": "Wyszukiwanie plików",
        "cp": "Kopiowanie plików",
        "mv": "Przenoszenie plików",
        "rm": "Usuwanie plików",
        "mkdir": "Tworzenie katalogów",
        "chmod": "Zmiana uprawnień",
        "chown": "Zmiana właściciela",
        "tar": "Archiwizacja",
        "zip": "Kompresja",
        "unzip": "Dekompresja",
        "ssh": "Połączenie SSH",
        "scp": "Kopiowanie przez SSH",
        "wget": "Pobieranie plików",
        "curl": "Klient HTTP",
        "apt": "Zarządzanie pakietami",
        "yum": "Zarządzanie pakietami",
        "dnf": "Zarządzanie pakietami",
        "ping": "Test połączenia",
        "traceroute": "Śledzenie trasy",
        "ifconfig": "Konfiguracja sieci",
        "ip": "Zarządzanie IP"
    },
    "en": {
        "ls": "File listing",
        "ps": "Process status",
        "hostname": "Host name",
        "netstat": "Network status",
        "systemctl": "Service control",
        "df": "Disk usage",
        "echo": "Text display",
        "cat": "File display",
        "grep": "Pattern search",
        "tail": "File end",
        "head": "File beginning",
        "find": "File search",
        "cp": "Copy files",
        "mv": "Move files",
        "rm": "Remove files",
        "mkdir": "Create directories",
        "chmod": "Change permissions",
        "chown": "Change owner",
        "tar": "Archive",
        "zip": "Compress",
        "unzip": "Decompress",
        "ssh": "SSH connection",
        "scp": "SSH copy",
        "wget": "Download files",
        "curl": "HTTP client",
        "apt": "Package management",
        "yum": "Package management",
        "dnf": "Package management",
        "ping": "Connection test",
        "traceroute": "Trace route",
        "ifconfig": "Network configuration",
        "ip": "IP management"
    }
}

class ShellRunner:
    """Główna klasa aplikacji do uruchamiania komend"""
    
    def __init__(self, backend_type: str = "bash", working_dir: str = ".", 
                enable_cache: bool = False, cache_max_size: int = 100,
                cache_auto_refresh: bool = False, cache_refresh_interval: int = 5,
                language: str = "pl"):
        self.backend_type = backend_type
        self.factory = CommandFactory(backend_type)
        self.context = CommandContext(current_directory=working_dir)
        self.local_backend = BashBackend()
        self.remote_backend = None
        self.language = language
        
        # Inicjalizacja cache'a
        self._cache_enabled = enable_cache
        self._command_cache = CommandCache(
            max_size=cache_max_size,
            auto_refresh=cache_auto_refresh,
            refresh_interval=cache_refresh_interval
        ) if enable_cache else None
    
    def create_command(self, command_name: str) -> CommandInterface:
        """Tworzy nową instancję komendy"""
        return self.factory.create_command(command_name)
    
    def execute(self, command: CommandInterface, 
               context_params: Optional[Dict[str, Any]] = None,
               cache_id: Optional[str] = None) -> CommandResult:
        """Wykonuje pojedynczą komendę lub łańcuch komend"""
        # Kopiujemy kontekst, aby nie modyfikować globalnego
        context = self._prepare_context(context_params)
        
        # Generujemy unikalny identyfikator komendy, jeśli nie podano
        if self._cache_enabled and cache_id is None:
            cache_id = self._generate_command_id(command, context)
            
            # Sprawdzamy, czy wynik jest w cache'u
            cached_result = self._command_cache.get(cache_id)
            if cached_result:
                return cached_result
        
        # Wykonujemy komendę
        result = None
        if isinstance(command, CommandChain):
            result = command.execute(context)
        else:
            result = command.execute(context)
            
        # Zapisujemy wynik w cache'u, jeśli cache jest włączony
        if self._cache_enabled and result:
            command_str = str(command)
            
            # Pobieramy typ komendy (nazwę klasy lub nazwę komendy)
            command_type = command.__class__.__name__
            if hasattr(command, 'name'):
                command_type = command.name
                
            # Pobieramy pełne polecenie
            command_string = command.build_command() if hasattr(command, 'build_command') else str(command)
            
            metadata = {
                'context': {
                    'current_directory': context.current_directory,
                    'execution_mode': str(context.execution_mode),
                    'remote_host': str(context.remote_host) if context.remote_host else None
                },
                'params': context_params,
                'command_type': command_type,
                'command_string': command_string
            }
            self._command_cache.store(cache_id, command_str, result, metadata)
            
        return result
    
    def register_command(self, alias: str, command: CommandInterface) -> None:
        """Rejestruje prekonfigurowaną komendę pod aliasem"""
        self.factory.register_command(alias, command)
    
    def get_command(self, alias: str) -> CommandInterface:
        """Pobiera prekonfigurowaną komendę według aliasu"""
        return self.factory.get_command(alias)
    
    def _prepare_context(self, context_params: Optional[Dict[str, Any]] = None) -> CommandContext:
        """Przygotowuje kontekst wykonania komendy"""
        # Tworzymy kopię głównego kontekstu
        context = CommandContext(
            current_directory=self.context.current_directory,
            environment_variables=self.context.environment_variables.copy(),
            execution_mode=self.context.execution_mode,
            remote_host=self.context.remote_host
        )
        
        # Dodajemy parametry kontekstu, jeśli są
        if context_params:
            for key, value in context_params.items():
                context.set_parameter(key, value)
                
        return context
    
    def _generate_command_id(self, command: CommandInterface, context: CommandContext) -> str:
        """Generuje unikalny identyfikator komendy na podstawie jej parametrów i kontekstu"""
        # Tworzymy hash na podstawie reprezentacji tekstowej komendy i kontekstu
        command_str = str(command)
        context_str = f"{context.current_directory}:{context.execution_mode}"
        if context.remote_host:
            context_str += f":{context.remote_host.host}:{context.remote_host.user}"
            
        hash_input = f"{command_str}:{context_str}:{uuid.uuid4()}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def set_remote_execution(self, host: str, user: Optional[str] = None, 
                           port: int = 22, key_file: Optional[str] = None,
                           password: Optional[str] = None, use_sudo: bool = False,
                           sudo_password: Optional[str] = None, use_agent: bool = False,
                           certificate_file: Optional[str] = None, identity_only: bool = False,
                           gssapi_auth: bool = False, gssapi_keyex: bool = False,
                           gssapi_delegate_creds: bool = False,
                           ssh_options: Optional[Dict[str, str]] = None) -> None:
        """Ustawia tryb wykonania zdalnego
        
        Args:
            host: Nazwa hosta lub adres IP zdalnego serwera
            user: Nazwa użytkownika (opcjonalnie)
            port: Port SSH (domyślnie 22)
            key_file: Ścieżka do pliku klucza prywatnego (opcjonalnie)
            password: Hasło (opcjonalnie, niezalecane - lepiej używać kluczy)
            use_sudo: Czy automatycznie używać sudo dla komend, które tego wymagają
            sudo_password: Hasło do sudo (opcjonalnie)
            use_agent: Czy używać agenta SSH do uwierzytelniania
            certificate_file: Ścieżka do pliku certyfikatu SSH
            identity_only: Czy używać tylko podanego klucza/certyfikatu (IdentitiesOnly=yes)
            gssapi_auth: Czy używać uwierzytelniania GSSAPI (Kerberos)
            gssapi_keyex: Czy używać wymiany kluczy GSSAPI
            gssapi_delegate_creds: Czy delegować poświadczenia GSSAPI
            ssh_options: Dodatkowe opcje SSH jako słownik
        """
        self.context.set_remote_execution(
            host=host,
            user=user,
            port=port,
            key_file=key_file,
            password=password,
            use_sudo=use_sudo,
            sudo_password=sudo_password,
            use_agent=use_agent,
            certificate_file=certificate_file,
            identity_only=identity_only,
            gssapi_auth=gssapi_auth,
            gssapi_keyex=gssapi_keyex,
            gssapi_delegate_creds=gssapi_delegate_creds,
            ssh_options=ssh_options
        )
        
        # Tworzymy backend SSH
        self.remote_backend = SshBackend(
            host=host,
            user=user,
            port=port,
            key_file=key_file,
            password=password,
            use_sudo=use_sudo,
            sudo_password=sudo_password,
            use_agent=use_agent,
            certificate_file=certificate_file,
            identity_only=identity_only,
            gssapi_auth=gssapi_auth,
            gssapi_keyex=gssapi_keyex,
            gssapi_delegate_creds=gssapi_delegate_creds,
            ssh_options=ssh_options
        )
    
    def set_local_execution(self) -> None:
        """Ustawia tryb wykonania lokalnego"""
        self.context.set_local_execution()
    
    def get_backend(self):
        """Zwraca odpowiedni backend na podstawie trybu wykonania"""
        if self.context.is_remote():
            if not self.remote_backend:
                # Jeśli nie mamy jeszcze backendu SSH, tworzymy go
                remote_host = self.context.remote_host
                self.remote_backend = SshBackend(
                    host=remote_host.host,
                    user=remote_host.user,
                    port=remote_host.port,
                    key_file=remote_host.key_file,
                    password=remote_host.password,
                    use_sudo=remote_host.use_sudo,
                    sudo_password=remote_host.sudo_password,
                    use_agent=remote_host.use_agent,
                    certificate_file=remote_host.certificate_file,
                    identity_only=remote_host.identity_only,
                    gssapi_auth=remote_host.gssapi_auth,
                    gssapi_keyex=remote_host.gssapi_keyex,
                    gssapi_delegate_creds=remote_host.gssapi_delegate_creds,
                    ssh_options=remote_host.ssh_options
                )
            return self.remote_backend
        else:
            return self.local_backend
    
    # Metody do zarządzania cache'em
    
    def enable_cache(self, max_size: int = 100, auto_refresh: bool = False, 
                    refresh_interval: int = 5) -> None:
        """
        Włącza cache dla wyników komend.
        
        Args:
            max_size: Maksymalna liczba przechowywanych wyników komend
            auto_refresh: Czy automatycznie odświeżać cache
            refresh_interval: Interwał odświeżania w sekundach
        """
        if not self._cache_enabled:
            self._cache_enabled = True
            self._command_cache = CommandCache(
                max_size=max_size,
                auto_refresh=auto_refresh,
                refresh_interval=refresh_interval
            )
        else:
            # Jeśli cache już istnieje, aktualizujemy jego parametry
            self._command_cache.set_auto_refresh(auto_refresh, refresh_interval)
    
    def disable_cache(self) -> None:
        """Wyłącza cache dla wyników komend"""
        if self._cache_enabled and self._command_cache:
            self._command_cache.stop_refresh()
            self._cache_enabled = False
            self._command_cache = None
    
    def clear_cache(self) -> None:
        """Czyści cache wyników komend"""
        if self._cache_enabled and self._command_cache:
            self._command_cache.clear()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Zwraca statystyki cache.
        
        Returns:
            Słownik ze statystykami lub pusty słownik, jeśli cache jest wyłączony
        """
        if self._cache_enabled and self._command_cache:
            return self._command_cache.get_statistics()
        return {}
    
    def get_command_history(self, limit: Optional[int] = None, 
                           success_only: bool = False) -> List[Any]:
        """
        Pobiera historię wykonanych komend.
        
        Args:
            limit: Maksymalna liczba zwracanych wpisów (od najnowszych)
            success_only: Czy zwracać tylko komendy zakończone sukcesem
            
        Returns:
            Lista krotek (command_id, timestamp, success) lub pusta lista, jeśli cache jest wyłączony
        """
        if self._cache_enabled and self._command_cache:
            return self._command_cache.get_history(limit, success_only)
        return []
    
    def get_cached_result(self, command_id: str) -> Optional[CommandResult]:
        """
        Pobiera wynik komendy z cache.
        
        Args:
            command_id: Identyfikator komendy
            
        Returns:
            Wynik komendy lub None, jeśli nie znaleziono lub cache wyłączony
        """
        if not self._cache_enabled or not self._command_cache:
            return None
            
        result = self._command_cache.get(command_id)
        
        # Pobierz również metadane z cache i dodaj je do wyniku
        if result:
            metadata_entry = self._command_cache.get_with_metadata(command_id)
            if metadata_entry and len(metadata_entry) > 2:
                _, _, meta_dict = metadata_entry
                if meta_dict and 'metadata' in meta_dict:
                    # Zaktualizuj metadane w wyniku, zachowując istniejące
                    if result.metadata is None:
                        result.metadata = meta_dict['metadata']
                    else:
                        result.metadata.update(meta_dict['metadata'])
                        
        return result
    
    def export_cache_data(self, include_results: bool = True) -> Dict[str, Any]:
        """
        Eksportuje dane cache do formatu JSON.
        
        Args:
            include_results: Czy dołączać pełne wyniki komend
            
        Returns:
            Słownik z danymi cache lub pusty słownik, jeśli cache jest wyłączony
        """
        if self._cache_enabled and self._command_cache:
            return self._command_cache.export_data(include_results)
        return {}

    def get_command_type_name(self, command_type: str, language: Optional[str] = None) -> str:
        """
        Zwraca nazwę typu komendy w określonym języku.
        
        Args:
            command_type: Typ komendy (np. 'ls', 'ps')
            language: Kod języka ('pl', 'en'), domyślnie używa języka ustawionego w instancji
            
        Returns:
            Nazwa typu komendy lub command_type jeśli brak tłumaczenia
        """
        lang = language or self.language
        if lang not in COMMAND_TYPES_TRANSLATION:
            return command_type
            
        translations = COMMAND_TYPES_TRANSLATION[lang]
        return translations.get(command_type, command_type)
    
    def set_language(self, language: str) -> None:
        """
        Ustawia język dla nazw komend.
        
        Args:
            language: Kod języka ('pl', 'en')
        """
        if language in COMMAND_TYPES_TRANSLATION:
            self.language = language
        else:
            raise ValueError(f"Nieobsługiwany język: {language}")
            
    def get_available_languages(self) -> List[str]:
        """
        Zwraca listę dostępnych języków.
        
        Returns:
            Lista kodów języków
        """
        return list(COMMAND_TYPES_TRANSLATION.keys())
