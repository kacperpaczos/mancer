from __future__ import annotations

import pathlib
from abc import abstractmethod
from copy import deepcopy
from typing import Any, Dict, List, Optional, TypeVar, Union, cast

import polars as pl
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypeAlias

from ...domain.interface.backend_interface import BackendInterface
from ...domain.interface.command_interface import CommandInterface
from ...domain.model.command_context import CommandContext, ExecutionMode
from ...domain.model.command_result import CommandResult
from ...domain.model.data_format import DataFormat
from ...domain.service.command_chain_service import CommandChain
from ..backend.bash_backend import BashBackend
from .loggable_command_mixin import LoggableCommandMixin

T = TypeVar("T", bound="BaseCommand")

# Type for command parameter values
ParamValue: TypeAlias = Union[str, int, float, bool, pathlib.Path, List[str], None]


class BaseCommand(BaseModel, CommandInterface, LoggableCommandMixin):
    """Base implementation of a command.

    Provides common building, execution and result preparation logic.
    Subclasses should override execute() and _parse_output().
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        ignored_types=(str, int, float, bool),  # Ignore simple class attributes
        populate_by_name=True,  # Allow both field names and aliases
    )  # Allow backend and other non-serializable types

    name: str
    options: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    flags: List[str] = Field(default_factory=list)
    backend: Any = Field(default_factory=BashBackend, exclude=True)  # Backend instance (not serializable)
    pipeline: Optional[str] = None  # Optional pipeline (e.g., | grep)
    requires_sudo: bool = False  # Whether the command requires sudo
    preferred_data_format: DataFormat = DataFormat.POLARS  # Preferred data format

    args: List[str] = Field(default_factory=list, exclude=True)  # Additional arguments (private, not serialized)

    def with_option(self, option: str) -> "BaseCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: BaseCommand = self.clone()
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value: ParamValue) -> "BaseCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: BaseCommand = self.clone()
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "BaseCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: BaseCommand = self.clone()
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "BaseCommand":
        """Return a new instance marked to require sudo."""
        new_instance: BaseCommand = self.clone()
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self: T, arg: str) -> T:
        """Return a new instance with an added positional argument."""
        new_instance = self.clone()
        new_instance.args.append(arg)
        return new_instance

    def add_args(self: T, args: List[str]) -> T:
        """Return a new instance with extended positional arguments."""
        new_instance = self.clone()
        new_instance.args.extend(args)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "BaseCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: BaseCommand = self.clone()
        new_instance.preferred_data_format = format_type
        return new_instance

    def clone(self: T) -> T:
        """Create a copy of the command instance (immutable builder pattern)."""
        # Use model_copy for Pydantic models
        base_copy: "BaseCommand" = self.model_copy(deep=True)
        new_instance = cast(T, base_copy)
        # Ensure backend and private attributes are properly copied
        new_instance.backend = self.backend
        new_instance.args = deepcopy(self.args)
        # model_copy preserves the type when self: T is used
        return new_instance

    def build_command(self) -> str:
        """Build the command string for execution."""
        cmd_parts = []

        # Add sudo if required
        if self.requires_sudo:
            cmd_parts.append("sudo")

        # Command name
        cmd_parts.append(self.name)

        # Options
        cmd_parts.extend(self.options)

        # Parameters
        for name, value in self.parameters.items():
            cmd_parts.append(self._format_parameter(name, value))

        # Flags
        cmd_parts.extend([f"--{flag}" for flag in self.flags])

        # Additional positional arguments
        cmd_parts.extend(self.args)

        # Pipeline if present
        if self.pipeline:
            cmd_parts.append(self.pipeline)

        return " ".join(cmd_parts)

    def _get_backend(self, context: CommandContext) -> BackendInterface:
        """Select an execution backend based on context (SSH for remote, otherwise default)."""
        if context.execution_mode == ExecutionMode.REMOTE and context.remote_host is not None:
            remote_host = context.remote_host
            from ..backend.ssh_backend import SshBackendFactory

            return cast(
                BackendInterface,
                SshBackendFactory.create_backend(
                    hostname=remote_host.host,
                    username=remote_host.user,
                    password=remote_host.password,
                    port=remote_host.port,
                    key_filename=remote_host.key_file,
                    allow_agent=remote_host.use_agent,
                    look_for_keys=True,
                    compress=False,
                    timeout=None,
                    gssapi_auth=remote_host.gssapi_auth,
                    gssapi_kex=remote_host.gssapi_keyex,
                    gssapi_delegate_creds=remote_host.gssapi_delegate_creds,
                    ssh_options=remote_host.ssh_options,
                ),
            )
        return cast(BackendInterface, self.backend)

    @abstractmethod
    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Execute the command (to be implemented by subclasses).

        Do not call directly; the __call__ wrapper ensures logging.
        """
        pass

    def __call__(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Execute the command with logging (main entry point).

        Args:
            context: Command execution context.
            input_result: Optional previous command result (for pipelines).

        Returns:
            CommandResult: Result of execution.
        """
        return self.execute_with_logging(self.execute, context, input_result)

    def _format_parameter(self, name: str, value: ParamValue) -> str:
        """Format a single command parameter.
        Override in subclasses for special formatting.
        """
        return f"--{name}={value}"

    def _get_additional_args(self) -> List[str]:
        """
        Zwraca dodatkowe argumenty specyficzne dla podklasy.
        Do nadpisania w podklasach.
        """
        return self.args

    def _parse_output(self, raw_output: str) -> Union[pl.DataFrame, Any]:
        """Parse raw command output to a structured representation.
        Override in subclasses.
        """
        return pl.DataFrame([{"raw_line": raw_output}])

    def _prepare_result(
        self,
        raw_output: str,
        success: bool,
        exit_code: int = 0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        """Prepare command result, add history and handle preferred data format."""
        # Parse output
        structured_output = self._parse_output(raw_output)

        # Utwórz obiekt wyniku
        result = CommandResult(
            raw_output=raw_output,
            success=success,
            structured_output=structured_output,
            exit_code=exit_code,
            error_message=error_message,
            metadata=metadata,
            data_format=self.preferred_data_format,
        )

        # Dodaj krok do historii
        structured_sample = None
        if isinstance(structured_output, pl.DataFrame):
            if len(structured_output) > 0:
                structured_sample = structured_output.head(5).to_dicts()
        else:
            structured_sample = structured_output[:5] if structured_output else None

        result.add_to_history(
            command_string=self.build_command(),
            command_type=self.__class__.__name__,
            structured_sample=structured_sample,
        )

        # Jeśli format danych jest inny niż POLARS, dokonaj konwersji
        if self.preferred_data_format != DataFormat.POLARS:
            return result.to_format(self.preferred_data_format)

        return result

    def then(self, next_command: CommandInterface) -> "CommandChain":
        """Create a sequential command chain with the next command."""
        chain = CommandChain(self)
        return chain.then(next_command)

    def pipe(self, next_command: CommandInterface) -> "CommandChain":
        """Create a pipeline chain, piping this command's output to the next."""
        chain = CommandChain(self)
        return chain.pipe(next_command)
