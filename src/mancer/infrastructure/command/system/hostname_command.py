from typing import Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ...command.base_command import BaseCommand


class HostnameCommand(BaseCommand):
    """Komenda hostname - wyświetla lub ustawia nazwę hosta"""

    def __init__(self):
        super().__init__("hostname")

    def execute(
        self, context: CommandContext, input_result: Optional[CommandResult] = None
    ) -> CommandResult:
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

    def _parse_output(self, raw_output: str) -> str:
        """Parsuje wyjście hostname - po prostu zwraca nazwę hosta"""
        return raw_output.strip()

    # Metody specyficzne dla hostname

    def set_hostname(self, name: str) -> "HostnameCommand":
        """Ustawia nazwę hosta (wymaga uprawnień roota)"""
        new_instance = self.clone()
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
