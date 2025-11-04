from typing import Any, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ...command.base_command import BaseCommand


class HostnameCommand(BaseCommand):
    """Komenda hostname - wyświetla lub ustawia nazwę hosta"""

    def __init__(self, name: str = "hostname"):
        """Initialize hostname command.

        Args:
            name: Command name (default: "hostname").
        """
        super().__init__(name=name)

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę hostname"""
        # Pobieramy backend
        backend = self._get_backend(context)

        # Budujemy komendę
        command_str = self.build_command()

        # Wykonujemy komendę
        result = backend.execute_command(
            command_str,
            working_dir=context.current_directory,
            env_vars=context.environment_variables,
        )

        # Parsujemy wynik
        if result.is_success():
            result.structured_output = self._parse_output(result.raw_output)

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "HostnameCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: HostnameCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value) -> "HostnameCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: HostnameCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "HostnameCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: HostnameCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "HostnameCommand":
        """Return a new instance marked to require sudo."""
        new_instance: HostnameCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "HostnameCommand":
        """Return a new instance with an added positional argument."""
        new_instance: HostnameCommand = self.clone()  # type: ignore  # type: ignore
        new_instance._args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "HostnameCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: HostnameCommand = self.clone()  # type: ignore  # type: ignore
        new_instance.preferred_data_format = format_type
        return new_instance

    def _parse_output(self, raw_output: str) -> List[Any]:
        """Parsuje wyjście hostname - po prostu zwraca nazwę hosta"""
        return [raw_output.strip()]

    # Metody specyficzne dla hostname

    def set_hostname(self, name: str) -> "HostnameCommand":
        """Ustawia nazwę hosta (wymaga uprawnień roota)"""
        new_instance: HostnameCommand = self.clone()  # type: ignore
        new_instance.requires_sudo = True
        return new_instance.with_param("name", name)

    def domain(self) -> "HostnameCommand":
        """Opcja -d - pokazuje nazwę domeny"""
        return self.with_option("-d")

    def fqdn(self) -> "HostnameCommand":
        """Opcja -f - pokazuje pełną nazwę domeny (FQDN)"""
        return self.with_option("-f")

    def ip_address(self) -> "HostnameCommand":
        """Opcja -i - pokazuje adresy IP hosta"""
        return self.with_option("-i")
