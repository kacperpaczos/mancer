from abc import abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Type
from copy import deepcopy
from ...domain.interface.command_interface import CommandInterface
from ...domain.model.command_result import CommandResult
from ...domain.model.command_context import CommandContext, ExecutionMode
from ...domain.model.data_format import DataFormat
from ..backend.bash_backend import BashBackend
from ..backend.ssh_backend import SshBackend
from .versioned_command_mixin import VersionedCommandMixin

T = TypeVar('T', bound='BaseCommand')

class BaseCommand(CommandInterface, VersionedCommandMixin):
    """Base command implementation"""
    
    def __init__(self, name: str):
        self.name = name
        self.options: List[str] = []
        self.parameters: Dict[str, Any] = {}
        self.flags: List[str] = []
        self.backend = BashBackend()  # Default backend
        self.pipeline = None  # Optional pipeline (e.g., | grep)
        self.requires_sudo = False  # Whether the command requires sudo
        self._args: List[str] = []  # List of additional arguments
        self.preferred_data_format: DataFormat = DataFormat.LIST  # Preferred data format
        self.tool_name = name  # By default, tool name is the same as command name
        self.detected_version = None  # Will store the detected version after checking
    
    def with_option(self, option: str) -> T:
        """Adds an option to the command"""
        new_instance = self.clone()
        new_instance.options.append(option)
        return new_instance
    
    def with_param(self, name: str, value: Any) -> T:
        """Sets a command parameter"""
        new_instance = self.clone()
        new_instance.parameters[name] = value
        return new_instance
    
    def with_flag(self, flag: str) -> T:
        """Adds a flag to the command"""
        new_instance = self.clone()
        new_instance.flags.append(flag)
        return new_instance
    
    def with_sudo(self) -> T:
        """Marks that the command requires sudo"""
        new_instance = self.clone()
        new_instance.requires_sudo = True
        return new_instance
    
    def add_arg(self, arg: str) -> T:
        """Adds an argument to the command"""
        new_instance = self.clone()
        new_instance._args.append(arg)
        return new_instance
    
    def add_args(self, args: List[str]) -> T:
        """Adds a list of arguments to the command"""
        new_instance = self.clone()
        new_instance._args.extend(args)
        return new_instance
    
    def with_data_format(self, format_type: DataFormat) -> T:
        """Sets the preferred output data format for the command"""
        new_instance = self.clone()
        new_instance.preferred_data_format = format_type
        return new_instance
    
    def clone(self) -> T:
        """Creates a copy of the command instance"""
        new_instance = type(self)()  # Call zero-argument constructor
        new_instance.name = self.name  # Copy command name
        new_instance.options = deepcopy(self.options)
        new_instance.parameters = deepcopy(self.parameters)
        new_instance.flags = deepcopy(self.flags)
        new_instance.backend = self.backend
        new_instance.pipeline = self.pipeline
        new_instance.requires_sudo = self.requires_sudo
        new_instance._args = deepcopy(self._args)
        new_instance.preferred_data_format = self.preferred_data_format
        new_instance.tool_name = self.tool_name  # Copy tool name
        return new_instance
    
    def build_command(self) -> str:
        """Builds the command string"""
        cmd_parts = []
        
        # Add sudo if required
        if self.requires_sudo:
            cmd_parts.append("sudo")
            
        # Add command name
        cmd_parts.append(self.name)
        
        # Add options
        cmd_parts.extend(self.options)
        
        # Add parameters
        for name, value in self.parameters.items():
            cmd_parts.append(self._format_parameter(name, value))
            
        # Add flags
        cmd_parts.extend([f"--{flag}" for flag in self.flags])
        
        # Add additional arguments
        cmd_parts.extend(self._get_additional_args())
        
        # Add pipeline if it exists
        if self.pipeline:
            cmd_parts.append(self.pipeline)
            
        return " ".join(cmd_parts)
    
    def _get_backend(self, context: CommandContext):
        """
        Selects the appropriate backend based on the context.
        """
        # If context indicates remote mode, use SSH
        if (context.execution_mode == ExecutionMode.REMOTE 
            and context.remote_host is not None):
            
            remote_host = context.remote_host
            
            return SshBackend(
                hostname=remote_host.hostname,
                username=remote_host.username,
                password=remote_host.password,
                port=remote_host.port,
                key_filename=remote_host.key_filename,
                passphrase=remote_host.passphrase,
                allow_agent=remote_host.allow_agent,
                look_for_keys=remote_host.look_for_keys,
                compress=remote_host.compress, 
                timeout=remote_host.timeout,
                gssapi_auth=remote_host.gssapi_auth,
                gssapi_kex=remote_host.gssapi_kex,
                gssapi_delegate_creds=remote_host.gssapi_delegate_creds,
                ssh_options=remote_host.ssh_options
            )
        else:
            # Otherwise use the default backend
            return self.backend
    
    @abstractmethod
    def execute(self, context: CommandContext, 
               input_result: Optional[CommandResult] = None) -> CommandResult:
        """Command execution implementation - to be implemented in subclasses"""
        # Check tool version before executing the command
        self.detected_version = self.check_tool_version(context)
        
        # Subclasses should call this base method before executing the command
        pass
    
    def _format_parameter(self, name: str, value: Any) -> str:
        """
        Formats a single command parameter.
        Can be overridden in subclasses for special formatting.
        """
        return f"--{name}={value}"
    
    def _get_additional_args(self) -> List[str]:
        """
        Returns additional arguments specific to the subclass.
        To be overridden in subclasses.
        """
        return self._args
    
    def _parse_output(self, raw_output: str) -> List[Any]:
        """
        Parses raw command output into a structure.
        To be overridden in subclasses.
        """
        return [raw_output]
    
    def _prepare_result(self, raw_output: str, success: bool, exit_code: int = 0, 
                       error_message: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> CommandResult:
        """
        Prepares the command result with the preferred data format and history.
        """
        # Parse output using version-specific method if available
        if hasattr(self, 'version_adapters') and self.version_adapters and self.detected_version:
            structured_output = self.adapt_to_version(
                self.detected_version,
                '_parse_output',
                raw_output
            )
            # If version-specific parsing failed, fall back to default
            if structured_output is None:
                structured_output = self._parse_output(raw_output)
        else:
            # Use default parsing method
            structured_output = self._parse_output(raw_output)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
            
        # Add version information to metadata
        if self.detected_version:
            metadata["tool_version"] = {
                "name": self.detected_version.name,
                "version": self.detected_version.version
            }
        
        # Create result object
        result = CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata,
            data_format=self.preferred_data_format
        )
        
        # Add step to history
        result.add_to_history(
            command_string=self.build_command(),
            command_type=self.__class__.__name__,
            structured_sample=structured_output[:5] if structured_output else None
        )
        
        # If data format is different from LIST, perform conversion
        if self.preferred_data_format != DataFormat.LIST:
            return result.to_format(self.preferred_data_format)
            
        return result
    
    def then(self, next_command: CommandInterface) -> 'CommandChain':
        """Creates a command chain"""
        from ...domain.service.command_chain_service import CommandChain
        chain = CommandChain(self)
        return chain.then(next_command)
    
    def pipe(self, next_command: CommandInterface) -> 'CommandChain':
        """Creates a command chain with output redirection"""
        from ...domain.service.command_chain_service import CommandChain
        chain = CommandChain(self)
        return chain.pipe(next_command)
