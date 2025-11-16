from typing import Any, Dict, List, Optional

from ....domain.model.command_context import CommandContext
from ....domain.model.command_result import CommandResult
from ....domain.model.data_format import DataFormat
from ..base_command import BaseCommand


class SystemctlCommand(BaseCommand):
    """Komenda systemctl - zarządza usługami systemowymi"""

    def __init__(self, name: str = "systemctl"):
        """Initialize systemctl command.

        Args:
            name: Command name (default: "systemctl").
        """
        super().__init__(name=name)

    def execute(self, context: CommandContext, input_result: Optional[CommandResult] = None) -> CommandResult:
        """Wykonuje komendę systemctl"""
        # Budujemy komendę
        cmd_str = self.build_command()

        # Pobieramy odpowiedni backend
        backend = self._get_backend(context)

        # Wykonujemy komendę
        result = backend.execute_command(cmd_str, working_dir=context.current_directory)

        # Parsujemy wynik dla określonych podkomend
        if result.success and "operation" in self.parameters:
            operation = self.parameters.get("operation")
            if operation == "status" or operation == "list-units":
                result.structured_output = self._parse_units_output(result.raw_output)

        return result

    def _get_additional_args(self) -> List[str]:
        """Dodaje argumenty specyficzne dla systemctl"""
        args = super()._get_additional_args().copy()

        # Dodaj operację
        if "operation" in self.parameters:
            args.append(self.parameters["operation"])

        # Dodaj nazwę usługi, jeśli istnieje
        if "service" in self.parameters:
            args.append(self.parameters["service"])

        return args

    def _format_parameter(self, name: str, value: Any) -> str:
        """Specjalne formatowanie dla systemctl"""
        if name == "operation" or name == "service":
            return ""  # Te parametry są obsługiwane przez _get_additional_args
        return super()._format_parameter(name, value)

    def _parse_units_output(self, raw_output: str) -> List[Dict[str, str]]:
        """Parsuje wynik statusu usług systemowych"""
        result = []
        lines = raw_output.strip().split("\n")

        # Pomijamy pierwszą linię, jeśli to nagłówek
        start_idx = 0
        if len(lines) > 0 and lines[0].strip().startswith("UNIT"):
            start_idx = 1

        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue

            # Podziel linię na kolumny
            parts = line.split(None, 4)  # Maksymalnie 5 kolumn

            if len(parts) >= 5:
                unit_info = {
                    "unit": parts[0],
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3],
                    "description": parts[4],
                }
                result.append(unit_info)
            elif len(parts) >= 1:
                # Jakiś inny format, zachowujemy co możemy
                result.append({"unit": parts[0]})

        return result

    # Przepisane metody buildera dla poprawnego typu zwracanego

    def with_option(self, option: str) -> "SystemctlCommand":
        """Return a new instance with an added short/long option (e.g., -l)."""
        new_instance: SystemctlCommand = self.clone()
        new_instance.options.append(option)
        return new_instance

    def with_param(self, name: str, value: Any) -> "SystemctlCommand":
        """Return a new instance with a named parameter (e.g., --name=value)."""
        new_instance: SystemctlCommand = self.clone()
        new_instance.parameters[name] = value
        return new_instance

    def with_flag(self, flag: str) -> "SystemctlCommand":
        """Return a new instance with a boolean flag (e.g., --recursive)."""
        new_instance: SystemctlCommand = self.clone()
        new_instance.flags.append(flag)
        return new_instance

    def with_sudo(self) -> "SystemctlCommand":
        """Return a new instance marked to require sudo."""
        new_instance: SystemctlCommand = self.clone()
        new_instance.requires_sudo = True
        return new_instance

    def add_arg(self, arg: str) -> "SystemctlCommand":
        """Return a new instance with an added positional argument."""
        new_instance: SystemctlCommand = self.clone()
        new_instance.args.append(arg)
        return new_instance

    def with_data_format(self, format_type: DataFormat) -> "SystemctlCommand":
        """Return a new instance with a preferred output data format."""
        new_instance: SystemctlCommand = self.clone()
        new_instance.preferred_data_format = format_type
        return new_instance

    # Metody specyficzne dla systemctl

    def start(self, service: str) -> "SystemctlCommand":
        """Uruchamia usługę"""
        return self.with_param("operation", "start").with_param("service", service)

    def stop(self, service: str) -> "SystemctlCommand":
        """Zatrzymuje usługę"""
        return self.with_param("operation", "stop").with_param("service", service)

    def restart(self, service: str) -> "SystemctlCommand":
        """Restartuje usługę"""
        return self.with_param("operation", "restart").with_param("service", service)

    def status(self, service: Optional[str] = None) -> "SystemctlCommand":
        """Sprawdza status usługi lub wszystkich usług"""
        cmd: SystemctlCommand = self.with_param("operation", "status")
        if service:
            cmd = cmd.with_param("service", service)
        return cmd

    def enable(self, service: str) -> "SystemctlCommand":
        """Włącza usługę przy starcie systemu"""
        return self.with_param("operation", "enable").with_param("service", service)

    def disable(self, service: str) -> "SystemctlCommand":
        """Wyłącza usługę przy starcie systemu"""
        return self.with_param("operation", "disable").with_param("service", service)

    def list_units(self) -> "SystemctlCommand":
        """Wyświetla listę jednostek systemowych"""
        return self.with_param("operation", "list-units")

    def with_type(self, unit_type: str) -> "SystemctlCommand":
        """Filtruje jednostki według typu (service, socket, etc.)"""
        return self.with_param("type", unit_type)
