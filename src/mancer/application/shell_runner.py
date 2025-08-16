from typing import Dict, Any, Optional, List, Union
from ..domain.model.command_context import CommandContext, ExecutionMode, RemoteHostInfo
from ..domain.model.command_result import CommandResult
from ..domain.interface.command_interface import CommandInterface
from ..domain.service.command_chain_service import CommandChain
from ..infrastructure.factory.command_factory import CommandFactory
from ..infrastructure.backend.bash_backend import BashBackend
from ..infrastructure.backend.ssh_backend import SshBackend
from .command_cache import CommandCache
from ..infrastructure.logging.mancer_logger import MancerLogger
from ..domain.service.log_backend_interface import LogLevel
import uuid
import hashlib

# Command type definitions in different languages
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
    """High-level entry point for creating and executing commands.

    Provides context management, optional caching, live output support, logging,
    and helpers for local/remote execution.
    """

    def __init__(self, backend_type: str = "bash", 
                context: Optional[CommandContext] = None, 
                cache_size: int = 100,
                enable_cache: bool = True,
                enable_live_output: bool = False,
                enable_command_logging: bool = True,
                log_to_file: bool = False,
                log_level: str = "info"):
        """Initialize the command runner.

        Args:
            backend_type: Backend type ("bash" or "ssh").
            context: Optional execution context. If None, a default is created.
            cache_size: Command cache size.
            enable_cache: Whether to enable command caching.
            enable_live_output: Show command output in real-time by default.
            enable_command_logging: Whether to enable command logging.
            log_to_file: Whether to log to a file in addition to console.
            log_level: Logging level ("debug", "info", "warning", "error", "critical").
        """
        self.factory = CommandFactory(backend_type)
        self._context = context or self._create_default_context()
        self._command_cache = CommandCache(max_size=cache_size)
        self._cache_enabled = enable_cache
        self.enable_live_output = enable_live_output
        
        # Initialize command logging subsystem
        if enable_command_logging:
            logger = MancerLogger.get_instance()
            logger.initialize(
                log_level=log_level,
                file_enabled=log_to_file,
                console_enabled=True
            )
    
    def create_command(self, command_name: str) -> CommandInterface:
        """Creates a new command instance"""
        return self.factory.create_command(command_name)
    
    def execute(self, command: CommandInterface,
               context_params: Optional[Dict[str, Any]] = None,
               cache_id: Optional[str] = None,
               live_output: bool = False) -> CommandResult:
        """Execute a single command or a CommandChain with optional caching and live output.

        Args:
            command: Command instance or CommandChain to execute.
            context_params: Optional context parameters to set for this run (e.g. env, live output config).
            cache_id: Optional cache key; if omitted and caching enabled, a stable key is derived.
            live_output: If True, stream stdout/stderr in real time (no caching).

        Returns:
            CommandResult with raw_output, structured_output, status and history.

        Notes:
            - When live_output is enabled, results are not cached.
            - For simple commands, the __call__ wrapper is used to ensure logging.
        """
        # Copy context to avoid modifying the global one
        context = self._prepare_context(context_params)
        
        # Determine if we're using live output
        use_live_output = live_output or self.enable_live_output
        
        # For commands with 'refresh' in their name, always enable live output
        if "refresh" in str(command).lower():
            use_live_output = True
        
        # Generate a unique command identifier if not provided
        if self._cache_enabled and cache_id is None and not use_live_output:
            cache_id = self._generate_command_id(command, context)
            
            # Check if the result is in the cache
            cached_result = self._command_cache.get(cache_id)
            if cached_result:
                return cached_result
        
        # Set the live_output parameter in the context
        if use_live_output:
            context.set_parameter("live_output", True)
            context.set_parameter("live_output_interval", 0.1)  # Refresh every 0.1 seconds
        
        # Execute the command - use __call__ method which provides logging
        if isinstance(command, CommandChain):
            result = command.execute(context)
        else:
            # Use __call__ instead of direct execute to ensure logging
            result = command(context) if hasattr(command, '__call__') else command.execute(context)
            
        # Store the result in the cache if caching is enabled (but not for live output)
        if self._cache_enabled and result and not use_live_output:
            command_str = str(command)
            
            # Get the command type (class name or command name)
            command_type = command.__class__.__name__
            if hasattr(command, 'name'):
                command_type = command.name
                
            # Get the full command string
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
        """Registers a preconfigured command under an alias"""
        self.factory.register_command(alias, command)
    
    def get_command(self, alias: str) -> CommandInterface:
        """Gets a preconfigured command by alias"""
        return self.factory.get_command(alias)
    
    def _prepare_context(self, context_params: Optional[Dict[str, Any]] = None) -> CommandContext:
        """Prepares the command execution context"""
        # Copy the base context
        context = self._context.clone()
        
        # Add parameters if provided
        if context_params:
            for key, value in context_params.items():
                context.set_parameter(key, value)
        
        return context
    
    def _create_default_context(self) -> CommandContext:
        """Creates a default execution context"""
        import os
        return CommandContext(current_directory=os.getcwd())
    
    def _generate_command_id(self, command: CommandInterface, context: CommandContext) -> str:
        """Generates a unique identifier for a command in a specific context"""
        # Get command string
        cmd_str = command.build_command() if hasattr(command, "build_command") else str(command)
        
        # Create a string containing all the contextual information
        context_str = f"{context.current_directory}|{context.execution_mode}|"
        
        # Add remote host info if applicable
        if context.remote_host:
            context_str += f"{context.remote_host.hostname}|{context.remote_host.username}|{context.remote_host.port}"
        
        # Combine and hash
        combined = f"{cmd_str}|{context_str}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()
    
    def set_remote_execution(self, host: str, user: Optional[str] = None, 
                           port: int = 22, key_file: Optional[str] = None,
                           password: Optional[str] = None, use_sudo: bool = False,
                           sudo_password: Optional[str] = None, use_agent: bool = False,
                           certificate_file: Optional[str] = None, identity_only: bool = False,
                           gssapi_auth: bool = False, gssapi_keyex: bool = False,
                           gssapi_delegate_creds: bool = False,
                           ssh_options: Optional[Dict[str, str]] = None) -> None:
        """
        Configures the runner for remote command execution via SSH.
        
        Args:
            host: Remote host address
            user: SSH username
            port: SSH port
            key_file: SSH private key file
            password: SSH password (not recommended, use key authentication)
            use_sudo: Whether to use sudo for commands
            sudo_password: Password for sudo
            use_agent: Whether to use SSH agent
            certificate_file: SSH certificate file
            identity_only: Whether to only use the specified identity
            gssapi_auth: Whether to use GSSAPI authentication
            gssapi_keyex: Whether to use GSSAPI key exchange
            gssapi_delegate_creds: Whether to delegate GSSAPI credentials
            ssh_options: Additional SSH options
        """
        # Configure remote execution mode in context
        self._context.set_remote_execution(
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
            ssh_options=ssh_options or {}
        )

        # Log the change
        logger = MancerLogger.get_instance()
        logger.info(f"Remote execution set to {host}:{port}", {
            "user": user,
            "use_sudo": use_sudo,
            "use_agent": use_agent
        })
    
    def set_local_execution(self) -> None:
        """Sets the execution mode back to local"""
        self._context.set_local_execution()
        
        # Log the change
        logger = MancerLogger.get_instance()
        logger.info("Execution mode set to local")
    
    def get_backend(self):
        """Returns the current execution backend"""
        if self._context.execution_mode == ExecutionMode.REMOTE:
            # Create an SSH backend
            rh = self._context.remote_host
            return SshBackend(
                hostname=rh.host,
                username=rh.user,
                password=rh.password,
                port=rh.port,
                key_filename=rh.key_file,
                allow_agent=rh.use_agent,
                look_for_keys=True,
                gssapi_auth=rh.gssapi_auth,
                gssapi_kex=rh.gssapi_keyex,
                gssapi_delegate_creds=rh.gssapi_delegate_creds,
                ssh_options=rh.ssh_options
            )
        else:
            # Use local bash backend
            return BashBackend()
    
    def enable_cache(self, max_size: int = 100, auto_refresh: bool = False, 
                    refresh_interval: int = 5) -> None:
        """
        Enables command result caching.
        
        Args:
            max_size: Maximum number of cached results
            auto_refresh: Whether to automatically refresh cached results
            refresh_interval: Refresh interval in minutes
        """
        self._cache_enabled = True
        self._command_cache.set_max_size(max_size)
        
        if auto_refresh:
            self._command_cache.enable_auto_refresh(refresh_interval)
            
        # Log the change
        logger = MancerLogger.get_instance()
        logger.info(f"Command cache enabled (size: {max_size}, auto refresh: {auto_refresh})")
    
    def disable_cache(self) -> None:
        """Disables command result caching"""
        self._cache_enabled = False
        self._command_cache.disable_auto_refresh()
        
        # Log the change
        logger = MancerLogger.get_instance()
        logger.info("Command cache disabled")
    
    def clear_cache(self) -> None:
        """Clears all cached command results"""
        self._command_cache.clear()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Returns statistics about the command cache"""
        if self._cache_enabled:
            stats = self._command_cache.get_statistics()
            stats["enabled"] = True
            return stats
        else:
            return {
                "enabled": False,
                "total_commands": 0,
                "success_count": 0,
                "error_count": 0,
                "cache_size": 0,
                "max_size": 0,
                "auto_refresh": False,
                "refresh_interval": 0
            }
    
    def get_command_history(self, limit: Optional[int] = None, 
                           success_only: bool = False) -> List[Any]:
        """
        Gets the command execution history.
        
        Args:
            limit: Maximum number of history entries to return
            success_only: Whether to only return successful commands
            
        Returns:
            List of command history entries
        """
        # Get history from the logger
        logger = MancerLogger.get_instance()
        return logger.get_command_history(limit=limit, success_only=success_only)
    
    def get_cached_result(self, command_id: str) -> Optional[CommandResult]:
        """
        Gets a cached command result by ID.
        
        Args:
            command_id: The cache ID of the command
            
        Returns:
            The cached result or None if not found
        """
        if not self._cache_enabled:
            return None
            
        return self._command_cache.get(command_id)
    
    def export_cache_data(self, include_results: bool = True) -> Dict[str, Any]:
        """
        Exports the command cache data.
        
        Args:
            include_results: Whether to include full command results
            
        Returns:
            Dictionary with cache data
        """
        return self._command_cache.export_data(include_results=include_results)
    
    def execute_live(self, command: CommandInterface,
                   context_params: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Execute a command with live (streamed) output.

        Args:
            command: The command to execute.
            context_params: Additional context parameters for this run.

        Returns:
            CommandResult: Result of execution.

        Notes:
            Live output mode disables caching for this execution.
        """
        return self.execute(command, context_params, live_output=True)
    
    def create_bash_command(self, command_str: str) -> CommandInterface:
        """Create a raw bash command wrapper based on EchoCommand.

        Args:
            command_str: Bash command string to execute as-is.

        Returns:
            CommandInterface: A command object whose build_command() returns command_str.

        Examples:
            runner.create_bash_command("ls -la /tmp").execute(ctx)
        """
        from ..infrastructure.command.system.echo_command import EchoCommand

        echo = EchoCommand()
        echo.command_str = command_str

        def _build_command():
            return command_str
        echo.build_command = _build_command

        return echo
    
    def get_command_type_name(self, command_type: str, language: Optional[str] = None) -> str:
        """
        Gets a human-readable name for a command type in the specified language.
        
        Args:
            command_type: Command type (e.g., "ls", "grep")
            language: Language code ("en" or "pl")
            
        Returns:
            Human-readable command name
        """
        language = language or self._context.get_parameter("language", "en")
        
        if language in COMMAND_TYPES_TRANSLATION and command_type in COMMAND_TYPES_TRANSLATION[language]:
            return COMMAND_TYPES_TRANSLATION[language][command_type]
        
        return command_type
    
    def set_language(self, language: str) -> None:
        """
        Sets the UI language.
        
        Args:
            language: Language code ("en" or "pl")
        """
        if language not in self.get_available_languages():
            raise ValueError(f"Unsupported language: {language}")
            
        self._context.set_parameter("language", language)
    
    def get_available_languages(self) -> List[str]:
        """
        Returns a list of available UI languages.
        
        Returns:
            List of language codes
        """
        return list(COMMAND_TYPES_TRANSLATION.keys())

